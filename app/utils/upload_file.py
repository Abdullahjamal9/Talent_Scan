import os
import re
import uuid
from fastapi import HTTPException, UploadFile
from app.core.config import MAX_RESUME_BYTES, UPLOADS_DIR


async def upload_file(resume: UploadFile) -> str:
    """Saves a PDF resume and returns its public path (e.g. /uploads/<name>.pdf)."""
    original = os.path.basename(resume.filename or "resume.pdf")
    if not original.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    content = await resume.read()
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail=f"Resume exceeds {MAX_RESUME_BYTES // (1024 * 1024)}MB limit")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", os.path.splitext(original)[0]).strip("-")[:50] or "resume"
    file_name = f"{uuid.uuid4().hex}-{stem}.pdf"

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    with open(os.path.join(UPLOADS_DIR, file_name), "wb") as f:
        f.write(content)

    return f"/uploads/{file_name}"
