#!/usr/bin/env python3
"""
Test end-to-end pentru CV Analyzer Agent.
Trimite un CV pe topic Redpanda și validează că agentul îl procesează.
"""

import asyncio
import json
import os
import time
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

# Allow overriding brokers via env for running inside Docker network.
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:19092")  # External by default
TOPIC_CV_UPLOADED = "cv.uploaded"
TOPIC_CV_ANALYZED = "cv.analyzed"

# Sample CV text for testing
SAMPLE_CV = """
JOHN DOE
john.doe@example.com | +1-234-567-8900

PROFESSIONAL SUMMARY
Experienced Full Stack Developer with 3 years of expertise in React, Node.js, and PostgreSQL.
Strong background in building scalable web applications and microservices architecture.

SKILLS
- Frontend: React, TypeScript, Tailwind CSS, Redux
- Backend: Node.js, Express, FastAPI, REST APIs
- Databases: PostgreSQL, MongoDB, Redis
- DevOps: Docker, Kubernetes, AWS, CI/CD

EXPERIENCE
Senior Frontend Developer | TechCorp (2022-Present)
- Led React team of 5 developers
- Improved performance by 40% through code optimization
- Implemented advanced state management with Redux

Junior Developer | StartupXYZ (2021-2022)
- Developed full-stack features in React and Node.js
- Improved API response time by 35%

EDUCATION
B.S. in Computer Science | State University (2021)

CERTIFICATIONS
- AWS Certified Solutions Architect
- Kubernetes Administrator (CKA)
"""


async def send_cv_test():
    """Trimite CV pe topic cv.uploaded"""
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    
    await producer.start()
    print("📤 Producer conectat... (", KAFKA_BROKERS, ")")

    message = {
        "user_id": "test-user-001",
        "cv_text": SAMPLE_CV,
        "timestamp": time.time(),
    }
    
    print(f"\n📨 Trimit CV pentru user: {message['user_id']}")
    print(f"   CV length: {len(SAMPLE_CV)} characters\n")
    
    await producer.send_and_wait(TOPIC_CV_UPLOADED, message)
    print("✓ CV trimis pe topic cv.uploaded\n")
    
    await producer.stop()
    return message["user_id"]


async def listen_for_response(user_id: str, timeout_seconds: int = 60):
    """Asculta răspunsurile de pe topic cv.analyzed"""
    consumer = AIOKafkaConsumer(
        TOPIC_CV_ANALYZED,
        bootstrap_servers=KAFKA_BROKERS,
        auto_offset_reset="latest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        consumer_timeout_ms=timeout_seconds * 1000,
    )
    
    await consumer.start()
    print("👂 Consumer asculta pe topic cv.analyzed... (", KAFKA_BROKERS, ")")

    try:
        start_time = time.time()
        async for message in consumer:
            data = message.value
            
            if data.get("user_id") == user_id:
                elapsed = time.time() - start_time
                print(f"\n✅ RĂSPUNS PRIMIT (după {elapsed:.1f}s):")
                print(f"   Score: {data.get('score')}/100")
                print(f"   Seniority: {data.get('seniority')}")
                print(f"   Target Role: {data.get('target_role')}")
                print(f"   Skills: {', '.join(data.get('skills_extracted', [])[:5])}")
                print(f"   Status: {data.get('status')}\n")
                
                if data.get("priority_gaps"):
                    print("   Priority Gaps:")
                    for gap in data.get("priority_gaps", [])[:3]:
                        # gap may be dict or object
                        skill = gap.get('skill') if isinstance(gap, dict) else getattr(gap, 'skill', None)
                        reason = gap.get('reason') if isinstance(gap, dict) else getattr(gap, 'reason', None)
                        print(f"     - {skill}: {reason}")

                return data
    except asyncio.TimeoutError:
        print(f"⏱️  Timeout după {timeout_seconds}s - nu s-a primit răspuns\n")
        return None
    finally:
        await consumer.stop()


async def main():
    print("=" * 60)
    print("🧪 TEST END-TO-END: CV Analyzer Agent")
    print("=" * 60 + "\n")
    
    print("1️⃣  Verificare conexiune Redpanda...")
    try:
        from aiokafka.admin import AIOKafkaAdminClient
        admin = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BROKERS)
        await admin.start()
        clusters = await admin.describe_cluster()
        print(f"   ✓ Conectat la Redpanda (controller: {clusters.controller})\n")
        await admin.close()
    except Exception as e:
        print(f"   ✗ Eroare conexiune: {e}")
        print("   💡 Asigură-te că Redpanda rulează și KAFKA_BROKERS este corect setat\n")
        return
    
    # Send CV
    user_id = await send_cv_test()
    
    # Listen for response
    print("2️⃣  Aștept răspunsul de la CV Analyzer Agent...")
    result = await listen_for_response(user_id)
    
    if result:
        print("3️⃣  REZULTAT:")
        print("   ✅ SUCCES! Agentul a procesat CV-ul cu succes!")
        if result.get("score") >= 70:
            print("   ✓ CV-ul are scor bun (≥70) → Se va declanșa job scraping")
        else:
            print("   ⚠️  CV-ul are scor mic (<70) → Se va declanșa learning path")
    else:
        print("3️⃣  EROARE:")
        print("   ✗ Nu s-a primit răspuns de la agent în timp util")
        print("   💡 Verifică logurile agentului: docker logs cp-cv-analyzer")


if __name__ == "__main__":
    asyncio.run(main())
