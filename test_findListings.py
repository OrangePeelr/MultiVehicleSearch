from __future__ import annotations
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
import pytest
from unittest.mock import patch

from findListings import load_locations
from findListings import parse_vehicle_query
from findListings import vehicle_order_fit_slot
from findListings import vehicles_fit_listings
from findListings import findListings


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

def test_vehicle_order_fit_slot_single_listing_fit() -> None:
    """Should return a set with one listing ID when all vehicles fit in one slot."""
    location_slots = [("A", 50)]  # one listing, 50 units long
    vehicle_order = [10, 20, 15]  # total 45 units, fits easily

    result = vehicle_order_fit_slot(vehicle_order, location_slots)

    assert result == {"A"}
    # Slot should have been reduced in place (if we didn’t copy)
    # but since we pass location_slots directly, it *is* mutated.
    assert location_slots[0][1] == 5  # 50 - 45 = 5


def test_vehicle_order_fit_slot_multiple_listings_used() -> None:
    """Should return both listing IDs when multiple slots are needed."""
    location_slots = [("A", 25), ("B", 20)]
    vehicle_order = [15, 15, 10]  # needs both A and B

    result = vehicle_order_fit_slot(vehicle_order, location_slots)

    assert result == {"A", "B"}


def test_vehicle_order_fit_slot_not_all_fit_returns_none() -> None:
    """Should return None when at least one vehicle does not fit in any slot."""
    location_slots = [("A", 10)]
    vehicle_order = [10, 15]  # the second vehicle won't fit

    result = vehicle_order_fit_slot(vehicle_order, location_slots)

    assert result is None

def test_vehicles_fit_listings_basic_length_orientation() -> None:
    """Should find a valid combination when vehicles fit under 'length' orientation."""
    listings = [
        {"id": "A", "length": 40, "width": 20, "price_in_cents": 10000},
    ]
    vehicles = [10, 10, 20]  # total 40 fits exactly under length orientation

    result = vehicles_fit_listings(listings, vehicles)

    # Expect one valid combination (the single listing with total cost)
    assert len(result) == 1
    assert (frozenset({"A"}), 10000) in result


def test_vehicles_fit_listings_width_orientation_multiple_slots() -> None:
    """Should use width orientation when vehicles fit under width-based slots."""
    listings = [
        {"id": "A", "length": 30, "width": 40, "price_in_cents": 5000},
    ]
    vehicles = [10, 10, 10, 10]  # 4 vehicles of length 10

    result = vehicles_fit_listings(listings, vehicles)

    # width=40 → 4 slots of length=30 → all vehicles fit
    assert len(result) == 1
    assert (frozenset({"A"}), 5000) in result


def test_vehicles_fit_listings_multiple_listings_used() -> None:
    """Should return a combination that includes both listings if vehicles span across them."""
    listings = [
        {"id": "A", "length": 20, "width": 20, "price_in_cents": 10000},
        {"id": "B", "length": 20, "width": 20, "price_in_cents": 12000},
    ]
    vehicles = [15, 15, 10]  # requires both A and B

    result = vehicles_fit_listings(listings, vehicles)

    # Expect one combo that includes both listings, with total cost 22000
    assert any(combo == (frozenset({"A", "B"}), 22000) for combo in result)

    # Should only contain tuples of (frozenset, cost)
    assert all(isinstance(combo, tuple) and isinstance(combo[0], frozenset) for combo in result)



def test_find_listings_single_valid_location(monkeypatch: Any) -> None:
    """Should return one location with its cheapest valid listing combination."""

    mock_locations = {
        "loc1": [
            {"id": "A", "length": 40, "width": 20, "price_in_cents": 1000},
            {"id": "B", "length": 20, "width": 10, "price_in_cents": 500},
        ]
    }

    vehicle_query = [
        {"length": 10, "quantity": 1},
        {"length": 20, "quantity": 1},
    ]

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # Expect one result dict for the location
    assert isinstance(result, list)
    assert len(result) == 1
    entry = result[0]
    assert entry["location_id"] == "loc1"
    assert "listing_ids" in entry
    assert "total_price_in_cents" in entry
    assert isinstance(entry["listing_ids"], list)
    assert all(isinstance(x, str) for x in entry["listing_ids"])
    assert isinstance(entry["total_price_in_cents"], int)


def test_find_listings_multiple_possible_combinations(monkeypatch: Any) -> None:
    """Should return the cheapest valid combination when several listings fit."""

    mock_locations = {
        "loc1": [
            {"id": "A", "length": 20, "width": 20, "price_in_cents": 100},
            {"id": "B", "length": 20, "width": 20, "price_in_cents": 200},
        ]
    }

    vehicle_query = [
        {"length": 10, "quantity": 2},  # total 20
    ]

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # Should return only the cheapest combination
    assert len(result) == 1
    entry = result[0]
    assert entry["location_id"] == "loc1"
    assert entry["listing_ids"] == ["A"]  # 'A' is cheaper than 'B'
    assert entry["total_price_in_cents"] == 100


def test_find_listings_no_fit_returns_empty(monkeypatch: Any) -> None:
    """Should return an empty list when no vehicles can fit any listing."""

    mock_locations = {
        "loc1": [
            {"id": "A", "length": 5, "width": 5, "price_in_cents": 100},
        ]
    }

    vehicle_query = [
        {"length": 50, "quantity": 1},
    ]

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # No valid configurations
    assert result == []


