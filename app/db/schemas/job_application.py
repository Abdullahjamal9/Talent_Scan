from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ApplicationStatus(str, Enum):
    """Hiring pipeline stages, in order."""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"


PIPELINE_STAGES = [s.value for s in ApplicationStatus]


class JobApplyRequest(BaseModel):
    job: str  # jobPostId


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationNotesUpdate(BaseModel):
    notes: str = Field("", max_length=5000)
