import asyncio
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm.session import sessionmaker

from northwind.database import Base, get_database_url
from northwind.main import create_app


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def engine():
    # FIXME: remove code duplication
    user = "postgres"
    passw = "postgres"
    host = "localhost"
    port = e if (e := os.getenv("POSTGRES_PORT")) else 5432
    db = e if (e := os.getenv("POSTGRES_DB")) else "northwind"

    database_test_uri = get_database_url(user, passw, host, port, db, dialect="postgresql+asyncpg")
    _engine = create_async_engine(database_test_uri, echo=False)
    yield _engine


@pytest_asyncio.fixture
async def session(engine):
    AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with AsyncSessionLocal() as _session:
        yield _session


@pytest_asyncio.fixture
async def setup_teardown_database(engine):
    async def setup():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    async def teardown():
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)

    return setup, teardown


@pytest_asyncio.fixture
async def application(setup_teardown_database):
    setup, teardown = setup_teardown_database

    await setup()
    yield create_app()
    await teardown()


@pytest_asyncio.fixture
async def client(application):
    async with AsyncClient(app=application, base_url="http://127.0.0.1/", follow_redirects=True) as ac:
        yield ac
