import re
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select

from app.db.models import Candidate, JobPost
from app.db.schemas.job_post import JobPostCreate, JobPostEdit
from app.db.session import session_scope
from app.utils.ids import parse_id

JOB_FIELDS = (
    "role", "minimumSalary", "maximumSalary", "payingCurrency",
    "description", "jobType", "isAcceptingApplications", "genderRestriction",
)


async def create_job(job: JobPostCreate, company_id: str):
    data = job.model_dump(mode="json")
    with session_scope() as db:
        post = JobPost(company_id=parse_id(company_id), **{k: data[k] for k in JOB_FIELDS if data[k] is not None})
        db.add(post)
        db.flush()
        return {"id": str(post.id)}


async def edit_job(job: JobPostEdit, company_id: str):
    changes = job.model_dump(mode="json", exclude_none=True, exclude={"id"})
    with session_scope() as db:
        post = db.get(JobPost, parse_id(job.id))
        if not post:
            raise HTTPException(status_code=404, detail="Job not found")
        if str(post.company_id) != company_id:
            raise HTTPException(status_code=403, detail="You can only edit your own jobs")
        for key, value in changes.items():
            setattr(post, key, value)
        post.updatedAt = datetime.now()
    return {"message": "Job updated successfully"}


def list_jobs():
    with session_scope() as db:
        return {"jobs": [j.to_dict(with_company=True) for j in db.scalars(select(JobPost).order_by(JobPost.id.desc()))]}


def eligibility_for(post: JobPost, candidate: Candidate | None) -> str:
    """"ok", "gender_missing" (candidate must complete their profile) or "not_eligible"."""
    restriction = post.genderRestriction or "any"
    if restriction == "any" or candidate is None:
        return "ok"
    if not candidate.gender:
        return "gender_missing"
    return "ok" if candidate.gender == restriction else "not_eligible"


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9+#.]+", (text or "").lower()))


def recommended_list_jobs(candidate_id: str):
    """Jobs ranked by overlap between the candidate skills and the job text."""
    with session_scope() as db:
        candidate = db.get(Candidate, parse_id(candidate_id))
        skills = [s for s in ((candidate.skills if candidate else None) or []) if s]

        jobs = []
        for post in db.scalars(select(JobPost).where(JobPost.isAcceptingApplications.is_(True))):
            job_tokens = _tokens(f"{post.role} {post.description}")
            matched = [s for s in skills if _tokens(s) <= job_tokens]
            job = post.to_dict(with_company=True)
            job["matchedSkills"] = matched
            job["eligibility"] = eligibility_for(post, candidate)
            job["matchScore"] = round(100 * len(matched) / len(skills), 2) if skills else 0
            jobs.append(job)

    jobs.sort(key=lambda j: j["matchScore"], reverse=True)
    return {"jobs": jobs}


def list_jobs_by_company(company_id: str):
    with session_scope() as db:
        posts = db.scalars(select(JobPost).where(JobPost.company_id == parse_id(company_id)).order_by(JobPost.id.desc()))
        return {"jobs": [p.to_dict() for p in posts]}


def get_job_by_id(id: str, viewer: dict | None = None):
    with session_scope() as db:
        post = db.get(JobPost, parse_id(id))
        if not post:
            raise HTTPException(status_code=404, detail="Job not found")
        job = post.to_dict(with_company=True)
        if viewer and viewer.get("role") == "candidate":
            job["eligibility"] = eligibility_for(post, db.get(Candidate, parse_id(viewer["id"])))
        return job
