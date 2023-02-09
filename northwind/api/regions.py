from fastapi import APIRouter, Body, Depends, Path, Query

from northwind.models.region import RegionService
from northwind.schemas.region import Region, RegionDB

router = APIRouter(
    prefix="/regions",
)


@router.post("/", status_code=201)
async def create_region(body: Region = Body(), service: RegionService = Depends()) -> RegionDB:
    return await service.create(body.dict())


@router.get("/")
async def retrieve_list_of_regions(
    offset: int | None = Query(default=None, ge=0),
    limit: int | None = Query(default=None, ge=0),
    service: RegionService = Depends(),
) -> list[RegionDB]:
    return await service.retrieve(offset=offset, limit=limit)


@router.get("/{id}/")
async def retrieve_region_details(id: int = Path(gt=0), service: RegionService = Depends()) -> RegionDB:
    return await service.retrieve(id)


@router.put("/{id}/")
async def update_region(id: int = Path(gt=0), body: Region = Body(), service: RegionService = Depends()) -> RegionDB:
    return await service.update(id, body.dict(exclude_unset=True))


@router.delete("/{id}/")
async def delete_region(id: int = Path(gt=0), service: RegionService = Depends()) -> RegionDB:
    return await service.delete(id)
