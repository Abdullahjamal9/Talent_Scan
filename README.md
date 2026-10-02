# Talent Scan

This project is built with [FastAPI](https://fastapi.tiangolo.com/), a modern, fast (high-performance) web framework for building APIs with Python. Follow the steps below to set up, run, and maintain the project.

## Prerequisites

- Python 3.10 or higher
- Node.js 20 or higher (for the frontend)
- MySQL 8 (or MariaDB 10.5+)
- A Groq API key (resume parsing and match scoring)
- Git

## Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Muzammilzia/Talent-Scan-FastAPI.git
   cd Talent-Scan-FastAPI
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   or
   py -3 -m venv venv
   ```

3. **Activate the virtual environment**:  
   - On Mac:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install the project dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Project

With the virtual environment activated, run the following command to start the FastAPI server:
```bash
python -m uvicorn app.main:app --reload
```
- `app.main:app` is the module path and the FastAPI instance name.
- `--reload` enables auto-reload for development.

The application should be accessible at `http://127.0.0.1:8000`.

## Configuration

Copy `.env.example` to `.env` in the project root and fill it in:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | MySQL connection, e.g. `mysql+pymysql://root:password@localhost:3306/talent_scan`. The database and tables are created on first start |
| `JWT_SECRET_KEY` | Required. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `GROQ_API_KEY` | Resume parsing and AI match scoring. Without it, sign-up still works but profiles are not pre-filled and applications are not scored |
| `GROQ_MODEL` | Optional, defaults to `openai/gpt-oss-120b` |
| `CORS_ORIGINS` | Comma separated allowed origins, defaults to `http://localhost:5173` |

## Frontend

React + Vite + TypeScript + Tailwind, in `frontend/`.

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies `/api` to the backend on port 8000 (override with `VITE_BACKEND_URL`), so no CORS setup is needed.
Run the backend first with `python -m uvicorn app.main:app --reload`. Vite uses port 5173 if it is free, otherwise the
next free port; it prints the address when it starts.

## How it works

- **Candidates** sign up with a PDF resume. The resume is parsed to pre-fill skills, experience and education. They browse jobs ranked by skill match, apply, and track every application through the hiring stages. They can see why they got their match score and can withdraw an application.
- **Companies** post jobs and run an ATS pipeline: applicants are ranked by AI score and move through **Applied, Screening, Interview, Offer, Hired / Rejected** on a drag-and-drop board. Recruiters get an AI analysis per applicant (requirement checklist, summary, suggested interview questions), can re-run it, and keep private notes.
- **Dashboards:** companies see KPIs, an applications trend, the hiring funnel, score distribution and top candidates. Candidates see their application stats, profile strength and recommended jobs.
- API docs are available at `http://localhost:8000/docs`.

### How the AI is used

- **Resume parsing:** the PDF text is sent to Groq, which returns structured JSON (summary, skills, experience, education). Gender and age are deliberately not extracted.
- **Match scoring:** the model rates each requirement of the job as met, partial or missing, and the score is computed from those ratings in code. This is much steadier than asking for a bare number. The candidate is sent anonymised (no name, email, gender or age), and the prompt forbids using protected characteristics.
- **Rate limits and outages:** Groq calls retry with backoff. If the AI is still unavailable, the application is saved unscored and a recruiter can use **Score now / Re-score**.
- **Quality check:** `venv\Scripts\python.exe -m scripts.eval_scoring` runs a small evaluation set against the real model. Run it after changing the prompt or `GROQ_MODEL`.

### Gender-specific roles

A job can be set to **Everyone**, **Female candidates only** or **Male candidates only**. This is an explicit setting made by the recruiter, shown on the posting, and enforced by the server when a candidate applies. The candidate's gender is whatever they enter themselves in their profile; it is never inferred from a resume and never used in scoring. Candidates who have not set a gender are asked to complete their profile before applying to a restricted role. Check that this fits the employment rules that apply to you.

### Privacy

Resumes are not publicly served. They are only available through `/api/v1/resume/{candidate_id}` to the candidate who owns the file and to companies that candidate has applied to.

## Demo data

To see everything populated, load the Pakistani demo data (3 companies, 16 candidates with PDF resumes, jobs including female-only and male-only roles, about 80 applications with AI analyses). It is safe to run twice:

```bash
venv\Scripts\python.exe -m scripts.seed_demo
venv\Scripts\python.exe -m scripts.seed_demo --company you@yourcompany.com   # also fills your own company account
venv\Scripts\python.exe -m scripts.seed_demo --reset                         # removes the demo data again
```

Demo logins (password `demo1234`): companies `hr@indusdigital.demo`, `hr@margalla.demo`, `hr@punjabsoftware.demo`; candidates such as `ahmed.raza@candidates.demo` (male) and `fatima.zahra@candidates.demo` (female).

## Tests

```bash
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest
```

The tests use a temporary SQLite database and a fake AI, so they never touch your MySQL data or call Groq. They cover authentication, roles, company isolation, gender eligibility, scoring fallback and re-score, resume access control, pipeline stages and the dashboards.

## Adding New Packages

1. **Install the new package**:
   ```bash
   pip install <package-name>
   ```

2. **Update `requirements.txt`**: After installing a new package, update the `requirements.txt` file to ensure others can install the latest dependencies:
   ```bash
   pip freeze > requirements.txt
   ```

3. **Commit the updated `requirements.txt`**:
   ```bash
   git add requirements.txt
   git commit -m "Added <package-name> to requirements"
   git push origin <branch-name>
   ```

