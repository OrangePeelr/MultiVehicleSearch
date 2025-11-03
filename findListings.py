import json
import itertools

listings_path = "listings.json"


def load_locations(listings_path=listings_path):
    with open(listings_path) as f:
        listings = json.load(f)

        locations = dict()
        for listing in listings:
            location_id = listing["location_id"]
            location_info = {
                "id": listing["id"],
                "length": listing["length"],
                "width": listing["width"],
                "price_in_cents": listing["price_in_cents"],
            }
            locations.setdefault(location_id, []).append(location_info)
        return locations


def parse_vehicle_query(vehicle_query):
    vehicles = []
    for query_item in vehicle_query:
        quantity = query_item["quantity"]
        vehicles.extend([query_item["length"] for i in range(quantity)])
    return vehicles

def vehicle_order_fit_slot(vehicle_order, location_slots):
    listings_used = set()
    for vehicle_len in vehicle_order:
        updated = False
        for i, slot in enumerate(location_slots):
            if vehicle_len <= slot[1]:
                location_slots[i] = (slot[0], slot[1] - vehicle_len)
                updated = True
                listings_used.add(slot[0])
                break
        if not updated:
            return
    return listings_used

def vehicles_fit_listings(listings, vehicles):
    listings_combinations = set()

    def _can_pack(vehicle_order, slots):
        slots = sorted(slots, reverse=True)
        for vehicle in sorted(vehicle_order, reverse=True):
            placed = False
            for i in range(len(slots)):
                if slots[i] >= vehicle:
                    slots[i] -= vehicle
                    placed = True
                    break
            if not placed:
                return False
        return True

    for orientation in ["width", "length"]:
        for i in range(1, len(listings) + 1):
            for listings_subset in itertools.combinations(listings, i):
                location_slots = []
                for listing in listings_subset:
                    if orientation == "width":
                        num_slots = listing["width"] // 10
                        location_slots.extend([(listing["id"], listing["length"])] * num_slots)
                    elif orientation == "length":
                        num_slots = listing["length"] // 10
                        location_slots.extend([(listing["id"], listing["width"])] * num_slots)
                
                slots = [slot[1] for slot in location_slots]
                if _can_pack(vehicles, slots.copy()):
                    listings_used = frozenset(listing["id"] for listing in listings_subset)
                    listings_cost = sum(listing["price_in_cents"] for listing in listings_subset)
                    listings_combinations.add((frozenset(listings_used), listings_cost))
    return listings_combinations

def findListings(vehicle_query):
    listings_by_location = load_locations(listings_path)

    vehicles = parse_vehicle_query(vehicle_query)

    if not vehicles:
        return []

    locations_used = []

    for location_id, listings in listings_by_location.items():
        listings_used = vehicles_fit_listings(listings, vehicles)
        if listings_used:
            locations_used.append((location_id, list(listings_used)))

    results = []
    for location in locations_used:
        min_combo = min(location[1], key = lambda x : x[1])
        results.append({
            "location_id": location[0],
            "listing_ids": list(min_combo[0]),
            "total_price_in_cents": min_combo[1]
        })
    return results
