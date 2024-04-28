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
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    """try:
        connection.execute(sqlalchemy.text("INSERT INTO processed (job_id, type) VALUES (:order_id, 'barrels')"), 
            [{"order_id": order_id}])
    except:
        return "OK" """

    newGreenMl = 0
    newRedMl = 0
    newBlueMl = 0
    newDarkMl = 0
    cost = 0

    with db.engine.begin() as connection:
        for barrel in barrels_delivered:
            cost += barrel.price * barrel.quantity
            if barrel.potion_type == [1, 0, 0, 0]:
                newRedMl += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 1, 0, 0]:
                newGreenMl += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 1, 0]:
                newBlueMl += barrel.ml_per_barrel * barrel.quantity
            elif barrel.potion_type == [0, 0, 0, 1]:
                newDarkMl += barrel.ml_per_barrel * barrel.quantity
            else:
                raise Exception("Invalid potion type")
        
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (change, description)
                                              VALUES (:cost, 'buying barrels')
                                           """), {'cost': -1 * cost})
        
        connection.execute(sqlalchemy.text("""UPDATE global_inventory 
                                           SET num_red_ml = num_red_ml + :newRed,
                                           num_green_ml = num_green_ml + :newGreen,
                                           num_blue_ml = num_blue_ml + :newBlue,
                                           num_dark_ml = num_dark_ml + :newDark,
                                           gold = gold - :cost
                                           """), {'newRed': newRedMl, 'newGreen': newGreenMl, 'newBlue': newBlueMl, 'newDark': newDarkMl, 'cost': cost})

        print(f"gold paid: {cost}, red: {newRedMl}, green: {newGreenMl}, blue: {newBlueMl}, dark: {newDarkMl}")

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print(wholesale_catalog)
    plan = []
    with db.engine.begin() as connection:
        currentgold, redStock, greenStock, blueStock, darkStock, capacity = connection.execute(sqlalchemy.text("SELECT gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, ml_capacity FROM global_inventory")).fetchone()
        currentgold = connection.execute(sqlalchemy.text("SELECT sum(change) FROM gold_ledger")).fetchone()[0]
        total_ml = redStock + greenStock + blueStock + darkStock
        colors = {"red": [1, 0, 0, 0], "green": [0, 1, 0, 0], "blue": [0, 0, 1, 0], "dark": [0, 0, 0, 1]}
        allStock = {"red": redStock, "green": greenStock, "blue": blueStock, "dark": darkStock}
        print("current stock:", allStock)
        allStock = dict(sorted(allStock.items(), key=lambda item: item[1]))
        print("sorted by lowest stock:", allStock)

        for color in allStock:
            type = colors[color]
            print(type, wholesale_catalog)
            colorBarrels = [bar for bar in wholesale_catalog if bar.potion_type == type]
            print(colorBarrels)
            bestIndex = None
            bestValue = 0
            for i in range (len(colorBarrels)):
                if colorBarrels[i].price <= currentgold and (colorBarrels[i].ml_per_barrel / colorBarrels[i].price) > bestValue:
                    bestIndex = i
                    bestValue = colorBarrels[i].ml_per_barrel / colorBarrels[i].price
            
            if bestIndex is not None:
                quantity = min((currentgold // colorBarrels[i].price) // 2, colorBarrels[i].quantity)
                if quantity == 0:
                    quantity = 1
                
                if total_ml + colorBarrels[i].ml_per_barrel * quantity > capacity:
                    quantity = (capacity - total_ml) // colorBarrels[i].ml_per_barrel
                    if quantity == 0:
                        continue
                total_ml += colorBarrels[i].ml_per_barrel * quantity

                plan.append({"sku": colorBarrels[bestIndex].sku, "quantity": quantity})
                print("buying barrel sku:", colorBarrels[bestIndex].sku, "quantity:", quantity, "current gold before purchase:", currentgold)
                currentgold -= colorBarrels[bestIndex].price * quantity

    return plan

