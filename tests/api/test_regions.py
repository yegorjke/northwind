import asyncio
import json
import logging
from functools import partial
from typing import Any, Callable
from unittest import mock

import pytest
import pytest_asyncio

# from fastapi.exception_handlers import request_validation_exception_handler
from httpx import AsyncClient
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from northwind.database import place_records_into_session_and_commit
from northwind.models import Region
from northwind.utils import make_api_url, make_object_factory

pytestmark = pytest.mark.asyncio

TEST_DESCRIPTION = "Test Region"


region_factory = make_object_factory(Region, region_description=TEST_DESCRIPTION)
api_region_url_factory = partial(make_api_url, "/api", "regions")


@pytest.mark.parametrize(
    ["limit", "offset", "regions_count", "expected_count"],
    [
        (None, None, 0, 0),
        (0, None, 0, 0),
        (None, 0, 0, 0),
        (0, 0, 0, 0),
        (None, None, 2, 2),
        (0, None, 2, 2),
        (1, None, 2, 1),
        (2, None, 2, 2),
        (3, None, 2, 2),
        (None, 0, 2, 2),
        (None, 2, 2, 0),
        (None, 2, 4, 2),
        (0, 0, 1, 1),
        (1, 0, 2, 1),
        (2, 0, 2, 2),
        (0, 1, 2, 1),
        (1, 1, 2, 1),
        (2, 1, 2, 1),
        (0, 2, 2, 0),
        (1, 2, 2, 0),
        (2, 2, 2, 0),
    ],
)
async def test_api_get_list_of_regions(
    limit: int | None,
    offset: int | None,
    regions_count: int,
    expected_count: int,
    client: AsyncClient,
    session: AsyncSession,
):

    # fill region table with records according to parameters of test
    regions = [region_factory() for _ in range(regions_count)]
    await place_records_into_session_and_commit(regions, session)

    url = api_region_url_factory(limit=limit, offset=offset)

    response = await client.get(url)
    assert response.status_code == 200

    response_regions = response.json()
    assert type(response_regions) == list
    assert len(response_regions) == expected_count


@pytest.mark.parametrize(
    ["limit", "offset", "expected_response"],
    [
        (
            None,
            -1,
            {
                "detail": [
                    {
                        "loc": ["query", "offset"],
                        "msg": "ensure this value is greater than or equal to 0",
                        "type": "value_error.number.not_ge",
                    }
                ]
            },
        ),
        (
            -1,
            None,
            {
                "detail": [
                    {
                        "loc": ["query", "limit"],
                        "msg": "ensure this value is greater than or equal to 0",
                        "type": "value_error.number.not_ge",
                    }
                ]
            },
        ),
        (
            -1,
            -1,
            {
                "detail": [
                    {
                        "loc": ["query", "offset"],
                        "msg": "ensure this value is greater than or equal to 0",
                        "type": "value_error.number.not_ge",
                    },
                    {
                        "loc": ["query", "limit"],
                        "msg": "ensure this value is greater than or equal to 0",
                        "type": "value_error.number.not_ge",
                    },
                ]
            },
        ),
    ],
)
async def test_api_get_list_of_regions_with_incorrect_query_params_responses_422_and_validator_msg(
    limit: int | None,
    offset: int | None,
    expected_response: dict[str, list[dict]],
    client: AsyncClient,
):
    url = api_region_url_factory(limit=limit, offset=offset)

    response = await client.get(url)
    assert response.status_code == 422

    for d, e in zip(response.json()["detail"], expected_response["detail"]):
        assert d["loc"] == e["loc"]
        assert d["msg"] == e["msg"]
        assert d["type"] == e["type"]


async def test_api_get_region_by_id(client: AsyncClient, session: AsyncSession):
    region: Region = region_factory()
    await place_records_into_session_and_commit([region], session)

    url = api_region_url_factory(region.region_id)

    response = await client.get(url)
    assert response.status_code == 200

    response_region = response.json()
    assert response_region["region_id"] == region.region_id
    assert response_region["region_description"] == TEST_DESCRIPTION


async def test_api_get_region_by_id_raises_error_if_no_rows_found(client: AsyncClient):
    with pytest.raises(NoResultFound):
        await client.get("/api/regions/99999/")


@pytest.mark.parametrize(
    ["id", "expected_response"],
    [
        (
            -1,
            {
                "detail": [
                    {
                        "loc": ["path", "id"],
                        "msg": "ensure this value is greater than 0",
                        "type": "value_error.number.not_gt",
                    },
                ]
            },
        ),
        (
            0,
            {
                "detail": [
                    {
                        "loc": ["path", "id"],
                        "msg": "ensure this value is greater than 0",
                        "type": "value_error.number.not_gt",
                    },
                ]
            },
        ),
        (
            "stupid-string",
            {
                "detail": [
                    {
                        "loc": ["path", "id"],
                        "msg": "value is not a valid integer",
                        "type": "type_error.integer",
                    },
                ]
            },
        ),
    ],
)
async def test_api_get_region_by_id_with_incorrect_id_responses_with_422_and_validator_msg(
    id: int | str,
    expected_response: dict[str, list[dict]],
    client: AsyncClient,
):
    url = api_region_url_factory(id)

    response = await client.get(url)
    assert response.status_code == 422

    details = response.json()["detail"]
    assert len(details) == 1  # only one error occured, related to "id" validation
    assert details[0]["loc"] == expected_response["detail"][0]["loc"]
    assert details[0]["msg"] == expected_response["detail"][0]["msg"]
    assert details[0]["type"] == expected_response["detail"][0]["type"]


@pytest.mark.parametrize(
    ["payload", "expected_region_id"],
    [
        ({"region_description": TEST_DESCRIPTION}, 1),
        ({"region_id": 999, "region_description": TEST_DESCRIPTION}, 1),
    ],
)
async def test_api_create_new_region(
    payload: dict[str, Any],
    expected_region_id: int,
    client: AsyncClient,
):
    url = api_region_url_factory()
    response = await client.post(url, content=json.dumps(payload))

    assert response.status_code == 201

    region = response.json()
    assert region["region_id"] == expected_region_id
    assert region["region_description"] == TEST_DESCRIPTION


@pytest.mark.parametrize(
    ["payload"],
    [
        ({"region_description": "Updated"},),
        ({"region_id": 999, "region_description": "Updated"},),
    ],
)
async def test_api_update_description_of_existing_region(
    payload: dict[str, Any],
    client: AsyncClient,
    session: AsyncSession,
):
    region: Region = region_factory()
    await place_records_into_session_and_commit([region], session)

    url = api_region_url_factory(region.region_id)

    response = await client.put(url, content=json.dumps(payload))
    assert response.status_code == 200

    response_region = response.json()
    # "region_id" should be the same. It shouldn't be changed after request
    assert response_region["region_id"] == region.region_id
    assert response_region["region_description"] == "Updated"


async def test_api_update_but_no_item_found_raised(client: AsyncClient):
    with pytest.raises(NoResultFound):
        await client.put("/api/regions/99999/", content=json.dumps({"region_description": "Updated"}))


async def test_api_delete_region_by_id(client: AsyncClient, session: AsyncSession):
    region: Region = region_factory()
    await place_records_into_session_and_commit([region], session)

    url = api_region_url_factory(region.region_id)

    response = await client.delete(url)
    assert response.status_code == 200

    response_region = response.json()
    assert response_region["region_id"] == region.region_id
