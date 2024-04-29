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
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        usedRedMl = 0
        usedGreenMl = 0
        usedBlueMl = 0
        usedDarkMl = 0
        for potion in potions_delivered:
            usedRedMl += potion.potion_type[0] * potion.quantity
            usedGreenMl += potion.potion_type[1] * potion.quantity
            usedBlueMl  += potion.potion_type[2] * potion.quantity
            usedDarkMl += potion.potion_type[3] * potion.quantity
            connection.execute(sqlalchemy.text("""UPDATE potions 
                                            SET quantity = quantity + :quant
                                            WHERE type = :type
                                           """), {'quant': potion.quantity, 'type': str(potion.potion_type)})
            
        if usedRedMl > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (change, type, description)
                                              VALUES (:ml, :type, 'bottling potions')
                                           """), {'ml': -1 * usedRedMl, 'type': '[1, 0, 0, 0]'})
        if usedGreenMl > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (change, type, description)
                                              VALUES (:ml, :type, 'bottling potions')
                                           """), {'ml': -1 * usedGreenMl, 'type': '[0, 1, 0, 0]'})
        if usedBlueMl > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (change, type, description)
                                              VALUES (:ml, :type, 'bottling potions')
                                           """), {'ml': -1 * usedBlueMl, 'type': '[0, 0, 1, 0]'})
        if usedDarkMl > 0:
            connection.execute(sqlalchemy.text("""INSERT INTO ml_ledger (change, type, description)
                                              VALUES (:ml, :type, 'bottling potions')
                                           """), {'ml': -1 * usedDarkMl, 'type': '[0, 0, 0, 1]'})
            
        connection.execute(sqlalchemy.text("""UPDATE global_inventory 
                                           SET num_red_ml = num_red_ml - :usedRedMl,
                                            num_green_ml = num_green_ml - :usedGreenMl,
                                            num_blue_ml = num_blue_ml - :usedBlueMl,
                                            num_dark_ml = num_dark_ml - :usedDarkMl
                                           """), {'usedRedMl': usedRedMl, 'usedGreenMl': usedGreenMl, 'usedBlueMl': usedBlueMl, 'usedDarkMl': usedDarkMl})


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
        #currentRedMl, currentGreenMl, currentBlueMl, currentDarkMl, capacity = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, potion_capacity FROM global_inventory")).fetchone()
        currentRedMl, currentGreenMl, currentBlueMl, currentDarkMl = connection.execute(sqlalchemy.text(""" SELECT 
                                                    SUM(CASE WHEN type = '[1, 0, 0, 0]' THEN change ELSE 0 END),
                                                    SUM(CASE WHEN type = '[0, 1, 0, 0]' THEN change ELSE 0 END),
                                                    SUM(CASE WHEN type = '[0, 0, 1, 0]' THEN change ELSE 0 END),
                                                    SUM(CASE WHEN type = '[0, 0, 0, 1]' THEN change ELSE 0 END)
                                                    FROM ml_ledger
                                                    """)).fetchone()
        capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity FROM global_inventory")).fetchone()[0]
        total_potions = connection.execute(sqlalchemy.text("SELECT SUM(quantity) FROM potions")).fetchone()[0]
        plan = []
        
        lowStock = connection.execute(sqlalchemy.text("SELECT type FROM potions ORDER BY quantity ASC, price DESC")).fetchall()
        print(lowStock)
        for i in range(len(lowStock)):
            lowStock[i] = lowStock[i][0][1:-1].split(", ")
            lowStock[i] = [int(x) for x in lowStock[i]]
        
        for type in lowStock:
            quantity = 1
            while currentRedMl >= type[0] * quantity and currentGreenMl >= type[1] * quantity and currentBlueMl >= type[2] * quantity and currentDarkMl >= type[3] * quantity:
                quantity += 1
            quantity -= 1

            if total_potions + quantity > capacity:
                quantity = capacity - total_potions
            total_potions += quantity

            if quantity > 0:
                plan.append({"potion_type": type, "quantity": quantity})

                currentRedMl -= type[0] * quantity
                currentGreenMl -= type[1] * quantity
                currentBlueMl -= type[2] * quantity
                currentDarkMl -= type[3] * quantity

        return plan

if __name__ == "__main__":
    print(get_bottle_plan())
