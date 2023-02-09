from unittest import mock

import pytest

from northwind.models.region import Region, RegionService
from northwind.utils import make_object_factory

region_factory = make_object_factory(Region)
REGION_DESCRIPTION = "DESCRIPTION"


def test_valid_region_fields_after_its_initialization():
    region = region_factory(region_id=1, region_description=REGION_DESCRIPTION)
    assert region.region_id == 1
    assert region.region_description == REGION_DESCRIPTION


@mock.patch("northwind.database.CreateMixin.create")
@pytest.mark.asyncio
async def test_create_region_using_own_CRUDService(_create):
    service = RegionService()
    payload = {"region_description": REGION_DESCRIPTION}

    await service.create(payload)

    _create.assert_called_once_with(Region, payload)
