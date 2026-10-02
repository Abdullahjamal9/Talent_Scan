r"""Checks the LLM match scoring against hand-written cases with expected score bands.

Run (needs GROQ_API_KEY in .env, makes about 10 API calls):
    venv\Scripts\python.exe -m scripts.eval_scoring

Use it after changing the prompt (app/utils/parsing.py) or GROQ_MODEL: every case should stay inside its band,
and repeated runs of the same case should not wander by more than a few points.
"""
import sys
import time

from app.utils.parsing import analyze_candidate_for_job

BACKEND_JOB = {
    "role": "Senior Backend Engineer",
    "jobType": "full time",
    "description": "Build and scale REST APIs. Requirements: Python, FastAPI, PostgreSQL, Docker, Redis. 4+ years experience.",
}
DESIGN_JOB = {
    "role": "UI/UX Designer",
    "jobType": "contract",
    "description": "Design mobile and web products. Requirements: Figma, prototyping, user research, design systems.",
}

STRONG_BACKEND = {
    "about": "Backend engineer with 6 years building FastAPI services.",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
    "experience": [{"role": "Backend Engineer", "company_or_organization": "Sapphire Systems", "startDate": "2019-03-01", "endDate": None}],
    "qualification": [{"program": "BS Computer Science", "institute": "FAST-NUCES"}],
}
PARTIAL_BACKEND = {
    "about": "Software developer with 3 years of Django experience.",
    "skills": ["Python", "Django", "MySQL"],
    "experience": [{"role": "Developer", "company_or_organization": "Karachi Soft", "startDate": "2021-01-01", "endDate": None}],
    "qualification": [{"program": "BS Computer Science", "institute": "NED University"}],
}
DESIGNER = {
    "about": "Product designer with a research background.",
    "skills": ["Figma", "UI/UX", "Prototyping", "User Research", "Design Systems"],
    "experience": [{"role": "UI/UX Designer", "company_or_organization": "Pixel Forge", "startDate": "2020-06-01", "endDate": None}],
    "qualification": [{"program": "BFA Design", "institute": "NCA Lahore"}],
}
UNRELATED = {
    "about": "Experienced accountant.",
    "skills": ["Tally", "Bookkeeping", "Taxation"],
    "experience": [{"role": "Accountant", "company_or_organization": "Lahore Traders", "startDate": "2016-01-01", "endDate": None}],
    "qualification": [{"program": "B.Com", "institute": "University of the Punjab"}],
}
EMPTY = {"about": "", "skills": [], "experience": [], "qualification": []}

# (name, candidate, job, minimum, maximum)
CASES = [
    ("strong backend  -> backend job", STRONG_BACKEND, BACKEND_JOB, 80, 100),
    ("partial backend -> backend job", PARTIAL_BACKEND, BACKEND_JOB, 35, 75),
    ("designer        -> design job", DESIGNER, DESIGN_JOB, 80, 100),
    ("designer        -> backend job", DESIGNER, BACKEND_JOB, 0, 30),
    ("accountant      -> backend job", UNRELATED, BACKEND_JOB, 0, 20),
    ("empty profile   -> backend job", EMPTY, BACKEND_JOB, 0, 15),
]
REPEATS = 3
PAUSE = 2.0
MAX_SPREAD = 12  # points between the highest and lowest of the repeats


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # model output can contain characters the Windows console cannot print
    failures = 0
    print(f"{'case':36} {'scores':18} {'band':10} result")
    for name, candidate, job, low, high in CASES:
        scores = []
        for _ in range(REPEATS):
            time.sleep(PAUSE)  # stay under the API rate limit
            result = analyze_candidate_for_job(candidate, job)
            if result is None:
                print(f"{name:36} LLM unavailable (is GROQ_API_KEY set?)")
                return 2
            scores.append(result["score"])
        in_band = all(low <= s <= high for s in scores)
        spread = max(scores) - min(scores)
        ok = in_band and spread <= MAX_SPREAD
        failures += not ok
        label = "ok" if ok else ("OUT OF BAND" if not in_band else f"UNSTABLE (spread {spread:.0f})")
        print(f"{name:36} {str(scores):18} {low}-{high:<6} {label}")

    sample = analyze_candidate_for_job(PARTIAL_BACKEND, BACKEND_JOB)
    if sample:
        print("\nSample explanation for the partial match:")
        print("  summary     :", sample["summary"])
        for r in sample["requirements"]:
            print(f"  {r['status']:8}    :", r["requirement"])
        print("  questions   :", sample["questions"])
    print(f"\n{len(CASES) - failures}/{len(CASES)} cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
