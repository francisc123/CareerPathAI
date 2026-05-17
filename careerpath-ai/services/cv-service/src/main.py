import os
import uuid
import magic
import boto3
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from contextlib import asynccontextmanager

from shared.types.kafka_events import CvUploadedEvent

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
# Am adăugat 'text' la importurile sqlalchemy
from sqlalchemy import Column, String, DateTime, Text, func, select, text

from cp_kafka import KafkaProducerBase

from extraction import extract_text_from_bytes
from .retry import startup_retry

# Configuratii
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://careerpath_user:change_me_strong_password@postgres:5432/careerpath").replace("postgresql://", "postgresql+asyncpg://")
MINIO_URL = os.getenv("MINIO_URL", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
REDPANDA_BROKER = os.getenv("KAFKA_BROKERS", "redpanda:9092")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Baza de date (PostgreSQL)
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class CVUpload(Base):
    __tablename__ = "cv_uploads"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    file_path = Column(String)
    status = Column(String)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# MinIO (boto3 - Sincron)
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

# FastAPI & Redpanda Lifecycle
producer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Setup Redpanda/Kafka Producer folosind pachetul shared
    global producer
    producer = KafkaProducerBase(bootstrap_servers=REDPANDA_BROKER)
    await producer.start()

    yield

    await producer.stop()

app = FastAPI(lifespan=lifespan, title="CV Service")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "cv-service"}

# Endpoints
@app.post("/upload")
async def upload_cv(
        file: UploadFile = File(...),
        x_user_id: str = Header(..., description="ID-ul utilizatorului injectat de API Gateway"),
        db: AsyncSession = Depends(get_db)
):
    # 1. Citire și Validare dimensiune
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    # 2. Validare tip fișier cu python-magic
    mime_type = magic.from_buffer(file_bytes, mime=True)
    allowed_mimes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg"
    ]
    if mime_type not in allowed_mimes:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime_type}. Only PDF, DOCX, and JPG are allowed.")

    # Generare ID-uri
    job_id = str(uuid.uuid4())
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
    file_path = f"{x_user_id}/{job_id}.{ext}"

    # 3. Extragere Text
    extracted_text = await asyncio.to_thread(extract_text_from_bytes, file_bytes, mime_type)

    # 4. Upload în MinIO
    try:
        await asyncio.to_thread(
            s3_client.put_object,
            Bucket="cvs-raw",
            Key=file_path,
            Body=file_bytes,
            ContentType=mime_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {str(e)}")

    # 5. Salvare în PostgreSQL
    new_cv = CVUpload(
        id=job_id,
        user_id=x_user_id,
        file_path=file_path,
        status="uploaded",
        extracted_text=extracted_text
    )
    db.add(new_cv)
    await db.commit()

    # 6. Publish eveniment către Redpanda folosind structura curată și nativă
    try:
        event = CvUploadedEvent(
            user_id=x_user_id,
            job_id=job_id,
            minio_path=file_path,
            file_name=file.filename,
            timestamp=datetime.utcnow()
        )

        await producer.send_message("cv.uploaded", event)

    except Exception as kafka_error:
        raise HTTPException(
            status_code=500,
            detail=f"Kafka Event Generation failed: {str(kafka_error)}"
        )

    return {"job_id": job_id, "status": "processing"}

# Endpoint modificat pentru a returna scorul
@app.get("/status/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CVUpload).where(CVUpload.id == job_id))
    job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")

    score = 0

    if job.status == "completed":
        try:
            score_result = await db.execute(
                text("SELECT score FROM cv_analysis_results WHERE user_id = :uid ORDER BY analyzed_at DESC LIMIT 1"),
                {"uid": job.user_id}
            )
            score_row = score_result.fetchone()
            if score_row and score_row[0] is not None:
                score = score_row[0]
        except Exception as e:
            print(f"Eroare la citirea scorului din baza de date: {e}")
            # Also fall back to cv_uploads.score which the analyzer writes directly.
            if job.status == "completed" and hasattr(job, "score") and getattr(job, "score", None):
                score = job.score

    return {
        "job_id": job.id,
        "status": job.status,
        "score": score
    }