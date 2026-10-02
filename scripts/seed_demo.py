r"""Fills the database with Pakistani demo data so every screen has something to show.

Run from the project root:

    venv\Scripts\python.exe -m scripts.seed_demo
    venv\Scripts\python.exe -m scripts.seed_demo --company you@yourcompany.com
    venv\Scripts\python.exe -m scripts.seed_demo --reset

What it creates (all demo logins use the password in scripts/demo_data.py, demo1234):
  - 3 companies (hr@indusdigital.demo, hr@margalla.demo, hr@punjabsoftware.demo)
  - 16 candidates (<name>@candidates.demo) each with a real PDF resume in uploads/
  - 13 jobs (some female-only or male-only) and 50+ applications spread over stages, scores and dates
  - an AI-style analysis (strengths, gaps, interview questions) on every application
  --company EMAIL  also posts a handful of the jobs under that existing company account
                   and gives it applicants, so its dashboard is populated too.
  --reset          removes everything this script created (and only that).

Running it twice is safe: existing demo data is detected and left alone.
"""
import argparse
import random
import re
from datetime import datetime, timedelta

import fitz
from sqlalchemy import delete, select

from app.db.base import connect_to_database
from app.db.models import Candidate, Company, JobApplication, JobPost
from app.db.session import session_scope
from app.utils.password import hash_password
from app.core.config import UPLOADS_DIR
from scripts.demo_data import CANDIDATE_DOMAIN, CANDIDATES, COMPANIES, GENDER_ONLY, JOBS, NOTES, PASSWORD

STAGES = ["applied", "screening", "interview", "offer", "hired", "rejected"]
# Stage odds by fit: strong matches tend to be further along, weak ones get rejected
STAGE_WEIGHTS = {
    "high": [8, 20, 32, 15, 20, 5],
    "mid": [30, 30, 20, 5, 3, 12],
    "low": [30, 15, 3, 0, 0, 52],
}


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def candidate_email(name: str) -> str:
    return f"{slug(name).replace('-', '.')}@{CANDIDATE_DOMAIN}"


def resume_filename(name: str) -> str:
    return f"demo-{slug(name)}.pdf"


def phone(rng: random.Random) -> str:
    return f"+92 3{rng.randint(0, 4)}{rng.randint(0, 9)} {rng.randint(1000000, 9999999)}"


def write_resume_pdf(c: dict, email: str, tel: str) -> None:
    """A plain, parser-friendly one page resume."""
    doc = fitz.open()
    page = doc.new_page()
    margin, width = 50, page.rect.width - 100
    y = 56

    def line(text, size=10, bold=False, gap=4):
        nonlocal y
        font = "hebo" if bold else "helv"
        rect = fitz.Rect(margin, y, margin + width, y + 200)
        used = page.insert_textbox(rect, text, fontsize=size, fontname=font, color=(0.1, 0.1, 0.1))
        lines = max(1, int(len(text) * size * 0.5 / width) + 1)
        y += lines * (size + 3) + gap
        return used

    line(c["name"], size=22, bold=True, gap=2)
    line(c["headline"], size=12, gap=6)
    line(f"{email}  |  {tel}  |  {c['city']}, Pakistan", size=10, gap=14)
    line("PROFESSIONAL SUMMARY", size=11, bold=True, gap=2)
    line(c["summary"], gap=12)
    line("SKILLS", size=11, bold=True, gap=2)
    line(", ".join(c["skills"]), gap=12)
    line("EXPERIENCE", size=11, bold=True, gap=2)
    for title, employer, start, end, what in c["exp"]:
        line(f"{title}, {employer}  ({start} - {end})", bold=True, gap=1)
        line(f"- {what}", gap=8)
    y += 4
    line("EDUCATION", size=11, bold=True, gap=2)
    degree, institute, start, end = c["edu"]
    line(f"{degree}, {institute}  ({start} - {end})", gap=8)

    doc.save(f"{UPLOADS_DIR}/{resume_filename(c['name'])}")
    doc.close()


def iso(month_year: str) -> str | None:
    if month_year == "Present":
        return None
    return datetime.strptime(month_year, "%m/%Y").isoformat()


