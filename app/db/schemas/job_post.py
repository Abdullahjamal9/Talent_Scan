from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from enum import Enum
from datetime import datetime

class JobType(str, Enum):
    FULL_TIME = "full time"
    PART_TIME = "part time"
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"
    LONG_TERM = "long term"
    CONTRACT = "contract"

class JobPostBase(BaseModel):
    company: str
    role: Optional[str] = ''
    minimumSalary: Optional[str] = ''
    maximumSalary: Optional[str] = ''
    payingCurrency: Optional[str] = ''
    description: Optional[str] = ''
    jobType: Optional[JobType] = None
    isAcceptingApplications: Optional[bool] = True
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class JobPostCreate(JobPostBase):
    pass

class JobPostInDB(JobPostCreate):
    id: str = Field(..., alias="_id")
    company: Optional[str] = None

class JobPostOut(JobPostInDB):
    pass
