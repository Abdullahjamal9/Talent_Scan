from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, require_candidate, require_company
from app.db.schemas.job_post import JobPostCreate, JobPostEdit
from app.services.job_post import (
    create_job, edit_job, get_job_by_id, list_jobs, list_jobs_by_company, recommended_list_jobs,
)

router = APIRouter()


@router.post("/create")
async def create(job: JobPostCreate, user: dict = Depends(require_company)):
    result = await create_job(job, user["id"])
    return {"message": "Job created successfully", "data": result}


@router.get("/list")
def list_all():
    return list_jobs()


@router.get("/recommended_list")
def recommended_list(user: dict = Depends(require_candidate)):
    return recommended_list_jobs(user["id"])


@router.post("/edit")
async def edit(job: JobPostEdit, user: dict = Depends(require_company)):
    return await edit_job(job, user["id"])


@router.get("/list-by-company-id/{companyId}")
def list_by_company(companyId: str):
    return list_jobs_by_company(companyId)


@router.get("/{id}")
def get_by_id(id: str, user: dict = Depends(get_current_user)):
    return get_job_by_id(id, user)