def candidate_row(c: dict, rng: random.Random) -> Candidate:
    email = candidate_email(c["name"])
    tel = phone(rng)
    write_resume_pdf(c, email, tel)
    degree, institute, start, end = c["edu"]
    return Candidate(
        email=email, password=hash_password(PASSWORD), fullName=c["name"], gender=c["gender"], age=str(c["age"]),
        phone=tel, address=f"{c['city']}, Pakistan", bio=c["headline"], about=c["summary"], skills=c["skills"],
        resume=f"/uploads/{resume_filename(c['name'])}",
        experience=[
            {"role": t, "company_or_organization": e, "description": d, "startDate": iso(s), "endDate": iso(en)}
            for t, e, s, en, d in c["exp"]
        ],
        qualification=[{
            "program": degree, "institute": institute,
            "startDate": datetime(start, 9, 1).isoformat(), "endDate": datetime(end, 6, 1).isoformat(),
        }],
        socials={},
    )


def fit(candidate_skills: list[str], required: list[str]) -> float:
    have = {s.lower() for s in candidate_skills}
    return sum(1 for r in required if r.lower() in have) / len(required)


def demo_analysis(cand: Candidate, role: str, required: list[str], score: int, now: datetime) -> dict:
    """Canned analysis derived from the skill overlap, so the demo needs no LLM calls."""
    have = {s.lower() for s in cand.skills}
    met = [r for r in required if r.lower() in have]
    missing = [r for r in required if r.lower() not in have]
    if score >= 70:
        summary = f"Strong fit for {role}: covers {len(met)} of {len(required)} core requirements with relevant experience."
    elif score >= 45:
        summary = f"Partial fit for {role}: meets {len(met)} of {len(required)} requirements, with notable gaps to explore."
    else:
        summary = f"Weak fit for {role}: only {len(met)} of {len(required)} core requirements are evidenced."
    questions = [f"Tell us about a project where you used {m}." for m in (met[:1] or required[:1])]
    questions += [f"How would you get up to speed with {g} for this role?" for g in missing[:2]]
    questions += ["Describe the most complex problem you solved in your last role."]
    return {
        "summary": summary,
        "requirements": [{"requirement": r, "status": "met" if r in met else "missing"} for r in required],
        "strengths": [f"Hands-on experience with {m}" for m in met[:4]],
        "gaps": [f"No evidence of {g}" for g in missing[:4]],
        "questions": questions[:3],
        "model": "demo-data",
        "generatedAt": now.isoformat(timespec="seconds"),
    }


def make_applications(db, rng, candidates, job_rows, now):
    """job_rows: list of (JobPost, required skills). Picks plausible applicants per job."""
    count = 0
    for job, required in job_rows:
        eligible = [c for c in candidates if job.genderRestriction == "any" or c.gender == job.genderRestriction]
        ranked = sorted(eligible, key=lambda c: fit(c.skills, required) + rng.random() * 0.15, reverse=True)
        strong = [c for c in ranked if fit(c.skills, required) > 0][:rng.randint(3, 5)]
        others = [c for c in ranked if c not in strong]
        applicants = strong + rng.sample(others, k=rng.randint(0, 2))

        for cand in applicants:
            ratio = fit(cand.skills, required)
            score = max(18, min(97, round(28 + 62 * ratio + rng.randint(-6, 9))))
            band = "high" if score >= 70 else "mid" if score >= 45 else "low"
            status = rng.choices(STAGES, STAGE_WEIGHTS[band])[0]
            age_days = rng.choice([rng.randint(0, 13)] * 4 + [rng.randint(14, 30)])
            created = now - timedelta(days=age_days, hours=rng.randint(0, 20))
            updated = created + timedelta(days=rng.randint(0, max(0, age_days)))
            notes = rng.choice(NOTES) if status in ("interview", "offer", "hired") else ""
            db.add(JobApplication(
                candidate_id=cand.id, job_id=job.id, company_id=job.company_id, AIScore=float(score),
                status=status, notes=notes, createdAt=created, updatedAt=min(updated, now),
                aiAnalysis=demo_analysis(cand, job.role, required, score, now),
            ))
            count += 1
    return count


