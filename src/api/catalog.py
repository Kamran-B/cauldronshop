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
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions")).fetchall()
        print("Current inventory:", potions)

        for potion in potions:
            if potion[2] > 0:
                catalog.append({
                "sku": potion[1],
                "name": potion[4],
                "quantity": potion[2],
                "price": 50,
                "potion_type": potion[3][1:-1].split(", "),
                })
            
            if len(catalog) >= 6:
                break
                
    return catalog
