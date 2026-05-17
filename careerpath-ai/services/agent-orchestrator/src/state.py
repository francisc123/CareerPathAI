from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field

# Pydantic model for the incoming Kafka event
class CvAnalyzedEvent(BaseModel):
    user_id: str
    score: int
    gaps: List[str] = Field(default_factory=list)
    target_role: str
    seniority: str = "mid"
    skills_extracted: List[str] = Field(default_factory=list)

    class Config:
        extra = "ignore"  # cv-analyzer publishes extra fields we don't need here

# LangGraph state
class WorkflowState(TypedDict, total=False):
    user_id: str
    cv_score: int
    gaps: List[str]
    target_role: str
    seniority: str
    skills: List[str]
    retry_count: int # Adăugat pentru mecanismul de reîncercare
    current_node: Optional[str]
    error: Optional[str]

