import os

from tests.conftest import FAKE_ANALYSIS, PDF


# ---------- authentication and roles ----------

def test_requests_without_token_are_rejected(client):
    assert client.get("/api/v1/job-post/list").status_code == 401
    assert client.get("/api/v1/dashboard/company").status_code == 401


def test_docs_and_health_are_public(client):
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200


def test_roles_are_enforced(client, make):
    cand, comp = make.candidate(), make.company()
    assert client.post("/api/v1/job-post/create", headers=cand["h"], json={"role": "x"}).status_code == 403
    assert client.get("/api/v1/dashboard/company", headers=cand["h"]).status_code == 403
    assert client.get("/api/v1/dashboard/candidate", headers=comp["h"]).status_code == 403
    assert client.get("/api/v1/candidate/me", headers=comp["h"]).status_code == 403


def test_sign_up_rules(client, make):
    make.candidate("a@example.com")
    dup = client.post(
        "/api/v1/candidate/sign-up",
        data={"fullName": "Dup", "email": "a@example.com", "password": "secret123"},
        files={"resume": ("cv.pdf", PDF, "application/pdf")},
    )
    assert dup.status_code == 409
    not_pdf = client.post(
        "/api/v1/candidate/sign-up",
        data={"fullName": "X", "email": "b@example.com", "password": "secret123"},
        files={"resume": ("cv.txt", b"hello", "text/plain")},
    )
    assert not_pdf.status_code == 400
    bad_login = client.post("/api/v1/candidate/sign-in", json={"email": "a@example.com", "password": "wrong"})
    assert bad_login.status_code == 401


def test_parser_never_sets_gender(client, monkeypatch):
    # Even if a parser returned a gender, the profile must only hold what the candidate declared
    monkeypatch.setattr(
        "app.api.v1.endpoints.candidate.parse_resume",
        lambda path: {"skills": ["Python"], "bio": "Dev", "gender": "female", "age": 30},
    )
    r = client.post(
        "/api/v1/candidate/sign-up",
        data={"fullName": "P", "email": "p@example.com", "password": "secret123"},
        files={"resume": ("cv.pdf", PDF, "application/pdf")},
    )
    cand = r.json()["candidate"]
    assert cand["skills"] == ["Python"]
    assert cand["gender"] == "" and cand["age"] == ""


# ---------- gender eligibility ----------

def test_female_only_job_rules(client, make):
    comp = make.company()
    job = make.job(comp, genderRestriction="female")
    woman = make.candidate("w@example.com", gender="female")
    man = make.candidate("m@example.com", gender="male")
    unset = make.candidate("u@example.com", gender="")

    assert make.apply(woman, job).status_code == 200

    refused = make.apply(man, job)
    assert refused.status_code == 403 and "female candidates only" in refused.json()["detail"]

    missing = make.apply(unset, job)
    assert missing.status_code == 403 and "set your gender" in missing.json()["detail"]


def test_eligibility_is_reported_to_candidates(client, make):
    comp = make.company()
    job = make.job(comp, genderRestriction="male")
    woman = make.candidate("w@example.com", gender="female")
    assert client.get(f"/api/v1/job-post/{job}", headers=woman["h"]).json()["eligibility"] == "not_eligible"
    listed = client.get("/api/v1/job-post/recommended_list", headers=woman["h"]).json()["jobs"]
    assert listed[0]["eligibility"] == "not_eligible"

    open_job = make.job(comp, role="Open role")
    assert client.get(f"/api/v1/job-post/{open_job}", headers=woman["h"]).json()["eligibility"] == "ok"


def test_gender_restriction_can_be_edited_by_owner_only(client, make):
    owner, other = make.company(), make.company("other@example.com", "Other")
    job = make.job(owner)
    assert client.post("/api/v1/job-post/edit", headers=other["h"], json={"id": job, "genderRestriction": "female"}).status_code == 403
    assert client.post("/api/v1/job-post/edit", headers=owner["h"], json={"id": job, "genderRestriction": "female"}).status_code == 200
    assert client.get(f"/api/v1/job-post/{job}", headers=owner["h"]).json()["genderRestriction"] == "female"


