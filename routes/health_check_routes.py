from fastapi.responses import JSONResponse
from fastapi import APIRouter

health_check_router = APIRouter()

@health_check_router.get("/api/chat")
async def health_check():
    return JSONResponse(status_code=200, content="API is working")
@health_check_router.get("/")
async def status_check():
    return JSONResponse(status_code=200, content="API is working")