from typing import Union
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status, HTTPException
from app.api.v1.routers import api_router
from fastapi.middleware.cors import CORSMiddleware
from .db.base import connect_to_database
from starlette.responses import JSONResponse
from app.utils.jwt import verify_jwt_token
from fastapi.staticfiles import StaticFiles
import os

load_dotenv()

app = FastAPI()

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Allow CORS from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    try:
        path = request.url.path

        if path.startswith("/uploads"):
            return await call_next(request)
        # Skip specific routes (e.g., login, signup)
        if path in [
            "/api/v1/candidate/sign-in", "/api/v1/candidate/sign-up",
            "/api/v1/company/sign-in", "/api/v1/company/sign-up"
        ]:
            return await call_next(request)

        # Skip if request is CORS preflight request
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get authorization header
        authorization: str = request.headers.get("authorization") or request.headers.get("Authorization")
        
        if not authorization or "Bearer " not in authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing or malformed"
            )

        # Extract token
        token = authorization.split(" ")[1]
        
        # Verify token
        payload = verify_jwt_token(token)  # Ensure this function handles exceptions internally
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        # Attach user payload to request state
        request.state.user = payload  

        return await call_next(request)

    except HTTPException as http_exc:
        return JSONResponse(content={"detail": http_exc.detail}, status_code=http_exc.status_code)

    except Exception as e:
        return JSONResponse(
            content={"detail": "Internal server error", "error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

connect_to_database()

# Include the API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return "Hello World!"