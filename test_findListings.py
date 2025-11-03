from __future__ import annotations
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import pytest

from findListings import load_locations
from findListings import parse_vehicle_query


# Type alias for readability
LocationListing = Dict[str, Any]
LocationsDict = Dict[str, List[LocationListing]]


@pytest.fixture
def sample_listings() -> list[dict[str, Any]]:
    """Sample JSON data mimicking listings.json"""
    return [
        {
            "id": "2f9266ce-7716-40b1-b27f-c1d77a807551",
            "location_id": "d1c331f1-9ae6-4d8a-9d87-a0cf5cfe1536",
            "length": 40,
            "width": 20,
            "price_in_cents": 64683,
        },
        {
            "id": "741a0213-8512-499e-a8f2-8d3aad664d76",
            "location_id": "760ec3ad-5db1-4e81-820b-f15f009d4b5a",
            "length": 20,
            "width": 20,
            "price_in_cents": 16293,
        },
        {
            "id": "2213d790-9641-4ac1-b56f-9883ac54ec1a",
            "location_id": "d1c331f1-9ae6-4d8a-9d87-a0cf5cfe1536",
            "length": 50,
            "width": 25,
            "price_in_cents": 75000,
        },
    ]


def _write_temp_listings(data: list[dict[str, Any]]) -> Path:
    """Helper to write JSON to a temp file"""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(tmp.name, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return Path(tmp.name)


def test_load_locations_returns_dict(sample_listings: list[dict[str, Any]]) -> None:
    """It should return a dictionary mapping location_id to listings"""
    tmp_file = _write_temp_listings(sample_listings)
    result = load_locations(tmp_file)

    assert isinstance(result, dict)
    assert "d1c331f1-9ae6-4d8a-9d87-a0cf5cfe1536" in result
    assert isinstance(result["d1c331f1-9ae6-4d8a-9d87-a0cf5cfe1536"], list)


def test_load_locations_groups_by_location_id(sample_listings: list[dict[str, Any]]) -> None:
    """It should group multiple listings under the same location_id"""
    tmp_file = _write_temp_listings(sample_listings)
    result = load_locations(tmp_file)

    # This location_id appears twice in the sample
    group = result["d1c331f1-9ae6-4d8a-9d87-a0cf5cfe1536"]
    assert len(group) == 2
    assert all("id" in listing for listing in group)


def test_load_locations_includes_expected_fields(sample_listings: list[dict[str, Any]]) -> None:
    """Each listing should include id, length, width, and price_in_cents"""
    tmp_file = _write_temp_listings(sample_listings)
    result = load_locations(tmp_file)

    first_key = next(iter(result))
    listing = result[first_key][0]
    expected_keys = {"id", "length", "width", "price_in_cents"}
    assert set(listing.keys()) == expected_keys



def test_parse_vehicle_query_expands_quantities() -> None:
    """It should expand each query item by its quantity into a flat list of lengths."""
    vehicle_query = [
        {"length": 10, "quantity": 1},
        {"length": 20, "quantity": 2},
        {"length": 25, "quantity": 1},
    ]

    result = parse_vehicle_query(vehicle_query)

    assert result == [10, 20, 20, 25]
    assert all(isinstance(x, int) for x in result)
    assert len(result) == sum(q["quantity"] for q in vehicle_query)
