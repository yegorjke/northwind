from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from northwind.database import get_session
from northwind.models.region import Region
from northwind.schemas.region import RegionDetail

router = APIRouter(prefix="/regions")


@router.get("/")
async def get_regions(session_local: AsyncSession = Depends(get_session)):
    async with session_local() as session:
        async with session.begin():
            stmt = select(Region)
            regions = (await session.execute(stmt)).scalars().all()

    return regions


@router.get("/{id}")
async def get_region_details(id: int, session_local: AsyncSession = Depends(get_session)) -> RegionDetail:
    async with session_local() as session:
        async with session.begin():
            stmt = select(Region).filter(Region.region_id == id)
            region = (await session.execute(stmt)).scalars().one()

    return region
