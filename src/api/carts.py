import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    with db.engine.begin() as connection:
        # TODO: INSERT ON CONFLICT
        customerId = connection.execute(sqlalchemy.text("""SELECT id FROM customers
                                                        WHERE name = :name
                                                        AND character_class = :class
                                                        AND level = :level
                                                        """), {'name': new_cart.customer_name, 'class': new_cart.character_class, 'level': new_cart.level}).fetchone()
        print(customerId)
        if customerId is None:
            connection.execute(sqlalchemy.text("""INSERT INTO customers (name, character_class, level)
                                            VALUES (:name, :class, :level) ON CONFLICT DO NOTHING
                                            """), {'name': new_cart.customer_name, 'class': new_cart.character_class, 'level': new_cart.level})
        
        customerId = connection.execute(sqlalchemy.text("""SELECT id FROM customers
                                                        WHERE name = :name
                                                        AND character_class = :class
                                                        AND level = :level
                                                        """), {'name': new_cart.customer_name, 'class': new_cart.character_class, 'level': new_cart.level}).fetchone()[0]
        
        cartId = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:id) RETURNING id"), {'id': customerId}).fetchone()[0]

    return {"cart_id": cartId}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        potionId = connection.execute(sqlalchemy.text("SELECT id FROM potions WHERE sku = :sku"), {'sku': item_sku}).fetchone()[0]
        connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, potion_id, quantity)
                                            VALUES (:cartId, :potionId, :quantity)
                                           """), {'cartId': cart_id, 'potionId': potionId, 'quantity': cart_item.quantity})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        items = connection.execute(sqlalchemy.text("SELECT * FROM cart_items WHERE cart_id = :cart"), {'cart': cart_id}).fetchall()
        potions_bought = 0
        cost = 0
        for potion in items:
            potion_id = potion[1]
            quantity = potion[2]
            potions_bought += quantity
            cost += connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE id = :potion_id"), {'potion_id': potion_id}).fetchone()[0] * quantity
            connection.execute(sqlalchemy.text("""UPDATE potions 
                                               SET quantity = quantity - :quantity
                                               WHERE id = :potion_id
                                               """), {'quantity': quantity, 'potion_id': potion_id})
        
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + :payment"), {'payment': cost})

    return {"total_potions_bought": potions_bought, "total_gold_paid": cost}
