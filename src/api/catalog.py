import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        stock = connection.execute(sqlalchemy.text("""SELECT potions.sku, potions.name, SUM(potion_ledger.change) AS quantity, potions.price, potions.type
                                                      FROM potion_ledger
                                                      JOIN potions ON potions.id = potion_ledger.potion_id
                                                      GROUP BY potions.sku, potions.name, potions.price, potions.type;
                                                   """)).fetchall()
        
        print("Current inventory:", stock)

        for potion in stock:

            if potion[2] > 0:
                catalog.append({
                "sku": potion[0],
                "name": potion[1],
                "quantity": potion[2],
                "price": potion[3],
                "potion_type": potion[4][1:-1].split(", "),
                })
            
            if len(catalog) >= 6:
                break
                
    return catalog
