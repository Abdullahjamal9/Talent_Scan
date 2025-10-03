from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request, status
from app.db.schemas.candidate import CandidateCreate, CandidateSignInRequest, Socials, Qualification, Experience
from app.services.candidate import create_candidate, sign_in_candidate, get_candidate_by_id, update_candidate, get_all_candidates
from enum import Enum
from app.utils.upload_file import upload_file
from app.utils.parsing import process_resumes
from typing import Literal, List, Optional
import json
import time
from datetime import datetime, date
from pydantic import ValidationError
import os

router = APIRouter()

class Candidate_Routes(str, Enum):
    SIGN_IN = '/sign-in'
    SIGN_UP = '/sign-up'
    GET_CANDIDATE_BY_ID = '/{id}'
    CANDIDATE_ME = '/me'
    PROFILE_EDIT = '/edit'
    LIST_CANDIDATES = '/list'


@router.post(Candidate_Routes.SIGN_IN.value)
async def sign_in(candidate: CandidateSignInRequest):
    try:
        result = await sign_in_candidate(candidate)
        return {"message": "Candidate signed in successfully", "data": result}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e.detail))



@router.post(Candidate_Routes.SIGN_UP.value)
async def sign_up(
    fullName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    resume: UploadFile = File(...),
):
    try:
        # Upload the resume file
        file_location = await upload_file(resume)

        # Process the resume to extract data
        result = process_resumes([file_location])
        print(result["results"][0]["data"])  # This prints the extracted data

        # Extract data from the result
        data = result["results"][0]["data"]

        # Gender handling: ensure it’s only "male", "female", or ""
        gender = data.get("gender", "").strip().lower()
        if gender not in ["male", "female"]:
            gender = ""

        # Function to parse date strings to datetime.date
        def parse_date(date_str: str) -> Optional[datetime]:
            try:
                # You can adjust the format here if necessary
                return datetime.strptime(date_str, "%m/%Y") if date_str else None
            except ValueError:
                return None

        # Convert experience and qualification dates
        experience_data = [
            {
                "company_or_organization": exp.get("company", "").strip(),
                "role": exp.get("title", "").strip(),
                "description": exp.get("description", "")
            }
            for exp in data.get("experience", [])
        ]

        qualification_data = [
            {
                "institute": qual.get("institution", "").strip(),
                "program": qual.get("degree", "").strip(),
                "description": qual.get("description", "")
            }
            for qual in data.get("qualification", [])
        ]

        # Create the candidate object
        candidate = {
            "fullName":fullName,
            "about": data.get("bio", ""),
            "age": data.get("age", ""),
            "email":email,
            "password":password,
            "skills":data.get("skills", []),
            "resume":file_location,
            "gender":gender,
            "experience":experience_data,
            "qualification":qualification_data
        }

        print(candidate)

        # Call the database function to create the candidate
        # result = await create_candidate(candidate)

        # Return the response
        return {"message": "Candidate created successfully", "candidate": "result"}

    except ValidationError as e:
        print('Validation error:', e.errors())
        raise HTTPException(status_code=400, detail="Validation error: " + str(e.errors()))
    except Exception as e:
        print('Error:', e)
        raise HTTPException(status_code=500, detail=str(e))
 
@router.get(Candidate_Routes.CANDIDATE_ME.value)
async def candidate_me(request: Request):
    try:
        candidate = await get_candidate_by_id(request.state.user["id"])
        return {"message": "success", "candidate": candidate}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.post(Candidate_Routes.PROFILE_EDIT.value)
async def edit_profile(
    request: Request,
    fullName: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    about: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    age: Optional[str] = Form(None),
    gender: Optional[Literal["male", "female", ""]] = Form(None),
    phone: Optional[str] = Form(None),
    skills: Optional[str] = Form(None),
    qualification: Optional[List[Qualification]] = Form(None),
    experience: Optional[List[Experience]] = Form(None),
    socials: Optional[str] = Form(None),
    resume: Optional[UploadFile] = File(None),
):
    try:
        # Convert `skills` JSON string back to a Python list
        skills_list: List[str] = json.loads(skills) if skills else []

        # Convert `socials` JSON string back to a Python dictionary
        socials_dict = json.loads(socials) if socials else {}

        candidate_id = request.state.user["id"]  # Extract candidate ID from request state

        update_data = {
            "fullName": fullName,
            "bio": bio,
            "about": about,
            "address": address,
            "age": age,
            "gender": gender,
            "phone": phone,
            "skills": skills_list,
            "qualification": qualification,
            "experience": experience,
            "socials": socials_dict,
        }


        # Remove None values to only update provided fields
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        print(update_data)

        if resume:
            print("inside")
            file_location = await upload_file(resume)
            update_data["resume"] = file_location

        print("herere")

        updated_candidate = await update_candidate(candidate_id, update_data)

        return {"message": "Profile updated successfully", "candidate": updated_candidate}

    except Exception as e:
        print("error", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get(Candidate_Routes.LIST_CANDIDATES.value)
async def candidate_list():
    try:
        candidates = await get_all_candidates()
        return {"message": "success", "candidates": candidates}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.get(Candidate_Routes.GET_CANDIDATE_BY_ID.value)
async def candidate_get_by_id(id: str):
    try:
        candidate = await get_candidate_by_id(id)
        return {"message": "success", "candidate": candidate}
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=e.status_code, detail=str(e))

