import json
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.deps import require_candidate
from app.db.schemas.candidate import CandidateSignInRequest, Experience, Qualification, Socials
from app.services.candidate import (
    create_candidate, get_all_candidates, get_candidate_by_id, sign_in_candidate, update_candidate,
)
from app.utils.jwt import create_jwt_token
from app.utils.parsing import parse_resume
from app.utils.upload_file import upload_file

router = APIRouter()

_email = TypeAdapter(EmailStr)


def _parse_date(value: Optional[str]) -> Optional[str]:
    """Converts MM/YYYY from the resume parser to an ISO string (stored in a JSON column)."""
    try:
        return datetime.strptime(value, "%m/%Y").isoformat() if value else None
    except ValueError:
        return None


def _with_dates(item: dict, start: Optional[str], end: Optional[str]) -> dict:
    item["startDate"] = _parse_date(start)
    item["endDate"] = _parse_date(end)
    return {k: v for k, v in item.items() if v is not None}


def _json_form(value: str, field: str):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Field {field} must be valid JSON")


@router.post("/sign-in")
async def sign_in(candidate: CandidateSignInRequest):
    result = await sign_in_candidate(candidate)
    return {"message": "Candidate signed in successfully", "data": result}


@router.post("/sign-up")
async def sign_up(
    fullName: str = Form(...),
    email: str = Form(...),
    password: str = Form(..., min_length=7),
    gender: Literal["male", "female", ""] = Form(""),  # self-declared, needed for gender-specific roles
    resume: UploadFile = File(...),
):
    try:
        email = str(_email.validate_python(email))
    except ValidationError:
        raise HTTPException(status_code=422, detail="Invalid email address")

    resume_path = await upload_file(resume)

    # Resume parsing is best-effort: the account is still created if the parser fails.
    data = await run_in_threadpool(parse_resume, resume_path) or {}

    candidate = await create_candidate({
        "fullName": fullName,
        "email": email,
        "password": password,
        "about": data.get("bio", ""),
        "gender": gender,
        "skills": data.get("skills", []),
        "resume": resume_path,
        "experience": [
            _with_dates({
                "company_or_organization": (e.get("company") or "").strip(),
                "role": (e.get("title") or "").strip(),
                "description": e.get("description") or "",
            }, e.get("start_date"), e.get("end_date"))
            for e in data.get("experience", [])
        ],
        "qualification": [
            _with_dates({
                "institute": (q.get("institution") or "").strip(),
                "program": (q.get("degree") or "").strip(),
                "description": q.get("description") or "",
            }, q.get("start_date"), q.get("end_date"))
            for q in data.get("qualification", [])
        ],
    })

    token = create_jwt_token({"id": candidate["_id"], "email": candidate["email"], "role": "candidate"})
    return {
        "message": "Candidate created successfully",
        "candidate": candidate,
        "token": token,
        "resumeParsed": bool(data),
    }


# Fixed paths must be declared before the id route
@router.get("/me")
async def candidate_me(user: dict = Depends(require_candidate)):
    return {"message": "success", "candidate": await get_candidate_by_id(user["id"])}


@router.post("/edit")
async def edit_profile(
    user: dict = Depends(require_candidate),
    fullName: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    about: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    age: Optional[str] = Form(None),
    gender: Optional[Literal["male", "female", ""]] = Form(None),
    phone: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),          # JSON array of strings
    qualification: Optional[str] = Form(None),   # JSON array of Qualification
    experience: Optional[str] = Form(None),      # JSON array of Experience
    socials: Optional[str] = Form(None),         # JSON object
    resume: Optional[UploadFile] = File(None),
):
    try:
        skills_list = TypeAdapter(List[str]).validate_python(_json_form(skills, "skills")) if skills is not None else None
        qualifications = TypeAdapter(List[Qualification]).validate_python(_json_form(qualification, "qualification")) if qualification is not None else None
        experiences = TypeAdapter(List[Experience]).validate_python(_json_form(experience, "experience")) if experience is not None else None
        socials_obj = Socials.model_validate(_json_form(socials, "socials")) if socials is not None else None
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=json.loads(e.json()))

    update_data = {
        "fullName": fullName,
        "bio": bio,
        "about": about,
        "address": address,
        "age": age,
        "gender": gender,
        "phone": phone,
        "skills": skills_list,
        "qualification": [q.model_dump(mode="json", exclude_none=True) for q in qualifications] if qualifications is not None else None,
        "experience": [x.model_dump(mode="json", exclude_none=True) for x in experiences] if experiences is not None else None,
        "socials": socials_obj.model_dump(mode="json", exclude_none=True) if socials_obj else None,
    }

    if resume:
        update_data["resume"] = await upload_file(resume)

    updated = await update_candidate(user["id"], update_data)
    return {"message": "Profile updated successfully", "candidate": updated}


@router.get("/list")
async def candidate_list():
    return {"message": "success", "candidates": await get_all_candidates()}


@router.get("/{id}")
async def candidate_get_by_id(id: str):
    return {"message": "success", "candidate": await get_candidate_by_id(id)}
