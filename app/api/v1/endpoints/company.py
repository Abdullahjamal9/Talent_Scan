from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request, status
from app.db.schemas.company import CompanyCreate, CompanySignInRequest, CompanyEditRequest
from app.services.company import create_company, sign_in_company, get_company_by_id, company_update, get_all_companies
from enum import Enum
from app.utils.upload_file import upload_file
import time
import os

router = APIRouter()

class Company_Routes(str, Enum):
    SIGN_IN = '/sign-in'
    SIGN_UP = '/sign-up'
    GET_COMPANY_BY_ID = '/{id}'
    COMPANY_ME = '/me'
    COMPANY_PROFILE_EDIT = '/edit'
    COMPANY_LIST = '/list'


@router.post(Company_Routes.SIGN_IN.value)
async def sign_in(company: CompanySignInRequest):
    try:
        result = await sign_in_company(company)
        return {"message": "Company signed in successfully", "data": result}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))

@router.post(Company_Routes.SIGN_UP.value)
async def sign_up(company: CompanyCreate):
    try:
        result = await create_company(company)
        return {"message": "Company created successfully", "company": result}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get(Company_Routes.COMPANY_ME.value)
async def company_me(request: Request):
    try:
        company = await get_company_by_id(request.state.user["id"])
        return {"message": "success", "company": company}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.post(Company_Routes.COMPANY_PROFILE_EDIT.value)
async def company_edit_profile(request: Request, company: CompanyEditRequest):
    try:
        result = await company_update(request.state.user["id"], company.dict())
        return {"message": "success", "company": result}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    
@router.get(Company_Routes.COMPANY_LIST.value)
async def company_list():
    try:
        companies = await get_all_companies()
        return {"message": "success", "companies": companies}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))
    
@router.get(Company_Routes.GET_COMPANY_BY_ID.value)
async def company_me(id: str):
    try:
        company = await get_company_by_id(id)
        return {"message": "success", "company": company}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))