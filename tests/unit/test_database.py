from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

from northwind.database import get_database_url, get_session, place_records_into_session_and_commit, primary_key

Base = declarative_base()


class ModelWithOnePK(Base):
    __tablename__ = "modelpk1"
    id_field = sa.Column(sa.SmallInteger, primary_key=True, autoincrement=True)
    boolean_field = sa.Column(sa.Boolean, default=False)


class ModelWithTwoPK(Base):
    __tablename__ = "modelpk2"
    id1_field = sa.Column(sa.SmallInteger, primary_key=True)
    id2_field = sa.Column(sa.SmallInteger, primary_key=True)
    boolean_field = sa.Column(sa.Boolean, default=False)


@pytest.mark.parametrize(
    ["user", "pw", "host", "port", "dbname", "dialect"],
    [
        ("user", "password", "localhost", "5432", "database", "postgres"),
    ],
)
def test_get_database_url(user, pw, host, port, dbname, dialect):
    url = get_database_url(user, pw, host, port, dbname, dialect=dialect)
    assert url == f"{dialect}://{user}:{pw}@{host}:{port}/{dbname}"


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


@pytest.mark.parametrize(
    ["model", "pk_columns"],
    [
        (ModelWithOnePK, [ModelWithOnePK.id_field]),
        (ModelWithTwoPK, [ModelWithTwoPK.id1_field, ModelWithTwoPK.id2_field]),
    ],
)
@pytest.mark.asyncio
async def test_primary_key(model, pk_columns, engine):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    primary_keys = list(primary_key(model))
    assert len(primary_keys) == len(pk_columns)
    for pk in primary_keys:
        assert pk in pk_columns

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.mark.parametrize(["value"], [(False,), (True,), (None,)])
@pytest.mark.asyncio
async def test_place_records_into_session_and_commit(value: bool, engine, session: AsyncSession):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    if value is None:
        record = ModelWithOnePK()
    else:
        record = ModelWithOnePK(boolean_field=value)
    await place_records_into_session_and_commit([record], session)

    assert record.id_field is not None
    assert record.id_field == 1  # since each test run in clean env

    if value is None:
        assert record.boolean_field is False
    else:
        assert record.boolean_field is value

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
