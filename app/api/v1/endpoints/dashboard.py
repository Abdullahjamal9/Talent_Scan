from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.deps import require_candidate, require_company
from app.db.models import Candidate, JobApplication, JobPost
from app.db.schemas.job_application import PIPELINE_STAGES
from app.db.session import session_scope
from app.services.job_post import recommended_list_jobs
from app.utils.ids import parse_id

router = APIRouter()

TREND_DAYS = 14
SCORE_BUCKETS = [("0-39", 0, 40), ("40-59", 40, 60), ("60-79", 60, 80), ("80-100", 80, 101)]


def _avg(values: list) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


def _funnel(statuses: list) -> list:
    counts = Counter(statuses)
    return [{"stage": stage, "count": counts.get(stage, 0)} for stage in PIPELINE_STAGES]


@router.get("/company")
async def company_dashboard(user: dict = Depends(require_company)):
    company_id = parse_id(user["id"])
    now = datetime.now()

    with session_scope() as db:
        jobs = list(db.scalars(select(JobPost).where(JobPost.company_id == company_id)))
        apps = list(
            db.scalars(
                select(JobApplication).where(JobApplication.company_id == company_id).order_by(JobApplication.id.desc())
            )
        )

        scores = [a.AIScore for a in apps if a.AIScore is not None]
        per_job = {j.id: [a for a in apps if a.job_id == j.id] for j in jobs}

        trend_start = (now - timedelta(days=TREND_DAYS - 1)).date()
        by_day = Counter(a.createdAt.date() for a in apps if a.createdAt.date() >= trend_start)

        def row(a: JobApplication) -> dict:
            return {
                "applicationId": str(a.id),
                "candidateId": str(a.candidate_id),
                "name": a.candidate.fullName or a.candidate.email,
                "email": a.candidate.email,
                "job": a.job.role,
                "jobId": str(a.job_id),
                "score": a.AIScore,
                "status": a.status,
                "createdAt": a.createdAt,
            }

        return {
            "kpis": {
                "openJobs": sum(1 for j in jobs if j.isAcceptingApplications),
                "totalJobs": len(jobs),
                "totalApplicants": len(apps),
                "newThisWeek": sum(1 for a in apps if a.createdAt >= now - timedelta(days=7)),
                "avgScore": _avg(scores),
                "inInterview": sum(1 for a in apps if a.status in ("interview", "offer")),
                "hired": sum(1 for a in apps if a.status == "hired"),
            },
            "funnel": _funnel([a.status for a in apps]),
            "trend": [
                {"date": (trend_start + timedelta(days=i)).isoformat(), "count": by_day.get(trend_start + timedelta(days=i), 0)}
                for i in range(TREND_DAYS)
            ],
            "scoreBuckets": [
                {"label": label, "count": sum(1 for s in scores if lo <= s < hi)} for label, lo, hi in SCORE_BUCKETS
            ],
            "topCandidates": [row(a) for a in sorted(apps, key=lambda a: a.AIScore or 0, reverse=True)[:5] if a.AIScore is not None],
            "recent": [row(a) for a in apps[:8]],
            "jobs": [
                {
                    "id": str(j.id),
                    "role": j.role,
                    "jobType": j.jobType,
                    "genderRestriction": j.genderRestriction or "any",
                    "createdAt": j.createdAt,
                    "isAcceptingApplications": j.isAcceptingApplications,
                    "applicants": len(per_job[j.id]),
                    "avgScore": _avg([a.AIScore for a in per_job[j.id] if a.AIScore is not None]),
                }
                for j in jobs
            ],
        }


PROFILE_CHECKS = [
    ("fullName", "Full name"),
    ("phone", "Phone number"),
    ("address", "Location"),
    ("about", "About you"),
    ("skills", "Skills"),
    ("experience", "Experience"),
    ("qualification", "Education"),
    ("resume", "Resume"),
]


@router.get("/candidate")
async def candidate_dashboard(user: dict = Depends(require_candidate)):
    candidate_id = parse_id(user["id"])

    with session_scope() as db:
        candidate = db.get(Candidate, candidate_id)
        apps = list(
            db.scalars(
                select(JobApplication).where(JobApplication.candidate_id == candidate_id).order_by(JobApplication.id.desc())
            )
        )
        missing = [label for field, label in PROFILE_CHECKS if not getattr(candidate, field)]
        scores = [a.AIScore for a in apps if a.AIScore is not None]

        data = {
            "kpis": {
                "applications": len(apps),
                "active": sum(1 for a in apps if a.status not in ("rejected", "hired")),
                "interviews": sum(1 for a in apps if a.status == "interview"),
                "offers": sum(1 for a in apps if a.status in ("offer", "hired")),
                "avgScore": _avg(scores),
            },
            "funnel": _funnel([a.status for a in apps]),
            "profile": {
                "percent": round(100 * (len(PROFILE_CHECKS) - len(missing)) / len(PROFILE_CHECKS)),
                "missing": missing,
            },
            "recent": [
                {
                    "applicationId": str(a.id),
                    "jobId": str(a.job_id),
                    "role": a.job.role,
                    "company": a.company.name,
                    "status": a.status,
                    "score": a.AIScore,
                    "createdAt": a.createdAt,
                    "updatedAt": a.updatedAt,
                }
                for a in apps[:6]
            ],
        }

    data["recommended"] = [
        j for j in recommended_list_jobs(user["id"])["jobs"] if j["matchScore"] > 0
    ][:4]
    return data
