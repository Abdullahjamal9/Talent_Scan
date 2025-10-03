# app/api/v1/routers.py
from fastapi import APIRouter
from app.api.v1.endpoints import candidate
from app.api.v1.endpoints import company
from app.api.v1.endpoints import job_post
from app.api.v1.endpoints import job_application

api_router = APIRouter()

# Include routes
api_router.include_router(candidate.router, prefix="/candidate", tags=["Candidate"])
api_router.include_router(company.router, prefix="/company", tags=["Company"])
api_router.include_router(job_post.router, prefix="/job-post", tags=["Job Post"])
api_router.include_router(job_application.router, prefix="/job-application", tags=["Job Application"])