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

def vehicles_fit_listings(listings, vehicle_orderings):
    listings_combinations = set()
    for orientation in ["width", "length"]:
        location_slots = []
        for listing in listings:
            if orientation == "width":
                num_slots = listing["width"] // 10
                location_slots.extend([(listing["id"], listing["length"])] * num_slots)
            elif orientation == "length":
                num_slots = listing["length"] // 10
                location_slots.extend([(listing["id"], listing["width"])] * num_slots)
        
        for vehicle_order in vehicle_orderings:
            listings_used = vehicle_order_fit_slot(vehicle_order, location_slots.copy())
            if listings_used:
                listings_combinations.add(frozenset(listings_used))
    return listings_combinations

def findListings(vehicle_query):
    listings = load_locations(listings_path)
    
    
    # for location in locations:
    #    location_list = []
    #    for vehicle_order in vehicle_orders
    #       if vehicles_fit_location(vehicle_order, location):
    #           location_list.append(location, cost)
    #
    # def vehicles_fit_location(vehicle_order, location): -> listings, cost
    #    remaining_space = dict(listing:(width, length)) # calculate by dividing length by 10 to get number of slots available, and then adding all the slots together to fit max # of cars
    #    used_listings = []
    #    cost = 0
    #    for vehicle in vehicle_order:
    #       vehicle_added = False
    #       for listing in location:
    #           if remaining_width[listing] > vehicle.length:
    #               used_listings.append(listing)
    #               vehicle_added = True
    #               break to new vehicle
    #           else:
    #               continue to next listing
    #       if vehicle_added == False:
    #           break to other orientation below
    #
    #    if all cars don't fit, run for other orientation
    #    
    


    # old code:
    #condensed_queries_list = []
    #for query in vehicle_queries:
    #    for i in range(query["quantity"]):
    #        condensed_queries_list.append()

    #permutations = list(itertools.permutations(vehicle_queries))
    #print(permutations)

'''
listing_quant: dict[str, int] = {}
for i, listing in enumerate(listings):
    cur_id = listing_quant.get(listing['location_id'])
    if cur_id is None:
        listing_quant[listing['location_id']] = 1
    else:
        listing_quant[listing['location_id']] += 1

print(len(listings))
print(listings[0])

print(sorted(listing_quant.items(), key=lambda item: item[1]))
'''