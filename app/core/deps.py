from fastapi import HTTPException, Request, status


def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def _require_role(request: Request, role: str) -> dict:
    user = get_current_user(request)
    if user.get("role") != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{role.capitalize()} access only")
    return user


def require_candidate(request: Request) -> dict:
    return _require_role(request, "candidate")


def require_company(request: Request) -> dict:
    return _require_role(request, "company")
