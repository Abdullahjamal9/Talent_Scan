from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _now() -> datetime:
    return datetime.now()


# Responses keep the "_id" (string) field names so API clients do not care which database is behind them.


class Candidate(Base):
    __tablename__ = "candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    fullName: Mapped[str] = mapped_column(String(255), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    about: Mapped[str] = mapped_column(Text, default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    age: Mapped[str] = mapped_column(String(20), default="")
    gender: Mapped[str] = mapped_column(String(10), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    resume: Mapped[str] = mapped_column(String(500), default="")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    qualification: Mapped[list] = mapped_column(JSON, default=list)
    experience: Mapped[list] = mapped_column(JSON, default=list)
    socials: Mapped[dict] = mapped_column(JSON, default=dict)

    def to_public(self) -> dict:
        """Candidate as returned by the API (never includes the password)."""
        return {
            "_id": str(self.id),
            "email": self.email,
            "fullName": self.fullName,
            "bio": self.bio,
            "about": self.about,
            "address": self.address,
            "age": self.age,
            "gender": self.gender,
            "phone": self.phone,
            "resume": self.resume,
            "skills": self.skills or [],
            "qualification": self.qualification or [],
            "experience": self.experience or [],
            "socials": self.socials or {},
        }


class Company(Base):
    __tablename__ = "company"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), default="")
    about: Mapped[str] = mapped_column(Text, default="")
    address: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    profilePicture: Mapped[str] = mapped_column(String(500), default="")
    totalEmployees: Mapped[int] = mapped_column(Integer, default=0)
    socials: Mapped[dict] = mapped_column(JSON, default=dict)

    def to_public(self) -> dict:
        return {
            "_id": str(self.id),
            "email": self.email,
            "name": self.name,
            "about": self.about,
            "address": self.address,
            "phone": self.phone,
            "profilePicture": self.profilePicture,
            "totalEmployees": self.totalEmployees,
            "socials": self.socials or {},
        }


class JobPost(Base):
    __tablename__ = "job_post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(255), default="")
    minimumSalary: Mapped[str] = mapped_column(String(50), default="")
    maximumSalary: Mapped[str] = mapped_column(String(50), default="")
    payingCurrency: Mapped[str] = mapped_column(String(20), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    jobType: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    isAcceptingApplications: Mapped[bool] = mapped_column(Boolean, default=True)
    # "any", "female" or "male": set by the recruiter, enforced when a candidate applies
    genderRestriction: Mapped[str] = mapped_column(String(10), default="any", server_default="any")
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=_now)

    company: Mapped[Company] = relationship()

    def to_dict(self, with_company: bool = False) -> dict:
        return {
            "_id": str(self.id),
            "company": self.company.to_public() if with_company else str(self.company_id),
            "role": self.role,
            "minimumSalary": self.minimumSalary,
            "maximumSalary": self.maximumSalary,
            "payingCurrency": self.payingCurrency,
            "description": self.description,
            "jobType": self.jobType,
            "isAcceptingApplications": self.isAcceptingApplications,
            "genderRestriction": self.genderRestriction or "any",
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
        }


class JobApplication(Base):
    __tablename__ = "job_application"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_application_candidate_job"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_post.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"), index=True)
    AIScore: Mapped[Optional[float]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="applied")
    notes: Mapped[str] = mapped_column(Text, default="")
    # LLM output: {summary, strengths, gaps, questions, model, generatedAt}
    aiAnalysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    candidate: Mapped[Candidate] = relationship()
    job: Mapped[JobPost] = relationship()
    company: Mapped[Company] = relationship()
