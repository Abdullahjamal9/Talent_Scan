import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api.v1.routers import api_router
from app.core.config import CORS_ORIGINS, UPLOADS_DIR
from app.db.base import connect_to_database
from app.utils.jwt import verify_jwt_token

app = FastAPI(title="Talent Scan API")

# Resumes are personal data: they are not served statically, only via the authorised /api/v1/resume endpoint
os.makedirs(UPLOADS_DIR, exist_ok=True)

PUBLIC_PATHS = {
    "/", "/docs", "/redoc", "/openapi.json",
    "/api/v1/candidate/sign-in", "/api/v1/candidate/sign-up",
    "/api/v1/company/sign-in", "/api/v1/company/sign-up",
}


@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or path in PUBLIC_PATHS:
        return await call_next(request)

    try:
        authorization = request.headers.get("authorization", "")
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing or malformed",
            )
        request.state.user = verify_jwt_token(authorization.split(" ", 1)[1])
    except HTTPException as http_exc:
        return JSONResponse(content={"detail": http_exc.detail}, status_code=http_exc.status_code)

    return await call_next(request)


# Added after the auth middleware so CORS headers are also set on 401 responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connect_to_database()

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "ok"}
