from fastapi import APIRouter, FastAPI

from northwind.api.regions import router as regions

# from fastapi.middleware.cors import CORSMiddleware


# TODO: add pydantic Setting


def create_app() -> FastAPI:
    app = FastAPI()

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["*"],
    #     allow_credentials=True,
    #     allow_methods=["*"],
    #     allow_headers=["*"],
    # )

    # TODO: add CORSMiddleware
    router = APIRouter(prefix="/api")
    router.include_router(regions)

    app.include_router(router)

    return app
