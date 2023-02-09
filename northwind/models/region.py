import sqlalchemy as sa

from northwind.database import Base, CRUDService


class Region(Base):
    __tablename__ = "region"

    region_id = sa.Column("region_id", sa.SmallInteger, primary_key=True, autoincrement=True)
    region_description = sa.Column("region_description", sa.String(60), nullable=False)


class RegionService(CRUDService):
    default_model = Region
