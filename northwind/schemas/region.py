from pydantic import BaseModel


class Region(BaseModel):
    region_description: str

    class Config:
        orm_mode = True


class RegionDB(Region):
    region_id: int | None
