from fastapi import APIRouter, Depends
from app.core.deps import require_company
from app.db.schemas.company import CompanyCreate, CompanyEditRequest, CompanySignInRequest
from app.services.company import (
    company_update, create_company, get_all_companies, get_company_by_id, sign_in_company,
)

router = APIRouter()


@router.post("/sign-in")
async def sign_in(company: CompanySignInRequest):
    result = await sign_in_company(company)
    return {"message": "Company signed in successfully", "data": result}


@router.post("/sign-up")
async def sign_up(company: CompanyCreate):
    result = await create_company(company)
    return {"message": "Company created successfully", "company": result}


# Fixed paths must be declared before the id route
@router.get("/me")
async def company_me(user: dict = Depends(require_company)):
    return {"message": "success", "company": await get_company_by_id(user["id"])}


@router.post("/edit")
async def company_edit_profile(company: CompanyEditRequest, user: dict = Depends(require_company)):
    result = await company_update(user["id"], company.model_dump())
    return {"message": "success", "company": result}


@router.get("/list")
async def company_list():
    return {"message": "success", "companies": await get_all_companies()}


@router.get("/{id}")
async def company_get_by_id(id: str):
    return {"message": "success", "company": await get_company_by_id(id)}
