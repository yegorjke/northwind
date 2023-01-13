from fastapi import APIRouter, FastAPI

from northwind.api.regions import router as router_regions

app = FastAPI()

router = APIRouter(prefix="/api")
router.include_router(router_regions)


@router.get("/")
async def index():
    return {"message": "hello world"}


app.include_router(router)