# ---------- applying, analysis and privacy ----------

def test_apply_stores_score_and_analysis(client, make):
    comp, cand = make.company(), make.candidate()
    job = make.job(comp)
    r = make.apply(cand, job)
    assert r.status_code == 200 and r.json()["AIScore"] == FAKE_ANALYSIS["score"]
    assert make.apply(cand, job).status_code == 409  # cannot apply twice

    # Recruiters get the full analysis incl. interview questions and notes; candidates must not
    recruiter = client.get(f"/api/v1/job-application/get-by-company-and-job/{job}", headers=comp["h"]).json()["data"][0]
    assert recruiter["analysis"]["questions"] == FAKE_ANALYSIS["questions"] and "notes" in recruiter

    own = client.get(f"/api/v1/job-application/get-by-candidate/{cand['id']}", headers=cand["h"]).json()["data"][0]
    assert "notes" not in own and "questions" not in own["analysis"]
    assert own["analysis"]["strengths"] == ["Python"]


def test_application_survives_llm_outage_and_can_be_rescored(client, make, monkeypatch):
    comp, cand = make.company(), make.candidate()
    job = make.job(comp)
    monkeypatch.setattr("app.api.v1.endpoints.job_application.analyze_candidate_for_job", lambda c, j: None)
    r = make.apply(cand, job)
    assert r.status_code == 200 and r.json()["AIScore"] is None

    app_id = client.get(f"/api/v1/job-application/get-by-company-and-job/{job}", headers=comp["h"]).json()["data"][0]["_id"]
    assert client.post(f"/api/v1/job-application/rescore/{app_id}", headers=comp["h"]).status_code == 502

    monkeypatch.setattr("app.api.v1.endpoints.job_application.analyze_candidate_for_job", lambda c, j: dict(FAKE_ANALYSIS))
    fixed = client.post(f"/api/v1/job-application/rescore/{app_id}", headers=comp["h"])
    assert fixed.status_code == 200 and fixed.json()["AIScore"] == FAKE_ANALYSIS["score"]


def test_company_isolation(client, make):
    owner, other = make.company(), make.company("other@example.com", "Other")
    cand = make.candidate()
    job = make.job(owner)
    make.apply(cand, job)
    app_id = client.get(f"/api/v1/job-application/get-by-company-and-job/{job}", headers=owner["h"]).json()["data"][0]["_id"]

    assert client.get(f"/api/v1/job-application/get-by-company-and-job/{job}", headers=other["h"]).status_code == 403
    assert client.post(f"/api/v1/job-application/status/{app_id}", headers=other["h"], json={"status": "hired"}).status_code == 404
    assert client.post(f"/api/v1/job-application/notes/{app_id}", headers=other["h"], json={"notes": "x"}).status_code == 404
    assert client.post(f"/api/v1/job-application/rescore/{app_id}", headers=other["h"]).status_code == 404
    assert client.get("/api/v1/job-application/get-by-company", headers=other["h"]).json()["data"] == []


def test_pipeline_stages_and_notes(client, make):
    comp, cand = make.company(), make.candidate()
    job = make.job(comp)
    make.apply(cand, job)
    app_id = client.get(f"/api/v1/job-application/get-by-company-and-job/{job}", headers=comp["h"]).json()["data"][0]["_id"]

    for stage in ("screening", "interview", "offer", "hired", "rejected", "applied"):
        assert client.post(f"/api/v1/job-application/status/{app_id}", headers=comp["h"], json={"status": stage}).status_code == 200
    assert client.post(f"/api/v1/job-application/status/{app_id}", headers=comp["h"], json={"status": "pending"}).status_code == 422
    assert client.post(f"/api/v1/job-application/notes/{app_id}", headers=comp["h"], json={"notes": "Good"}).status_code == 200
    row = client.get(f"/api/v1/job-application/get-by-company-and-job/{job}", headers=comp["h"]).json()["data"][0]
    assert row["notes"] == "Good" and row["status"] == "applied"


