from fastapi import HTTPException


def parse_id(value) -> int:
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid ID")
    if parsed < 1:
        raise HTTPException(status_code=400, detail="Invalid ID")
    return parsed
