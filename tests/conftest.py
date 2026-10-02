"""Test setup. The environment must be configured before the app is imported:
tests run against a throwaway SQLite file and uploads folder, never your real MySQL data."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="talentscan-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'test.db').replace(os.sep, '/')}"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["GROQ_API_KEY"] = ""
os.environ["UPLOADS_DIR"] = os.path.join(_tmp, "uploads")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"

FAKE_ANALYSIS = {
    "score": 82.0,
    "summary": "Strong fit.",
    "strengths": ["Python"],
    "gaps": ["Kubernetes"],
    "questions": ["Q1", "Q2", "Q3"],
    "model": "test",
    "generatedAt": "2026-01-01T00:00:00",
}


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    # No network: the LLM is replaced by a canned analysis (tests override this when they need a failure)
    monkeypatch.setattr("app.api.v1.endpoints.job_application.analyze_candidate_for_job", lambda c, j: dict(FAKE_ANALYSIS))
    monkeypatch.setattr("app.api.v1.endpoints.candidate.parse_resume", lambda path: None)


@pytest.fixture
def client():
    return TestClient(app)


class Helpers:
    def __init__(self, client):
        self.c = client

    def candidate(self, email="cand@example.com", gender="", name="Test Candidate"):
        r = self.c.post(
            "/api/v1/candidate/sign-up",
            data={"fullName": name, "email": email, "password": "secret123", "gender": gender},
            files={"resume": ("cv.pdf", PDF, "application/pdf")},
        )
        assert r.status_code == 200, r.text
        return {"id": r.json()["candidate"]["_id"], "h": {"Authorization": "Bearer " + r.json()["token"]}}

    def company(self, email="hr@example.com", name="Acme"):
        r = self.c.post("/api/v1/company/sign-up", json={"name": name, "email": email, "password": "secret123"})
        assert r.status_code == 200, r.text
        r = self.c.post("/api/v1/company/sign-in", json={"email": email, "password": "secret123"})
        data = r.json()["data"]
        return {"id": data["company"]["id"], "h": {"Authorization": "Bearer " + data["token"]}}

    def job(self, company, **fields):
        body = {"role": "Backend Engineer", "description": "Python and FastAPI", "jobType": "remote", **fields}
        r = self.c.post("/api/v1/job-post/create", headers=company["h"], json=body)
        assert r.status_code == 200, r.text
        return r.json()["data"]["id"]

    def apply(self, candidate, job_id):
        return self.c.post("/api/v1/job-application/apply", headers=candidate["h"], json={"job": job_id})


@pytest.fixture
def make(client):
    return Helpers(client)
