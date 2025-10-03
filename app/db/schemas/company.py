from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from typing import Optional

class CompanySignInRequest(BaseModel):
    email: EmailStr
    password: str

class CompanySocials(BaseModel):
    linkedin: Optional[HttpUrl] = None
    facebook: Optional[HttpUrl] = None
    github: Optional[HttpUrl] = None

    @field_validator("linkedin", "facebook", "github", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        return None if v == "" else v

class CompanyBase(BaseModel):
    name: Optional[str] = ''
    email: EmailStr
    password: str = Field(..., min_length=7)
    address: Optional[str] = ''
    about: Optional[str] = ''
    phone: Optional[str] = ''
    profilePicture: Optional[str] = ''
    totalEmployees: Optional[int] = 0

class CompanyCreate(CompanyBase):
    socials: Optional[CompanySocials] = {}

class CompanyEditRequest(BaseModel):
    name: Optional[str] = ''
    address: Optional[str] = ''
    about: Optional[str] = ''
    phone: Optional[str] = ''
    profilePicture: Optional[str] = ''
    totalEmployees: Optional[int] = 0
    socials: Optional[CompanySocials] = {}

class CompanyInDB(CompanyCreate):
    id: str = Field(..., alias="_id")

class CompanyOut(CompanyInDB):
    pass
