import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Type, TypeVar

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

T = TypeVar("T")

# FIXME: move database params to config
POSTGRES_USER = e if (e := os.getenv("POSTGRES_USER")) else "postgres"
POSTGRES_PASSWORD = e if (e := os.getenv("POSTGRES_PASSWORD")) else "postgres"
POSTGRES_HOST = e if (e := os.getenv("POSTGRES_HOST")) else "localhost"
POSTGRES_PORT = e if (e := os.getenv("POSTGRES_PORT")) else 5432
POSTGRES_DB = e if (e := os.getenv("POSTGRES_DB")) else "northwind"


def get_database_url(user: str, password: str, host: str, port: str, dbname: str, dialect: str = "postgres") -> str:
    return f"{dialect}://{user}:{password}@{host}:{port}/{dbname}"


database_uri = get_database_url(
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    dialect="postgresql+asyncpg",
)

engine = create_async_engine(database_uri, echo=False)

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

Base = declarative_base(metadata=metadata)


@asynccontextmanager
async def get_session(asyncsessionmaker=AsyncSessionLocal) -> AsyncIterator[AsyncSession]:
    try:
        async with asyncsessionmaker() as session:
            yield session
    except:  # noqa: E722
        # FIXME: point out a set of specific exceptions
        await session.rollback()
        raise
    finally:
        await session.close()


def primary_key(model: Base):
    pk: sa.Column
    for pk in model.__table__.primary_key:
        yield pk


def _pk_equals_id(model: Base, id: Any):
    whereclauses = ()
    for pk in primary_key(model):
        whereclauses += (pk == id,)

    return sa.or_(*whereclauses)


async def place_records_into_session_and_commit(records: list, session: AsyncSession):
    async with session:
        async with session.begin():
            session.add_all(records)
            # commit


class CreateMixin:
    @staticmethod
    async def create(model: Type[T], payload: dict[str, Any]) -> T:
        record = model(**payload)

        async with get_session() as session:
            async with session.begin():
                session.add(record)

            await session.refresh(record)

        return record


class RetrieveMixin:
    @staticmethod
    async def retrieve(
        model: Type[T],
        id: Any | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[T]:
        async with get_session() as session:
            async with session.begin():
                stmt = sa.select(model)

                if id:
                    stmt = stmt.where(_pk_equals_id(model, id))
                    result = (await session.execute(stmt)).scalars().one()
                else:
                    if offset:
                        stmt = stmt.offset(offset)
                    if limit:
                        stmt = stmt.limit(limit)
                    result = (await session.execute(stmt)).scalars().all()

            return result


class UpdateMixin:
    @staticmethod
    async def update(model: Type[T], id: Any, payload: dict[str, Any]) -> T:
        async with get_session() as session:
            async with session.begin():
                # look up
                stmt = sa.select(model).where(_pk_equals_id(model, id))
                record = (await session.execute(stmt)).scalars().one()

                # update
                stmt = (
                    sa.update(model)
                    .where(_pk_equals_id(model, id))
                    .values(payload)
                    .execution_options(synchronize_session="fetch")
                )

                await session.execute(stmt)
            await session.refresh(record)

        return record


class DeleteMixin:
    @staticmethod
    async def delete(model: Type[T], id: Any) -> T:
        async with get_session() as session:
            async with session.begin():
                # look up
                stmt = sa.select(model).where(_pk_equals_id(model, id))
                record = (await session.execute(stmt)).scalars().one()

                # delete
                stmt = sa.delete(model).where(_pk_equals_id(model, id)).execution_options(synchronize_session="fetch")
                await session.execute(stmt)

            return record


class CRUDService(CreateMixin, RetrieveMixin, UpdateMixin, DeleteMixin):
    default_model = None  # TODO: think about another idea. i don't like it

    def __init__(self, model: Type[T] | None = None):
        self.model = model if model else self.default_model
        if not self.model:
            raise RuntimeError("'model' should be provided")

    async def create(self, payload: dict[str, Any]) -> T:
        return await CreateMixin.create(self.model, payload)

    async def retrieve(self, id: Any | None = None, offset: int | None = None, limit: int | None = None) -> list[T]:
        return await RetrieveMixin.retrieve(self.model, id=id, offset=offset, limit=limit)

    async def update(self, id: Any, payload: dict[str, Any]):
        return await UpdateMixin.update(self.model, id, payload)

    async def delete(self, id: Any):
        return await DeleteMixin.delete(self.model, id)
