from app.db.base import get_collection

def get_candidates_collection():
    return get_collection("candidate")

def get_company_collection():
    return get_collection("company")

def get_job_post_collection():
    return get_collection("jobPost")

def get_job_Application_collection():
    return get_collection("jobApplication")
