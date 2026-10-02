from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import Candidate
from app.db.schemas.candidate import CandidateSignInRequest
from app.db.session import session_scope
from app.utils.ids import parse_id
from app.utils.jwt import create_jwt_token
from app.utils.password import hash_password, verify_password

EDITABLE_FIELDS = {
    "fullName", "bio", "about", "address", "age", "gender", "phone",
    "skills", "qualification", "experience", "socials", "resume",
}


def _email_taken() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")


async def create_candidate(data: dict) -> dict:
    with session_scope() as db:
        if db.scalar(select(Candidate.id).where(Candidate.email == data["email"])):
            raise _email_taken()

        candidate = Candidate(
            email=data["email"],
            password=hash_password(data["password"]),
            **{k: data[k] for k in EDITABLE_FIELDS if k in data and data[k] is not None},
        )
        db.add(candidate)
        try:
            db.flush()
        except IntegrityError:
            raise _email_taken()
        return candidate.to_public()


async def sign_in_candidate(payload: CandidateSignInRequest) -> dict:
    with session_scope() as db:
        candidate = db.scalar(select(Candidate).where(Candidate.email == payload.email))
        # Same message for unknown email and wrong password to avoid account enumeration
        if not candidate or not verify_password(payload.password, candidate.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        candidate_id = str(candidate.id)
        token = create_jwt_token({"id": candidate_id, "email": candidate.email, "role": "candidate"})
        return {"token": token, "candidate": {"id": candidate_id, "email": candidate.email}}


async def get_candidate_by_id(id: str) -> dict:
    with session_scope() as db:
        candidate = db.get(Candidate, parse_id(id))
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return candidate.to_public()


async def update_candidate(candidate_id: str, update_data: dict) -> dict:
    update_data = {k: v for k, v in update_data.items() if v is not None and k in EDITABLE_FIELDS}
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    with session_scope() as db:
        candidate = db.get(Candidate, parse_id(candidate_id))
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        for key, value in update_data.items():
            setattr(candidate, key, value)
        db.flush()
        return candidate.to_public()


async def get_all_candidates() -> list:
    with session_scope() as db:
        return [c.to_public() for c in db.scalars(select(Candidate))]