def test_withdraw_rules(client, make):
    comp, cand, other = make.company(), make.candidate(), make.candidate("o@example.com")
    job = make.job(comp)
    make.apply(cand, job)
    app_id = client.get(f"/api/v1/job-application/get-by-candidate/{cand['id']}", headers=cand["h"]).json()["data"][0]["_id"]

    assert client.post(f"/api/v1/job-application/withdraw/{app_id}", headers=other["h"]).status_code == 404
    client.post(f"/api/v1/job-application/status/{app_id}", headers=comp["h"], json={"status": "offer"})
    assert client.post(f"/api/v1/job-application/withdraw/{app_id}", headers=cand["h"]).status_code == 400
    client.post(f"/api/v1/job-application/status/{app_id}", headers=comp["h"], json={"status": "rejected"})
    assert client.post(f"/api/v1/job-application/withdraw/{app_id}", headers=cand["h"]).status_code == 400
    client.post(f"/api/v1/job-application/status/{app_id}", headers=comp["h"], json={"status": "screening"})
    assert client.post(f"/api/v1/job-application/withdraw/{app_id}", headers=cand["h"]).status_code == 200
    assert client.get(f"/api/v1/job-application/get-by-candidate/{cand['id']}", headers=cand["h"]).json()["data"] == []


def test_closed_jobs_reject_applications(client, make):
    comp, cand = make.company(), make.candidate()
    job = make.job(comp, isAcceptingApplications=False)
    assert make.apply(cand, job).status_code == 400


# ---------- resume access ----------

def test_resume_access_control(client, make):
    comp, other = make.company(), make.company("other@example.com", "Other")
    cand, stranger = make.candidate(), make.candidate("s@example.com")
    job = make.job(comp)
    url = f"/api/v1/resume/{cand['id']}"

    assert client.get(url).status_code == 401                                   # anonymous
    assert client.get(url, headers=cand["h"]).status_code == 200                 # owner
    assert client.get(url, headers=comp["h"]).status_code == 404                 # no application yet
    make.apply(cand, job)
    ok = client.get(url, headers=comp["h"])                                      # company it was sent to
    assert ok.status_code == 200 and ok.headers["content-type"] == "application/pdf" and ok.content == PDF
    assert client.get(url, headers=other["h"]).status_code == 404                # unrelated company
    assert client.get(url, headers=stranger["h"]).status_code == 404            # other candidate


def test_uploads_are_not_served_statically(client, make):
    cand = make.candidate()
    path = client.get("/api/v1/candidate/me", headers=cand["h"]).json()["candidate"]["resume"]
    assert path.startswith("/uploads/")
    assert os.path.exists(os.path.join(os.environ["UPLOADS_DIR"], os.path.basename(path)))
    assert client.get(path).status_code in (401, 404)


# ---------- dashboards ----------

def test_dashboards(client, make):
    comp, cand = make.company(), make.candidate()
    job = make.job(comp)
    make.apply(cand, job)

    d = client.get("/api/v1/dashboard/company", headers=comp["h"]).json()
    assert d["kpis"]["totalApplicants"] == 1 and d["kpis"]["openJobs"] == 1
    assert d["funnel"][0] == {"stage": "applied", "count": 1}
    assert len(d["trend"]) == 14 and sum(t["count"] for t in d["trend"]) == 1
    assert d["topCandidates"][0]["score"] == FAKE_ANALYSIS["score"]

    c = client.get("/api/v1/dashboard/candidate", headers=cand["h"]).json()
    assert c["kpis"]["applications"] == 1 and c["kpis"]["active"] == 1
    assert c["profile"]["percent"] < 100 and "Skills" in c["profile"]["missing"]
