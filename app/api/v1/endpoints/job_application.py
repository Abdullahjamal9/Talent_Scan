from fastapi import APIRouter, HTTPException, Request
from app.db.schemas.job_application import JobApplicationBase
from app.db.session import get_job_Application_collection, get_job_post_collection, get_company_collection, get_candidates_collection
from enum import Enum
from bson import ObjectId
import random

router = APIRouter()

class Job_Application_Routes(str, Enum):
    APPLY = '/apply'
    GET_BY_COMPANY_AND_JOB = '/get-by-company-and-job/{jobId}'
    GET_BY_CANDIDATE = '/get-by-candidate/{id}'
    GET_BY_JOB = '/get-by-job'

@router.post(Job_Application_Routes.APPLY.value)
async def create(job_application: JobApplicationBase):
    try:
        collection = get_job_Application_collection()
        job_application = job_application.dict()
        
        job_application["AIScore"] = round(random.uniform(50, 90), 2)
        
        result = collection.insert_one(job_application)
        return {"message": "Job application created successfully", "data": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get(Job_Application_Routes.GET_BY_CANDIDATE.value)
async def get_by_candidate(id: str):
    try:
        collection = get_job_Application_collection()

        job_applications = list(collection.find({"candidate": id}))

        for application in job_applications:
            application["_id"] = str(application["_id"])
        
        return {"data": job_applications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(Job_Application_Routes.GET_BY_COMPANY_AND_JOB.value)
async def get_by_company_and_job(request: Request, jobId: str):
    try:
        collection = get_job_Application_collection()
        job_post_collection = get_job_post_collection()
        company_collection = get_company_collection()
        candidate_collection = get_candidates_collection()  # Get candidates collection

        job_applications = list(collection.find({"company": request.state.user["id"], "job": jobId}))

        populated_applications = []

        for application in job_applications:
            application["_id"] = str(application["_id"])
            application["candidate"] = str(application["candidate"])
            application["company"] = str(application["company"])
            application["job"] = str(application["job"])

            # Fetch candidate details
            candidate = candidate_collection.find_one({"_id": ObjectId(application["candidate"])}, {"password": 0})
            if candidate:
                candidate["_id"] = str(candidate["_id"])
                application["candidate"] = candidate  # Replace ID with object

            # Fetch company details
            company = company_collection.find_one({"_id": ObjectId(application["company"])})
            if company:
                company["_id"] = str(company["_id"])
                application["company"] = company  # Replace ID with object

            # Fetch job details
            job = job_post_collection.find_one({"_id": ObjectId(application["job"])})
            if job:
                job["_id"] = str(job["_id"])
                application["job"] = job  # Replace ID with object

            populated_applications.append(application)

        return {"data": populated_applications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
