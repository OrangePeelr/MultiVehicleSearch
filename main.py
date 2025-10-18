from typing import Union
from pydantic import BaseModel

from fastapi import FastAPI

app = FastAPI()

class VehicleQuery(BaseModel):
    length: int
    quantity: int


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/")
def get_items(vehicle_queries: list[VehicleQuery]) -> VehicleQuery:
    return vehicle_queries[0]