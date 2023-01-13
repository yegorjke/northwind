from fastapi import APIRouter, FastAPI, Request, Response

app = FastAPI()

router = APIRouter(prefix="/api")


@router.get("/")
async def index():
    return {"message": "hello world"}


app.include_router(router)
