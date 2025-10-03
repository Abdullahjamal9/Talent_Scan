from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request, status
import time
import os

async def upload_file(resume: UploadFile):
    try:
        print(resume)
        file_name = f"{time.time()}-{resume.filename.replace(" ", "-")}"
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PARENT_OF_PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
        file_location = os.path.join(PARENT_OF_PARENT_DIR, "uploads", file_name)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as f:
            f.write(await resume.read())

        return f"/uploads/{file_name}"
    
    except Exception as e:
        print('error',e)
        raise HTTPException(status_code=500, detail=str(e))