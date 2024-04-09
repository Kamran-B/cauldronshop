import sqlalchemy
from src import database as db
from fastapi import APIRouter

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        row = connection.execute(sqlalchemy.text("SELECT * FROM global_inventory")).fetchone()
    
    print(row)

    if row[0] == 0:
        return []

    return [
            {
                "sku": "GREEN_POTION_0",
                "name": "green potion",
                "quantity": 1, #row[0],
                "price": 50,
                "potion_type": [0, 1, 0, 0],
            }
        ]
