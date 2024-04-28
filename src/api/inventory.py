import sqlalchemy
from fastapi import APIRouter, Depends
from src import database as db
from pydantic import BaseModel
from src.api import auth
import math

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        numPotions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potions")).fetchone()[0]
        gold, red_ml, green_ml, blue_ml, dark_ml = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory")).fetchone()
        gold = connection.execute(sqlalchemy.text("SELECT sum(change) FROM gold_ledger")).fetchone()[0]
        ml = red_ml + green_ml + blue_ml + dark_ml
    return {"number_of_potions": numPotions, "ml_in_barrels": ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return "OK"
