from fastapi import APIRouter, HTTPException, Request
from app.db.schemas.job_post import JobPostCreate, JobPostInDB
from app.services.job_post import create_job, edit_job, get_job_by_id, list_jobs_by_company, list_jobs, recommended_list_jobs
from enum import Enum

router = APIRouter()

class Job_Post_Routes(str, Enum):
    CREATE = '/create'
    LIST = '/list'
    RECOMMENDED_LIST = '/recommended_list'
    GET_BY_ID = '/{id}'
    EDIT = '/edit'
    LIST_BY_COMPANY_ID = '/list-by-company-id/{companyId}'

@router.post(Job_Post_Routes.CREATE.value)
async def create(job: JobPostCreate):
    try:
        result = await create_job(job)
        return {"message": "Job created successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(Job_Post_Routes.LIST.value)
def list():
    try:
        return list_jobs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(Job_Post_Routes.RECOMMENDED_LIST.value)
def Recommended_list(request: Request):
    try:
        print(request.state.user["id"])
        return recommended_list_jobs(request.state.user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(Job_Post_Routes.GET_BY_ID.value)
def get_by_id(id: str):
    try:
        return get_job_by_id(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post(Job_Post_Routes.EDIT.value)
async def edit(job: JobPostInDB):
    try:
        return await edit_job(job.id, job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(Job_Post_Routes.LIST_BY_COMPANY_ID.value)
def list_by_company(companyId: str):
    try:
        return list_jobs_by_company(companyId)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
