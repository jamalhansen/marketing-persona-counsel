from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField


class PersonaEvaluation(BaseModel):
    """Evaluation result from a single persona."""

    persona_name: str
    sentiment: str = Field(description="One-word or short-phrase sentiment (e.g. 'Skeptical but Interested', 'Ecstatic', 'Bored')")
    interest_score: int = Field(ge=1, le=10, description="Overall interest in the topic")
    engagement_score: int = Field(ge=1, le=10, description="How likely they are to read the whole thing")
    friendliness_score: int = Field(ge=1, le=10, description="Tone friendliness and accessibility")
    shareability_score: int = Field(ge=1, le=10, description="Likelihood to share with their network")
    
    outstanding_questions: list[str] = Field(description="Questions left unanswered for this persona")
    tips_to_improve: list[str] = Field(description="Specific actionable advice to improve the post for this persona")
    narrative: str = Field(description="2-3 sentence overall take from this persona's perspective")


class CouncilResult(BaseModel):
    """The aggregated result from all personas."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    source_title: str
    source_location: str  # URL or file path
    
    evaluations: list[PersonaEvaluation]
    
    @property
    def average_interest(self) -> float:
        return sum(e.interest_score for e in self.evaluations) / len(self.evaluations)

    @property
    def average_engagement(self) -> float:
        return sum(e.engagement_score for e in self.evaluations) / len(self.evaluations)


class EvaluationRecord(SQLModel, table=True):
    """Database record for persistence in SQLite."""
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    timestamp: datetime = SQLField(default_factory=datetime.now)
    source_title: str
    source_location: str
    
    persona_name: str
    sentiment: str
    interest_score: int
    engagement_score: int
    friendliness_score: int
    shareability_score: int
    
    # Store lists as joined strings or JSON (SQLModel/SQLite simplicity)
    outstanding_questions: str 
    tips_to_improve: str
    narrative: str
