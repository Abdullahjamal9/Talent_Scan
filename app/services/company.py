# app/services/company.py
from fastapi import HTTPException, status
from app.db.session import get_company_collection
from app.db.schemas.company import CompanyCreate, CompanySignInRequest
from bson import ObjectId  # For MongoDB ObjectId handling
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_jwt_token

async def create_company(company_data: CompanyCreate) -> dict:
    collection = get_company_collection()
    company = collection.find_one({ "email": company_data.email })

    if company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already in use"
        )

    # Hash the password before storing it in the database
    hashed_password = hash_password(company_data.password)

    company_document = {
        'name': company_data.name,
        'email': company_data.email,
        'password': hashed_password,
        'about': company_data.about,
        'profilePicture': company_data.profilePicture,
        'totalEmployees': company_data.totalEmployees,
        "address": company_data.address,
        "phone": company_data.phone,
        "socials": company_data.socials,
    }

    # Insert the company document into MongoDB
    result = collection.insert_one(company_document)

    # Return the created company with MongoDB _id as string
    company_document["_id"] = str(result.inserted_id)
    company_document.pop("password")
    return company_document

async def sign_in_company(payload_company: CompanySignInRequest) -> dict:
    # Fetch the collection
    collection = get_company_collection()

    # Search for the company by email
    company = collection.find_one({"email": payload_company.email})
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found."
        )

    # Verify the password
    if not verify_password(payload_company.password, company["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password."
        )

    # Generate JWT token
    token = create_jwt_token({"id": str(company["_id"]), "email": company["email"]})

    # Return the token and company information
    return {"token": token, "company": {"id": str(company["_id"]), "email": company["email"]}}

async def get_company_by_id(id: str) -> dict:
    collection = get_company_collection()
    try:
        object_id = ObjectId(id)  # Convert string to ObjectId
    except Exception as e:
        print(f"Invalid ObjectId: {e}")
        return None  # Handle invalid ObjectId cases

    company = collection.find_one({"_id": object_id}, {"password": 0})
    company["_id"] = str(company["_id"])
    return company

async def company_update(company_id: str, update_data: dict) -> dict:
    collection = get_company_collection()
    try:
        object_id = ObjectId(company_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid company ID: {e}")

    # Remove keys with empty string or None values
    update_data = {k: v for k, v in update_data.items() if v not in [None, ""]}

    if "socials" in update_data and isinstance(update_data["socials"], dict):
        update_data["socials"] = {
            k: str(v) for k, v in update_data["socials"].items() if v not in [None, ""]
        }

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update.")

    result = collection.find_one_and_update(
        {"_id": object_id},
        {"$set": update_data},
        return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="Company not found.")

    result["_id"] = str(result["_id"])
    return result


async def get_all_companies() -> list:
    collection = get_company_collection()
    companies = collection.find({}, {"password": 0})  # Exclude password field

    # Convert ObjectId to string and return a list of candidates
    return [{**company, "_id": str(company["_id"])} for company in companies]