from pydantic import BaseModel, Field

class JobApplicationBase(BaseModel):
    candidate: str  # candidateId
    company: str  # companyId
    job: str  # jobPostId

class JobApplicationCreate(JobApplicationBase):
    AIScore: int

class JobApplicationInDB(JobApplicationCreate):
    id: str = Field(..., alias="_id")

class JobApplicationOut(JobApplicationInDB):
    pass
