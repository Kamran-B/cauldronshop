import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        currentpotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone()[0]
        currentml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone()[0]
        for potion in potions_delivered:
            currentpotions += 1
            currentml -= 100
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :currentml"), {'currentml': currentml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :currentpotions"), {'currentpotions': currentpotions})


    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    newpotions = 0
    with db.engine.begin() as connection:
        currentml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone()[0]
        newpotions = currentml // 100
        plan = []
        #newpotions += currentml // 100
        #currentml -= 100 * (currentml // 100)
        #connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :currentml"), {'currentml': currentml})
        #connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = num_green_potions + :newpotions"), {'newpotions': newpotions})
        if newpotions > 0:
            plan.append({
                    "potion_type": [0, 0, 1, 0],
                    "quantity": newpotions,
                })

        return plan

if __name__ == "__main__":
    print(get_bottle_plan())
