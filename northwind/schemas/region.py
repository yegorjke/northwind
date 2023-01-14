import pydantic as pd
from pydantic import BaseModel


class RegionBase(BaseModel):
    region_id: int
    region_description: str


class RegionDetail(RegionBase):
    class Config:
        orm_mode = True
