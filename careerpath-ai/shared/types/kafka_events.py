"""Shared Kafka event Pydantic models — used by all Python services."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserRegisteredEvent(BaseModel):
    user_id: str
    email: str
    timestamp: datetime


class CvUploadedEvent(BaseModel):
    user_id: str
    job_id: str
    minio_path: str
    file_name: str
    timestamp: datetime


class CvAnalyzedEvent(BaseModel):
    user_id: str
    job_id: str
    score: int                  # 0-100
    skills: list[str]
    gaps: list[str]
    target_role: str
    seniority_level: str
    timestamp: datetime


class GapsIdentifiedEvent(BaseModel):
    user_id: str
    gaps: list[str]
    current_level: str
    target_role: str
    timestamp: datetime


class JobsScrapedEvent(BaseModel):
    user_id: str
    scrape_run_id: str
    job_count: int
    timestamp: datetime


class JobsMatchedEvent(BaseModel):
    user_id: str
    top_job_ids: list[str]
    timestamp: datetime


class LearningPathCreatedEvent(BaseModel):
    user_id: str
    path_id: str
    total_weeks: int
    timestamp: datetime


class LearningCompletedEvent(BaseModel):
    user_id: str
    path_id: str
    timestamp: datetime


class InterviewCompletedEvent(BaseModel):
    user_id: str
    session_id: str
    type: str               # hr | technical
    score: float
    timestamp: datetime
