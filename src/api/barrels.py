import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    newml = 0
    cost = 0

    with db.engine.begin() as connection:
        print("gold tuple:", connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())
        currentgold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone()[0]
        for barrel in barrels_delivered:
            newml += barrel.ml_per_barrel
            cost += barrel.price
        
        print("NEW ML:", newml)
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :new"), {'new': newml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :costval"), {'costval': cost})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    plan = []
    with db.engine.begin() as connection:
        print("gold tuple:", connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())
        currentgold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone()[0]
        currentpotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone()[0]
        for barrel in wholesale_catalog:
            if currentpotions < 10 and "GREEN" in barrel.sku and barrel.price <= currentgold:
                plan.append({"sku": barrel.sku, "quantity": 1})
                break

    return plan

