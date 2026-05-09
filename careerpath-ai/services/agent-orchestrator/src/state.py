from typing import TypedDict, List, Optional
from pydantic import BaseModel

# Pydantic model for the incoming Kafka event
class CvAnalyzedEvent(BaseModel):
    user_id: str
    score: int
    gaps: List[str]
    target_role: str

# LangGraph state
class WorkflowState(TypedDict):
    user_id: str
    cv_score: int
    gaps: List[str]
    target_role: str
    retry_count: int # Adăugat pentru mecanismul de reîncercare
    current_node: Optional[str] = None
    error: Optional[str] = None

