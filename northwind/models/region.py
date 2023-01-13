import sqlalchemy as sa

from northwind.database import Base


class Region(Base):
    __tablename__ = "region"

    region_id = sa.Column("region_id", sa.SmallInteger, primary_key=True)
    region_description = sa.Column("region_description", sa.String(60), nullable=False)
