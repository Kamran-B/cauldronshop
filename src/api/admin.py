import sqlalchemy
from src import database as db
import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("DELETE FROM potion_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM gold_ledger"))
        connection.execute(sqlalchemy.text("DELETE FROM ml_ledger"))
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (change, description)
                                              VALUES (100, 'initial gold')
                                           """))
        connection.execute(sqlalchemy.text("DELETE FROM capacity_ledger"))
        connection.execute(sqlalchemy.text("""INSERT INTO capacity_ledger (change, type, description)
                                              VALUES (50, 'potion', 'initial potion capacity')
                                           """))
        connection.execute(sqlalchemy.text("""INSERT INTO capacity_ledger (change, type, description)
                                              VALUES (10000, 'ml', 'initial ml capacity')
                                           """))

    return "OK"

