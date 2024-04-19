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

    try:
        connection.execute(sqlalchemy.text("INSERT INTO processed (job_id, type) VALUES (:order_id, 'barrels')"), 
            [{"order_id": order_id}])
    except IntegrityError as e:
        return "OK"

    newGreenMl = 0
    newRedMl = 0
    newBlueMl = 0
    newDarkMl = 0
    cost = 0

    with db.engine.begin() as connection:
        print("gold tuple:", connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone())
        currentgold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).fetchone()[0]
        for barrel in barrels_delivered:
            cost += barrel.price * barrel.quantity
            if barrel.potion_type == [0, 1, 0, 0]:
                newGreenMl += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [1, 0, 0, 0]:
                newRedMl += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 1, 0]:
                newBlueMl += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 0, 1]:
                newDarkMl += barrel.ml_per_barrel * barrel.quantity
            else:
                raise Exception("Invalid potion type")
        
        connection.execute(sqlalchemy.text(
            """UPDATE global_inventory SET 
            num_green_ml = num_green_ml + :newGreen
            num_red_ml = num_red_ml + :newRed
            num_blue_ml = num_blue_ml + :newBlue
            num_dark_ml = num_dark_ml + :newDark
            gold = gold - :costval
            """), [{'newGreen': newGreenMl, 'newRed': newRedMl, 'newBlue': newBlueMl, 'newDark': newDarkMl, 'costval': cost}])

        #connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = num_green_ml + :new"), {'new': newGreenMl})
        #connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = num_green_ml + :new"), {'new': newRedMl})
        #connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = num_green_ml + :new"), {'new': newBlueMl})
        #connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold - :costval"), {'costval': cost})

        print(f"gold paid: {cost}, red: {newRedMl}, green: {newGreenMl}, blue: {newBlueMl}")

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
            print("barrel sku:", barrel.sku, "current potions:", currentpotions)
            if currentpotions < 10 and (barrel.potion_type in [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) and barrel.price <= currentgold:
                plan.append({"sku": barrel.sku, "quantity": 1})
                print("     buying barrel")
                break

    return plan

