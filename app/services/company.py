from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import Company
from app.db.schemas.company import CompanyCreate, CompanySignInRequest
from app.db.session import session_scope
from app.utils.ids import parse_id
from app.utils.jwt import create_jwt_token
from app.utils.password import hash_password, verify_password

EDITABLE_FIELDS = {"name", "about", "address", "phone", "profilePicture", "totalEmployees", "socials"}


def _email_taken() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")


async def create_company(data: CompanyCreate) -> dict:
    with session_scope() as db:
        if db.scalar(select(Company.id).where(Company.email == data.email)):
            raise _email_taken()

        company = Company(
            email=data.email,
            password=hash_password(data.password),
            name=data.name,
            about=data.about,
            profilePicture=data.profilePicture,
            totalEmployees=data.totalEmployees,
            address=data.address,
            phone=data.phone,
            socials=data.socials.model_dump(mode="json", exclude_none=True) if data.socials else {},
        )
        db.add(company)
        try:
            db.flush()
        except IntegrityError:
            raise _email_taken()
        return company.to_public()


async def sign_in_company(payload: CompanySignInRequest) -> dict:
    with session_scope() as db:
        company = db.scalar(select(Company).where(Company.email == payload.email))
        # Same message for unknown email and wrong password to avoid account enumeration
        if not company or not verify_password(payload.password, company.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        company_id = str(company.id)
        token = create_jwt_token({"id": company_id, "email": company.email, "role": "company"})
        return {"token": token, "company": {"id": company_id, "email": company.email}}


async def get_company_by_id(id: str) -> dict:
    with session_scope() as db:
        company = db.get(Company, parse_id(id))
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        return company.to_public()


async def company_update(company_id: str, update_data: dict) -> dict:
    # Drop empty values so a blank form field never wipes existing data
    update_data = {k: v for k, v in update_data.items() if v not in (None, "") and k in EDITABLE_FIELDS}

    if "socials" in update_data and isinstance(update_data["socials"], dict):
        update_data["socials"] = {k: str(v) for k, v in update_data["socials"].items() if v not in (None, "")}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update.")

    with session_scope() as db:
        company = db.get(Company, parse_id(company_id))
        if not company:
            raise HTTPException(status_code=404, detail="Company not found.")
        for key, value in update_data.items():
            setattr(company, key, value)
        db.flush()
        return company.to_public()


async def get_all_companies() -> list:
    with session_scope() as db:
        return [c.to_public() for c in db.scalars(select(Company))]
