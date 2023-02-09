from fastapi import APIRouter, FastAPI

from northwind.api.regions import router as regions

# TODO: add CORSMiddleware
# TODO: add pydantic Setting
# TODO: middleware to check if user is admin


def create_app() -> FastAPI:
    app = FastAPI()

    router = APIRouter(prefix="/api")
    router.include_router(regions)

    app.include_router(router)

    return app
