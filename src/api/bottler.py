import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import json

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
            
            potion_id = connection.execute(sqlalchemy.text("""SELECT id FROM potions 
                                                            WHERE type = :type
                                                            """), {'type': json.dumps(potion.potion_type)}).fetchone()[0]
            
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (change, potion_id, description)
                                              VALUES (:quantity, :id, 'bottling potions')
                                           """), {'quantity': potion.quantity, 'id': potion_id})
            
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

    with db.engine.begin() as connection:
        currentRedMl, currentGreenMl, currentBlueMl, currentDarkMl = connection.execute(sqlalchemy.text(""" SELECT 
                                                    COALESCE(SUM(CASE WHEN type = '[1, 0, 0, 0]' THEN change ELSE 0 END), 0),
                                                    COALESCE(SUM(CASE WHEN type = '[0, 1, 0, 0]' THEN change ELSE 0 END), 0),
                                                    COALESCE(SUM(CASE WHEN type = '[0, 0, 1, 0]' THEN change ELSE 0 END), 0),
                                                    COALESCE(SUM(CASE WHEN type = '[0, 0, 0, 1]' THEN change ELSE 0 END), 0)
                                                    FROM ml_ledger
                                                    """)).fetchone()
        capacity = connection.execute(sqlalchemy.text("SELECT SUM(change) FROM capacity_ledger WHERE type = 'potion'")).fetchone()[0]
        total_potions = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger")).fetchone()[0]
        plan = []
        
        stock = connection.execute(sqlalchemy.text("""SELECT type, max_quantity, potion_id
                                                         FROM potions
                                                         LEFT JOIN potion_ledger ON potions.id = potion_ledger.potion_id
                                                         GROUP BY type, max_quantity, potion_id
                                                         ORDER BY COALESCE(SUM(potion_ledger.change), 0) ASC""")).fetchall()
        print("current stock:", stock)
        lowStock = [i for i in stock]
        for i in range(len(stock)):
            lowStock[i] = stock[i][0][1:-1].split(", ")
            lowStock[i] = [int(x) for x in lowStock[i]]
        
        i = 0
        for type in lowStock:
            maxForType = stock[i][1]
            numType = connection.execute(sqlalchemy.text("SELECT COALESCE(SUM(change), 0) FROM potion_ledger WHERE potion_id = :id"), {'id': stock[i][2]}).fetchone()[0]
            i += 1

            if numType >= maxForType:
                continue

            quantity = 1
            while currentRedMl >= type[0] * quantity and currentGreenMl >= type[1] * quantity and currentBlueMl >= type[2] * quantity and currentDarkMl >= type[3] * quantity:
                quantity += 1
            quantity -= 1

            if numType + quantity > maxForType:
                quantity = maxForType - numType

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
