import os
from dotenv import load_dotenv

load_dotenv()

# e.g. mysql+pymysql://user:password@localhost:3306/talent_scan
DATABASE_URL = os.getenv("DATABASE_URL")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "30"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

MAX_RESUME_BYTES = int(os.getenv("MAX_RESUME_MB", "5")) * 1024 * 1024

# Uploaded resumes live here. They are served only through the authorised /resume endpoint.
UPLOADS_DIR = os.path.abspath(os.getenv("UPLOADS_DIR") or os.path.join(os.path.dirname(__file__), "../../uploads"))
