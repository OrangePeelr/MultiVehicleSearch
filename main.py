from pydantic import BaseModel

from fastapi import FastAPI

from findListings import findListings

app = FastAPI()

class VehicleQuery(BaseModel):
    length: int
    quantity: int
    
class LocationsResponse(BaseModel):
    locations: list

def parse_vehicle_queries(vehicle_queries: list[VehicleQuery]) -> list[dict[str, int]]:
    parsed = []
    for query in vehicle_queries:
        parsed.append({"length" : query.length, "quantity" : query.quantity})
    return parsed

@app.post("/")
def get_items(vehicle_queries: list[VehicleQuery]) -> list[dict[str, str | list[str] | int]]:
    print("this is the query\n\n\n\n\n")
    print(vehicle_queries)
    parsed_vehicle_queries = parse_vehicle_queries(vehicle_queries)
    print(parsed_vehicle_queries)
    response = findListings(parsed_vehicle_queries)
    return response