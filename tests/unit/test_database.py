from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
import sqlalchemy as sa

# # TODO: mock session.rollback and session.close
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

from northwind.database import _pk_equals_id, get_session, place_records_into_session_and_commit, primary_key

Base = declarative_base()


class ModelForTesting(Base):
    __tablename__ = "testpyModelForTesting"

    id_field = sa.Column(sa.SmallInteger, primary_key=True, autoincrement=True)
    boolean_field = sa.Column(sa.Boolean, default=False)


@pytest.mark.asyncio
async def test_get_session(engine):
    sm = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with get_session(sm) as session:
        async with session.begin():
            result = (await session.execute(sa.text("SELECT 1;"))).scalars().one()

    assert result == 1


@pytest.mark.asyncio
async def test_get_session_rollbacks_when_an_exception_occurs(engine):
    sm = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    with pytest.raises(Exception):  # FIXME: replace with a specific exception
        async with get_session(sm) as session:
            async with session.begin():
                (await session.execute(sa.text("this raises exception;")))


@pytest.mark.asyncio
async def test_primary_key(engine):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    primary_keys = list(primary_key(ModelForTesting))
    assert primary_keys[0] == ModelForTesting.id_field

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.mark.parametrize(["value"], [(False,), (True,), (None,)])
@pytest.mark.asyncio
async def test_place_records_into_session_and_commit(value: bool, engine, session: AsyncSession):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    if value is None:
        record = ModelForTesting()
    else:
        record = ModelForTesting(boolean_field=value)
    await place_records_into_session_and_commit([record], session)

    assert record.id_field is not None
    assert record.id_field == 1  # since each test run in clean env

    if value is None:
        assert record.boolean_field is False
    else:
        assert record.boolean_field is value

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
