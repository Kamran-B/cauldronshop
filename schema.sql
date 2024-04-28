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
    type TEXT,
    quantity INT4,
    price INT4
);

CREATE TABLE cart_items (
    cart_id INT4 REFERENCES carts(id),
    potion_id INT4 REFERENCES potions(id),
    quantity INT4,
    price INT4,
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
VALUES (100, 0, 0, 0, 0, 50, 10000);

    
INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('RED_POTION_0', 'red potion', '[100, 0, 0, 0]', 0, 40);

INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('GREEN_POTION_0', 'green potion', '[0, 100, 0, 0]', 0, 40);
    
INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('BLUE_POTION_0', 'blue potion', '[0, 0, 100, 0]', 0, 40);
    
INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('DARK_POTION_0', 'dark potion', '[0, 0, 0, 100]', 0, 40);

INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('PURPLE_POTION_0', 'purple potion', '[50, 0, 50, 0]', 0, 45);

INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('YELLOW_POTION_0', 'yellow potion', '[50, 50, 0, 0]', 0, 50);

INSERT INTO potions (sku, name, type, quantity, price) 
VALUES ('WHITE_POTION_0', 'white potion', '[34, 33, 33, 0]', 0, 60);
