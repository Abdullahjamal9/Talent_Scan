from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.deps import require_candidate, require_company
from app.db.models import Candidate, JobApplication, JobPost
from app.db.schemas.job_application import ApplicationNotesUpdate, ApplicationStatusUpdate, JobApplyRequest
from app.db.session import session_scope
from app.utils.ids import parse_id
from app.utils.parsing import analyze_candidate_for_job

router = APIRouter()

NOT_WITHDRAWABLE = ("offer", "hired", "rejected")  # already decided: nothing left to withdraw


def _application_dict(a: JobApplication, recruiter_view: bool = False, **related) -> dict:
    """Recruiter notes and interview questions are internal and never sent to candidates."""
    analysis = dict(a.aiAnalysis) if a.aiAnalysis else None
    if analysis and not recruiter_view:
        analysis.pop("questions", None)

    data = {
        "_id": str(a.id),
        "candidate": str(a.candidate_id),
        "company": str(a.company_id),
        "job": str(a.job_id),
        "AIScore": a.AIScore,
        "analysis": analysis,
        "status": a.status,
        "createdAt": a.createdAt,
        "updatedAt": a.updatedAt,
        **related,
    }
    if recruiter_view:
        data["notes"] = a.notes
    return data


def _check_eligibility(post: JobPost, candidate: Candidate) -> None:
    restriction = post.genderRestriction or "any"
    if restriction == "any":
        return
    if not candidate.gender:
        raise HTTPException(
            status_code=403,
            detail=f"This role is open to {restriction} candidates only. Please set your gender in your profile to apply.",
        )
    if candidate.gender != restriction:
        raise HTTPException(status_code=403, detail=f"This role is open to {restriction} candidates only.")


@router.post("/apply")
async def apply(body: JobApplyRequest, user: dict = Depends(require_candidate)):
    job_id = parse_id(body.job)

    # Load what scoring needs, then release the connection while the (slow) AI call runs
    with session_scope() as db:
        post = db.get(JobPost, job_id)
        if not post:
            raise HTTPException(status_code=404, detail="Job not found")
        if not post.isAcceptingApplications:
            raise HTTPException(status_code=400, detail="This job is not accepting applications")
        candidate = db.get(Candidate, parse_id(user["id"]))
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        _check_eligibility(post, candidate)

        if db.scalar(select(JobApplication.id).where(
            JobApplication.candidate_id == candidate.id, JobApplication.job_id == job_id
        )):
            raise HTTPException(status_code=409, detail="You have already applied to this job")
        job_data, candidate_data, company_id = post.to_dict(), candidate.to_public(), post.company_id

    analysis = await run_in_threadpool(analyze_candidate_for_job, candidate_data, job_data)

    with session_scope() as db:
        application = JobApplication(
            candidate_id=int(user["id"]), job_id=job_id, company_id=company_id,
            AIScore=analysis["score"] if analysis else None, aiAnalysis=analysis, status="applied",
        )
        db.add(application)
        try:
            db.flush()
        except IntegrityError:
            raise HTTPException(status_code=409, detail="You have already applied to this job")
        result = {
            "message": "Job application created successfully",
            "data": str(application.id),
            "AIScore": application.AIScore,
            "analysis": _application_dict(application)["analysis"],
        }
    return result


@router.get("/get-by-candidate/{id}")
async def get_by_candidate(id: str, user: dict = Depends(require_candidate)):
    if id != user["id"]:
        raise HTTPException(status_code=403, detail="You can only view your own applications")

    with session_scope() as db:
        rows = db.scalars(
            select(JobApplication).where(JobApplication.candidate_id == parse_id(id)).order_by(JobApplication.id.desc())
        )
        return {
            "data": [_application_dict(a, job=a.job.to_dict(), company=a.company.to_public()) for a in rows]
        }


@router.post("/withdraw/{application_id}")
async def withdraw(application_id: str, user: dict = Depends(require_candidate)):
    with session_scope() as db:
        application = db.get(JobApplication, parse_id(application_id))
        if not application or str(application.candidate_id) != user["id"]:
            raise HTTPException(status_code=404, detail="Application not found")
        if application.status in NOT_WITHDRAWABLE:
            raise HTTPException(status_code=400, detail="This application has already been decided and cannot be withdrawn here. Please contact the company.")
        db.delete(application)
    return {"message": "Application withdrawn"}


@router.get("/get-by-company-and-job/{jobId}")
async def get_by_company_and_job(jobId: str, user: dict = Depends(require_company)):
    with session_scope() as db:
        post = db.get(JobPost, parse_id(jobId))
        if not post:
            raise HTTPException(status_code=404, detail="Job not found")
        if str(post.company_id) != user["id"]:
            raise HTTPException(status_code=403, detail="You can only view applications for your own jobs")

        rows = db.scalars(select(JobApplication).where(JobApplication.job_id == post.id))
        applications = [_application_dict(a, recruiter_view=True, candidate=a.candidate.to_public()) for a in rows]

    applications.sort(key=lambda a: a["AIScore"] or 0, reverse=True)
    return {"data": applications}


@router.get("/get-by-company")
async def get_by_company(user: dict = Depends(require_company)):
    """Every application across all of the company jobs (for the candidates table)."""
    with session_scope() as db:
        rows = db.scalars(
            select(JobApplication).where(JobApplication.company_id == parse_id(user["id"])).order_by(JobApplication.id.desc())
        )
        return {
            "data": [
                _application_dict(a, recruiter_view=True, candidate=a.candidate.to_public(), job=a.job.to_dict())
                for a in rows
            ]
        }


@router.post("/rescore/{application_id}")
async def rescore(application_id: str, user: dict = Depends(require_company)):
    """Runs the AI analysis again, e.g. after the first attempt failed or the profile or job changed."""
    with session_scope() as db:
        application = db.get(JobApplication, parse_id(application_id))
        if not application or str(application.company_id) != user["id"]:
            raise HTTPException(status_code=404, detail="Application not found")
        candidate_data, job_data = application.candidate.to_public(), application.job.to_dict()

    analysis = await run_in_threadpool(analyze_candidate_for_job, candidate_data, job_data)
    if not analysis:
        raise HTTPException(status_code=502, detail="The AI service is unavailable right now. Please try again shortly.")

    with session_scope() as db:
        application = db.get(JobApplication, parse_id(application_id))
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        application.AIScore = analysis["score"]
        application.aiAnalysis = analysis
        return _application_dict(application, recruiter_view=True)


@router.post("/notes/{application_id}")
async def update_notes(application_id: str, body: ApplicationNotesUpdate, user: dict = Depends(require_company)):
    with session_scope() as db:
        application = db.get(JobApplication, parse_id(application_id))
        if not application or str(application.company_id) != user["id"]:
            raise HTTPException(status_code=404, detail="Application not found")
        application.notes = body.notes
    return {"message": "Notes saved"}


@router.post("/status/{application_id}")
async def update_status(application_id: str, body: ApplicationStatusUpdate, user: dict = Depends(require_company)):
    with session_scope() as db:
        application = db.get(JobApplication, parse_id(application_id))
        if not application or str(application.company_id) != user["id"]:
            raise HTTPException(status_code=404, detail="Application not found")
        application.status = body.status.value
    return {"message": "Status updated", "status": body.status.value}