def seed(existing_company_email: str | None):
    rng = random.Random(7)
    now = datetime.now()
    import os
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    with session_scope() as db:
        if db.scalar(select(Company.id).where(Company.email == COMPANIES[0]["email"])):
            print("Demo companies already exist, skipping. Use --reset to remove them first.")
            return

        companies = {}
        for spec in COMPANIES:
            companies[spec["key"]] = Company(
                email=spec["email"], password=hash_password(PASSWORD), name=spec["name"], about=spec["about"],
                address=spec["city"], phone=phone(rng), totalEmployees=spec["employees"],
                socials={"linkedin": spec["linkedin"]},
            )
        db.add_all(companies.values())

        candidates = [candidate_row(c, rng) for c in CANDIDATES]
        db.add_all(candidates)
        db.flush()

        job_rows = []
        for key, role, job_type, low, high, required, intro, _ in JOBS:
            job = JobPost(
                company_id=companies[key].id, role=role, jobType=job_type, minimumSalary=low, maximumSalary=high,
                payingCurrency="PKR", createdAt=now - timedelta(days=rng.randint(8, 35)),
                genderRestriction=GENDER_ONLY.get(role, "any"),
                description=f"{intro} We are hiring in {companies[key].address}.\n\nRequirements: {', '.join(required)}.\n"
                            f"Salary range is per month in PKR.",
            )
            job_rows.append((job, required))
        db.add_all(j for j, _ in job_rows)

        mine = None
        if existing_company_email:
            mine = db.scalar(select(Company).where(Company.email == existing_company_email))
            if not mine:
                raise SystemExit(f"No company account with email {existing_company_email}")
            for key, role, job_type, low, high, required, intro, extra in JOBS:
                if extra:
                    job = JobPost(
                        company_id=mine.id, role=role, jobType=job_type, minimumSalary=low, maximumSalary=high,
                        payingCurrency="PKR", createdAt=now - timedelta(days=rng.randint(6, 25)),
                        genderRestriction=GENDER_ONLY.get(role, "any"),
                        description=f"{intro}\n\nRequirements: {', '.join(required)}.\nSalary range is per month in PKR.",
                    )
                    db.add(job)
                    job_rows.append((job, required))
        db.flush()

        total = make_applications(db, rng, candidates, job_rows, now)

    print(f"Created {len(COMPANIES)} companies, {len(CANDIDATES)} candidates (with PDF resumes), "
          f"{len(job_rows)} jobs and {total} applications.")
    print(f"Logins (password {PASSWORD}):")
    for spec in COMPANIES:
        print(f"  company:   {spec['email']}")
    print(f"  candidate: {candidate_email(CANDIDATES[0]['name'])}")
    if existing_company_email:
        print(f"Also added demo jobs and applicants to your company {existing_company_email}.")


def reset(existing_company_email: str | None):
    with session_scope() as db:
        demo_company_ids = list(db.scalars(select(Company.id).where(Company.email.like("%.demo"))))
        demo_candidate_ids = list(db.scalars(select(Candidate.id).where(Candidate.email.like(f"%@{CANDIDATE_DOMAIN}"))))

        extra_job_ids = []
        if existing_company_email:
            mine = db.scalar(select(Company).where(Company.email == existing_company_email))
            if mine:
                demo_roles = {role for _, role, *_ in JOBS}
                extra_job_ids = list(db.scalars(
                    select(JobPost.id).where(JobPost.company_id == mine.id, JobPost.role.in_(demo_roles),
                                             JobPost.payingCurrency == "PKR")
                ))

        job_ids = extra_job_ids + list(db.scalars(select(JobPost.id).where(JobPost.company_id.in_(demo_company_ids))))
        # Explicit order: SQLite does not enforce ON DELETE CASCADE by default
        db.execute(delete(JobApplication).where(
            (JobApplication.candidate_id.in_(demo_candidate_ids)) | (JobApplication.job_id.in_(job_ids))
        ))
        db.execute(delete(JobPost).where(JobPost.id.in_(job_ids)))
        db.execute(delete(Candidate).where(Candidate.id.in_(demo_candidate_ids)))
        db.execute(delete(Company).where(Company.id.in_(demo_company_ids)))

    import os
    for c in CANDIDATES:
        path = f"{UPLOADS_DIR}/{resume_filename(c['name'])}"
        if os.path.exists(path):
            os.remove(path)
    print("Demo data removed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", metavar="EMAIL", help="existing company account that should also get demo jobs")
    parser.add_argument("--reset", action="store_true", help="delete the demo data instead of creating it")
    args = parser.parse_args()
    connect_to_database()
    reset(args.company) if args.reset else seed(args.company)