def test_find_listings_empty_vehicle_query(monkeypatch: Any) -> None:
    """Should return an empty list when vehicle_query is empty."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 20, "width": 20, "price_in_cents": 1000}
        ]
    }

    vehicle_query: list[dict[str, Any]] = []

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    assert result == []


def test_find_listings_empty_locations(monkeypatch: Any) -> None:
    """Should return an empty list when there are no locations."""
    mock_locations: dict[str, list[dict[str, Any]]] = {}

    vehicle_query = [{"length": 10, "quantity": 1}]

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    assert result == []


def test_find_listings_vehicle_larger_than_all_slots(monkeypatch: Any) -> None:
    """Should return an empty list when vehicles are larger than any single listing slot."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 10, "width": 10, "price_in_cents": 1000},
            {"id": "B", "length": 15, "width": 15, "price_in_cents": 1200},
        ]
    }

    vehicle_query = [{"length": 50, "quantity": 1}]  # bigger than any available slot

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    assert result == []


def test_find_listings_duplicate_vehicle_lengths(monkeypatch: Any) -> None:
    """Should correctly handle multiple vehicles of the same length and pick cheapest listings."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 20, "width": 20, "price_in_cents": 800},
            {"id": "B", "length": 20, "width": 20, "price_in_cents": 1000},
        ]
    }

    vehicle_query = [{"length": 10, "quantity": 3}]  # three identical vehicles

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # Should return only cheapest listings combination
    assert len(result) == 1
    entry = result[0]
    assert entry["location_id"] == "loc1"
    assert entry["listing_ids"] == ["A"]
    assert entry["total_price_in_cents"] == 800


def test_find_listings_all_vehicles_fit_single_slot(monkeypatch: Any) -> None:
    """All vehicles fit exactly into a single listing slot; total cost reflects one listing."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 30, "width": 30, "price_in_cents": 1500}
        ]
    }

    vehicle_query = [{"length": 10, "quantity": 3}]  # exactly fits 30-length slot

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    assert len(result) == 1
    entry = result[0]
    assert entry["location_id"] == "loc1"
    assert entry["listing_ids"] == ["A"]
    assert entry["total_price_in_cents"] == 1500

def test_find_listings_prefers_minimum_cost_combination(monkeypatch: Any) -> None:
    """Should return the combination of listings with the lowest total cost."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 30, "width": 30, "price_in_cents": 5000},
            {"id": "B", "length": 30, "width": 30, "price_in_cents": 10000},
        ]
    }

    vehicle_query = [{"length": 10, "quantity": 3}]  # total length 30 fits in one slot

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # Expect single cheapest listing (A)
    assert len(result) == 1
    combo = result[0]
    assert combo["listing_ids"] == ["A"]
    assert combo["total_price_in_cents"] == 5000


def test_find_listings_multiple_combos_selects_lowest_total(monkeypatch: Any) -> None:
    """Should choose a combination with the lowest summed cost when multiple sets fit."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 20, "width": 20, "price_in_cents": 8000},
            {"id": "B", "length": 20, "width": 20, "price_in_cents": 3000},
            {"id": "C", "length": 20, "width": 20, "price_in_cents": 4000},
        ]
    }

    vehicle_query = [{"length": 15, "quantity": 2}]  # needs one listing of 20 or two of them

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # The cheapest single listing that fits should win (B)
    assert len(result) == 1
    combo = result[0]
    assert combo["listing_ids"] == ["B"]
    assert combo["total_price_in_cents"] == 3000


def test_find_listings_combines_multiple_listings_for_cheapest_fit(monkeypatch: Any) -> None:
    """Should choose the cheapest valid multi-listing combination."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 15, "width": 10, "price_in_cents": 2000},
            {"id": "B", "length": 15, "width": 10, "price_in_cents": 2000},
            {"id": "C", "length": 30, "width": 10, "price_in_cents": 5000},
        ]
    }

    vehicle_query = [{"length": 15, "quantity": 2}]  # total length 30 required

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    # Both A and B combined (4000) is cheaper than C (5000)
    assert len(result) == 1
    combo = result[0]
    assert set(combo["listing_ids"]) == {"A", "B"}
    assert combo["total_price_in_cents"] == 4000


def test_find_listings_handles_identical_cost_ties(monkeypatch: Any) -> None:
    """Should return any one of the tied cheapest combos if costs are identical."""
    mock_locations = {
        "loc1": [
            {"id": "A", "length": 30, "width": 20, "price_in_cents": 5000},
            {"id": "B", "length": 30, "width": 20, "price_in_cents": 5000},
        ]
    }

    vehicle_query = [{"length": 10, "quantity": 3}]

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    assert len(result) == 1
    combo = result[0]
    assert combo["listing_ids"] in (["A"], ["B"])
    assert combo["total_price_in_cents"] == 5000


def test_find_listings_ignores_higher_cost_when_both_fit(monkeypatch: Any) -> None:
    """If multiple listings fit individually, only return the cheaper one."""
    mock_locations = {
        "loc1": [
            {"id": "cheap", "length": 40, "width": 10, "price_in_cents": 2000},
            {"id": "expensive", "length": 40, "width": 10, "price_in_cents": 9000},
        ]
    }

    vehicle_query = [{"length": 20, "quantity": 1}, {"length": 20, "quantity": 1}]

    with patch("findListings.load_locations", return_value=mock_locations):
        result = findListings(vehicle_query)

    assert len(result) == 1
    combo = result[0]
    assert combo["listing_ids"] == ["cheap"]
    assert combo["total_price_in_cents"] == 2000