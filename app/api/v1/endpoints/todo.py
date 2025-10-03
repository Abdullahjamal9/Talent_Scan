# todo APIs are just for structure testing, and won't be used in app.
from fastapi import APIRouter, HTTPException
# from app.services.item_service import get_items, create_item
# from app.db.schemas.item import ItemCreate, ItemResponse

router = APIRouter()

@router.get('/')
async def get_todos():
    return ['todo_1', 'todo_2']

# @router.get("/", response_model=list[ItemResponse])
# async def read_items():
#     return await get_items()

# @router.post("/", response_model=ItemResponse)
# async def create_new_item(item: ItemCreate):
#     return await create_item(item)
