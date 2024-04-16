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
        currentGreenPotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).fetchone()[0]
        currentGreenMl = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone()[0]
        currentRedPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).fetchone()[0]
        currentRedMl = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).fetchone()[0]
        currentBluePotions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).fetchone()[0]
        currentBlueMl = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).fetchone()[0]
        for potion in potions_delivered:
            if potion.potion_type == [100, 0, 0, 0]:
                currentGreenPotions += 1
                currentGreenMl -= 100
            if potion.potion_type == [0, 100, 0, 0]:
                currentRedPotions += 1
                currentRedMl -= 100
            if potion.potion_type == [0, 0, 100, 0]:
                currentBluePotions += 1
                currentBlueMl -= 100
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :currentml"), {'currentml': currentGreenMl})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :currentpotions"), {'currentpotions': currentGreenPotions})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :currentml"), {'currentml': currentRedMl})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :currentpotions"), {'currentpotions': currentRedPotions})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = :currentml"), {'currentml': currentBlueMl})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = :currentpotions"), {'currentpotions': currentBluePotions})


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
        currentGreenMl = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).fetchone()[0]
        currentRedMl = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).fetchone()[0]
        currentBlueMl = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).fetchone()[0]
        newGreenPotions = currentGreenMl // 100
        newRedPotions = currentRedMl // 100
        newBluePotions = currentBlueMl // 100
        plan = []
        
        if newGreenPotions > 0:
            plan.append({
                    "potion_type": [0, 100, 0, 0],
                    "quantity": newGreenPotions,
                })
        if newRedPotions > 0:
            plan.append({
                    "potion_type": [100, 0, 0, 0],
                    "quantity": newRedPotions,
                })
        if newBluePotions > 0:
            plan.append({
                    "potion_type": [0, 0, 100, 0],
                    "quantity": newBluePotions,
                })

        return plan

if __name__ == "__main__":
    print(get_bottle_plan())
