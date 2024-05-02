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
        numPotions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger")).fetchone()[0]
        gold = connection.execute(sqlalchemy.text("SELECT sum(change) FROM gold_ledger")).fetchone()[0]
        ml = connection.execute(sqlalchemy.text("SELECT sum(change) FROM ml_ledger")).fetchone()[0]
    return {"number_of_potions": numPotions, "ml_in_barrels": ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        potion_capacity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM capacity_ledger WHERE type = 'potion'")).fetchone()[0]
        ml_capacity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM capacity_ledger WHERE type = 'ml'")).fetchone()[0]
        gold = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM gold_ledger")).fetchone()[0]

    new_ml_cap = 0
    new_potion_cap = 0
    if gold > 1500:
        if (ml_capacity / 10000) <= (potion_capacity / 50):
            gold -= 1000
            new_ml_cap += 1
        else:
            gold -= 1000
            new_potion_cap += 1


    return {
        "potion_capacity": new_potion_cap,
        "ml_capacity": new_ml_cap
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

    with db.engine.begin() as connection:
        if capacity_purchase.potion_capacity > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO capacity_ledger (change, type, description)
                                                VALUES (:cap, 'potion', 'bought potion capacity')
                                                """), {'cap': capacity_purchase.potion_capacity * 50})
        
        if capacity_purchase.ml_capacity > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO capacity_ledger (change, type, description)
                                                VALUES (:cap, 'ml', 'bought ml capacity')
                                                """), {'cap': capacity_purchase.ml_capacity * 10000})
        
        units_bought = capacity_purchase.potion_capacity + capacity_purchase.ml_capacity

        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (change, description)
                                                VALUES (:cost, 'bought capacity')
                                                """), {'cost': units_bought * -1000})

    return "OK"
