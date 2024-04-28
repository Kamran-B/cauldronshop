CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT,
    character_class TEXT,
    level INT4
);

CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    customer_id INT4 REFERENCES customers(id)
);

CREATE TABLE potions (
    id SERIAL PRIMARY KEY,
    sku TEXT,
    name TEXT,
    quantity INT4,
    price INT4
);

CREATE TABLE cart_items (
    cart_id INT4 REFERENCES carts(id),
    potion_id INT4 REFERENCES potions(id),
    quantity INT4,
    PRIMARY KEY (cart_id, potion_id)
);

CREATE TABLE global_inventory (
    id SERIAL PRIMARY KEY,
    gold INT4,
    num_red_ml INT4,
    num_green_ml INT4,
    num_blue_ml INT4,
    num_dark_ml INT4,
    potion_capacity INT4,
    ml_capacity INT4
);

CREATE TABLE processed (
    id SERIAL PRIMARY KEY,
    job_id INT4,
    type TEXT
);

INSERT INTO global_inventory (gold, num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, potion_capacity, ml_capacity) 
VALUES (100, 0, 0, 0, 0, 50, 10000)
