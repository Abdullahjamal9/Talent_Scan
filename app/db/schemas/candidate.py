from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Literal, List, Optional
from datetime import date, datetime

class Qualification(BaseModel):
    institute: Optional[str] = ""
    program: Optional[str] = ""
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    description: Optional[str] = ""

    # Optional: Override the dict method to remove None values before serialization
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        return {key: value for key, value in result.items() if value is not None}

class Experience(BaseModel):
    company_or_organization: Optional[str] = ""
    role: Optional[str] = ""
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    description: Optional[str] = ""

    # Optional: Override the dict method to remove None values before serialization
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        return {key: value for key, value in result.items() if value is not None}
class Socials(BaseModel):
    linkedin: Optional[HttpUrl] = None
    facebook: Optional[HttpUrl] = None
    github: Optional[EmailStr] = None

class CandidateSignInRequest(BaseModel):
    email: EmailStr  # Ensures the email is a valid email format
    password: str 

class CandidateBase(BaseModel):
    fullName: Optional[str] = ''
    resume: Optional[str] = ''
    bio: Optional[str] = ''
    about: Optional[str] = ''
    address: Optional[str] = ''
    age: Optional[str] = ''
    gender: Literal["male", "female", ""] = ""
    phone: Optional[str] = ''
    email: EmailStr
    password: str  = Field(..., min_length=7)
    skills: Optional[List[str]] = []
    resume: Optional[str] = ''

class CandidateCreate(CandidateBase):
    qualification: Optional[List[Qualification]] = []
    experience: Optional[List[Experience]] = []
    socials: Optional[Socials] = {}

class CandidateInDB(CandidateCreate):
    id: str = Field(..., alias="_id")

class CandidateOut(CandidateInDB):
    pass
