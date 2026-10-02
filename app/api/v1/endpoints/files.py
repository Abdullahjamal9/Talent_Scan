import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import UPLOADS_DIR
from app.core.deps import get_current_user
from app.db.models import Candidate, JobApplication
from app.db.session import session_scope
from app.utils.ids import parse_id

router = APIRouter()


@router.get("/{candidate_id}")
async def get_resume(candidate_id: str, user: dict = Depends(get_current_user)):
    """A resume is visible to its owner and to companies the candidate has applied to."""
    cid = parse_id(candidate_id)

    with session_scope() as db:
        if user.get("role") == "candidate":
            allowed = str(cid) == user["id"]
        elif user.get("role") == "company":
            allowed = db.scalar(
                select(JobApplication.id).where(
                    JobApplication.candidate_id == cid, JobApplication.company_id == parse_id(user["id"])
                )
            ) is not None
        else:
            allowed = False

        candidate = db.get(Candidate, cid)
        resume = candidate.resume if candidate else ""

    # Same response for "no such candidate" and "not allowed" so ids cannot be probed
    if not allowed or not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    path = os.path.join(UPLOADS_DIR, os.path.basename(resume))
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Resume file is missing")

    return FileResponse(path, media_type="application/pdf", headers={"Content-Disposition": "inline"})
