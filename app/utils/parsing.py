import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import fitz
import requests

from app.core.config import GROQ_API_KEY, GROQ_MODEL, UPLOADS_DIR

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# Deliberately no gender or age here: candidates state those themselves, and they must not be guessed from a CV.
RESUME_PROMPT = (
    "You parse resumes. Return ONLY a JSON object with exactly these keys:\n"
    '{"name": str, "email": str, "bio": str (2-3 sentence professional summary), "skills": [str], '
    '"total_experience": number (years), '
    '"experience": [{"title": str, "company": str, "start_date": "MM/YYYY", "end_date": "MM/YYYY"|"Present", "description": str}], '
    '"qualification": [{"degree": str, "institution": str, "start_date": "MM/YYYY", "end_date": "MM/YYYY", "description": str}]}\n'
    "Use MM/YYYY dates (01/YYYY if only the year is known). Use empty strings or empty lists for anything not in the resume. "
    "Most recent items first. Only use information that is written in the resume."
)

ANALYSIS_PROMPT = (
    "You are a careful, fair recruiter judging how well a candidate fits a job. "
    "Judge ONLY on skills, experience, education and the stated job requirements. "
    "Never consider or infer gender, age, name, ethnicity, religion, nationality, marital status or appearance. "
    "Base every statement on the data provided and do not invent facts.\n"
    "Step 1: list the 4 to 8 most important requirements of the job (skills, years of experience, education) as short phrases.\n"
    "Step 2: for each requirement decide whether the candidate data shows it: "
    '"met" (clear evidence), "partial" (related or weak evidence) or "missing" (no evidence). '
    "A closely related technology or partly met requirement counts as partial, for example a different web framework "
    "or SQL database than the one requested, or fewer years of experience than asked.\n"
    "Return ONLY a JSON object:\n"
    '{"summary": one or two sentences for the recruiter, '
    '"requirements": [{"requirement": short phrase, "status": "met"|"partial"|"missing"}], '
    '"questions": [exactly 3 interview questions that probe the partial or missing requirements and the key claims]}'
)

STATUS_POINTS = {"met": 1.0, "partial": 0.5, "missing": 0.0}


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    try:
        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text("text") for page in doc).strip()
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return None


RETRIES = 3


def _groq_json(system: str, user: str) -> Optional[Dict[str, Any]]:
    if not GROQ_API_KEY:
        print("GROQ_API_KEY is not set")
        return None
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
        "max_tokens": 4000,
        "response_format": {"type": "json_object"},
    }
    if GROQ_MODEL.startswith("openai/gpt-oss"):
        payload["reasoning_effort"] = "low"  # fewer hidden reasoning tokens: faster and kinder to rate limits

    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.post(
                GROQ_ENDPOINT,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=45,
            )
            if response.status_code in (429, 500, 502, 503) and attempt < RETRIES:
                # Rate limited or a transient server error: wait as long as the API asks (capped), then retry
                wait = min(float(response.headers.get("retry-after", 2 * attempt)), 20)
                print(f"Groq returned {response.status_code}, retrying in {wait:.0f}s ({attempt}/{RETRIES})")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"Groq request failed: {e}")
            return None
    return None


def parse_resume(resume_path: str) -> Optional[Dict[str, Any]]:
    """Parses a stored resume (path like /uploads/x.pdf). Returns None if parsing fails."""
    abs_path = os.path.join(UPLOADS_DIR, os.path.basename(resume_path))
    text = extract_text_from_pdf(abs_path)
    if not text:
        return None

    data = _groq_json(RESUME_PROMPT, f"Resume text:\n\n{text[:15000]}")
    if not data:
        return None

    if not data.get("email"):
        found = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
        data["email"] = found.group(0) if found else ""
    return data


def _clean_list(value: Any, limit: int) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()][:limit]


def analyze_candidate_for_job(candidate: dict, job: dict) -> Optional[Dict[str, Any]]:
    """Scores a candidate against a job and explains the score. Returns None if the LLM is unavailable.

    The model only rates each job requirement (met / partial / missing); the score is computed from those ratings
    here, which is far steadier than asking a model for a bare number. The candidate is sent anonymised
    (no name, email, gender or age) so the model cannot be swayed by them.
    """
    profile = {
        "summary": candidate.get("about") or candidate.get("bio"),
        "skills": candidate.get("skills", []),
        "experience": candidate.get("experience", []),
        "education": candidate.get("qualification", []),
    }
    posting = {k: job.get(k) for k in ("role", "description", "jobType")}
    result = _groq_json(
        ANALYSIS_PROMPT,
        f"Candidate:\n{json.dumps(profile, default=str)}\n\nJob:\n{json.dumps(posting, default=str)}",
    )
    if not result or not isinstance(result.get("requirements"), list):
        return None

    rated = []
    for item in result["requirements"]:
        status = str(item.get("status", "")).lower() if isinstance(item, dict) else ""
        name = str(item.get("requirement", "")).strip() if isinstance(item, dict) else ""
        if name and status in STATUS_POINTS:
            rated.append((name, status))
    if not rated:
        return None

    score = round(100 * sum(STATUS_POINTS[status] for _, status in rated) / len(rated), 2)
    return {
        "score": score,
        "summary": str(result.get("summary", "")).strip(),
        "requirements": [{"requirement": name, "status": status} for name, status in rated],
        "strengths": [name for name, status in rated if status == "met"][:4],
        "gaps": [f"{name} (partial)" if status == "partial" else name for name, status in rated if status != "met"][:4],
        "questions": _clean_list(result.get("questions"), 3),
        "model": GROQ_MODEL,
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
    }
