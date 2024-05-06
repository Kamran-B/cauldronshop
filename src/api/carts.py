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

    with db.engine.begin() as connection:
        stmt = (
            sqlalchemy.select(
                db.cart_items.c.cart_id,
                db.cart_items.c.potion_id,
                db.cart_items.c.quantity,
                db.cart_items.c.price,
                db.carts.c.id,
                db.carts.c.customer_id,
                db.customers.c.name,
                db.potions.c.name,
                db.carts.c.timestamp,
                db.potions.c.sku,
            )
            .limit(5)
            #.order_by(sort_col, db.movies.c.movie_id)
            .select_from(
                db.cart_items
                .join(db.carts, db.cart_items.c.cart_id == db.carts.c.id)
                .join(db.customers, db.carts.c.customer_id == db.customers.c.id)
                .join(db.potions, db.cart_items.c.potion_id == db.potions.c.id)
            )
        )

        if customer_name != "":
            stmt = stmt.where(db.customers.c.name == customer_name)

        if potion_sku != "":
            stmt = stmt.where(db.potions.c.sku == potion_sku)

        purchases = connection.execute(stmt).fetchall()
        print(purchases)

    results = []
    for item in purchases:
        results.append({
            "line_item_id": item[1],
            "item_sku": f"{str(item[2])} {item[7]}",
            "customer_name": item[6],
            "line_item_total": item[2] * item[3],
            "timestamp": item[8],
        })

    return {
        "previous": "",
        "next": "",
        "results": results,
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
        potion = connection.execute(sqlalchemy.text("SELECT id, price FROM potions WHERE sku = :sku"), {'sku': item_sku}).fetchone()
        connection.execute(sqlalchemy.text("""INSERT INTO cart_items (cart_id, potion_id, quantity, price)
                                            VALUES (:cartId, :potionId, :quantity, :price)
                                           """), {'cartId': cart_id, 'potionId': potion[0], 'quantity': cart_item.quantity, 'price': potion[1]})
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        items = connection.execute(sqlalchemy.text("SELECT potion_id, quantity, price FROM cart_items WHERE cart_id = :cart"), {'cart': cart_id}).fetchall()
        potions_bought = 0
        cost = 0
        for potion in items:
            potion_id = potion[0]
            quantity = potion[1]
            potions_bought += quantity
            cost += potion[2] * quantity
            
            connection.execute(sqlalchemy.text("""INSERT INTO potion_ledger (change, potion_id, description)
                                              VALUES (:quantity, :id, 'selling potions')
                                           """), {'quantity': -1 * quantity, 'id': potion_id})
        
        connection.execute(sqlalchemy.text("""INSERT INTO gold_ledger (change, description)
                                              VALUES (:cost, 'selling potions')
                                           """), {'cost': cost})

    return {"total_potions_bought": potions_bought, "total_gold_paid": cost}
