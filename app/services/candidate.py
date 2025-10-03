# app/services/candidate.py
from fastapi import HTTPException, status
from app.db.session import get_candidates_collection
from app.db.schemas.candidate import CandidateCreate, CandidateSignInRequest
from bson import ObjectId  # For MongoDB ObjectId handling
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_jwt_token

async def create_candidate(candidate_data: CandidateCreate) -> dict:
    collection = get_candidates_collection()
    candidate = collection.find_one({ "email": candidate_data["email"] })

    if candidate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )

    # Hash the password before storing it in the database
    hashed_password = hash_password(candidate_data["password"])

    # Candidate data to insert into MongoDB
    candidate_document = {
        "fullName": candidate_data["fullName"],
        "bio": candidate_data.get("bio", ""),  
        "address": candidate_data.get("address", ""),
        "age": candidate_data.get("age", ""),
        "gender": candidate_data.get("gender", ""),
        "phone": candidate_data.get("phone", ""), 
        "email": candidate_data["email"],
        "skills": candidate_data.get("skills", []),
        "qualification": candidate_data.get("qualification", []),
        "experience": candidate_data.get("experience", []),
        "socials": candidate_data.get("socials", {}),
        "password": hashed_password,
        "resume": candidate_data["resume"]
    }

    # Insert the candidate document into MongoDB
    result = collection.insert_one(candidate_document)

    # Return the created candidate with MongoDB _id as string
    candidate_document["_id"] = str(result.inserted_id)
    candidate_document.pop("password")
    return candidate_document

async def sign_in_candidate(payload_candidate: CandidateSignInRequest) -> dict:
    # Fetch the collection
    collection = get_candidates_collection()

    # Search for the candidate by email
    candidate = collection.find_one({"email": payload_candidate.email})
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found."
        )

    # Verify the password
    if not verify_password(payload_candidate.password, candidate["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password."
        )

    # Generate JWT token
    token = create_jwt_token({"id": str(candidate["_id"]), "email": candidate["email"]})

    # Return the token and candidate information
    return {"token": token, "candidate": {"id": str(candidate["_id"]), "email": candidate["email"]}}

async def get_candidate_by_id(id: str) -> dict:
    collection = get_candidates_collection()
    try:
        object_id = ObjectId(id)  # Convert string to ObjectId
    except Exception as e:
        print(f"Invalid ObjectId: {e}")
        return None  # Handle invalid ObjectId cases

    candidate = collection.find_one({"_id": object_id}, {"password": 0})
    candidate["_id"] = str(candidate["_id"])
    return candidate

async def update_candidate(candidate_id: str, update_data: dict) -> dict:
    collection = get_candidates_collection()
    
    # Convert candidate_id to ObjectId
    try:
        object_id = ObjectId(candidate_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid candidate ID")
    
    # Remove any empty or None values to prevent overwriting existing fields with null
    update_data = {k: v for k, v in update_data.items() if v is not None and v != ""}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")
    
    # Update the candidate record
    result = collection.update_one({"_id": object_id}, {"$set": update_data})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Retrieve the updated candidate data
    updated_candidate = collection.find_one({"_id": object_id}, {"password": 0})
    if updated_candidate:
        updated_candidate["_id"] = str(updated_candidate["_id"])
    
    return updated_candidate

async def get_all_candidates() -> list:
    collection = get_candidates_collection()
    candidates = collection.find({}, {"password": 0})  # Exclude password field

    # Convert ObjectId to string and return a list of candidates
    return [{**candidate, "_id": str(candidate["_id"])} for candidate in candidates]