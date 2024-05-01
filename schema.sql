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
    price INT4,
    max_quantity INT4
);

CREATE TABLE cart_items (
    cart_id INT4 REFERENCES carts(id),
    potion_id INT4 REFERENCES potions(id),
    quantity INT4,
    price INT4,
    PRIMARY KEY (cart_id, potion_id)
);

CREATE TABLE processed (
    id SERIAL PRIMARY KEY,
    job_id INT4,
    type TEXT
);

CREATE TABLE gold_ledger (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change INT4,
    description TEXT
);

CREATE TABLE ml_ledger (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT
    change INT4,
    description TEXT
);

CREATE TABLE potion_ledger (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    potion_id INT4 REFERENCES potions(id),
    change INT4,
    description TEXT
);

CREATE TABLE capacity_ledger (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT
    change INT4,
    description TEXT
);
    
INSERT INTO gold_ledger (change, description) 
VALUES (100, 'initial gold');

INSERT INTO capacity_ledger (change, type, description) 
VALUES (50, 'potion', 'initial capacity');

INSERT INTO capacity_ledger (change, type, description) 
VALUES (10000, 'ml', 'initial capacity');

INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('RED_POTION_0', 'red potion', '[100, 0, 0, 0]', 15, 40);

INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('GREEN_POTION_0', 'green potion', '[0, 100, 0, 0]', 15, 40);
    
INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('BLUE_POTION_0', 'blue potion', '[0, 0, 100, 0]', 15, 40);
    
INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('DARK_POTION_0', 'dark potion', '[0, 0, 0, 100]', 20, 40);

INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('PURPLE_POTION_0', 'purple potion', '[50, 0, 50, 0]', 10, 45);

INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('YELLOW_POTION_0', 'yellow potion', '[50, 50, 0, 0]', 10, 50);

INSERT INTO potions (sku, name, type, max_quantity, price) 
VALUES ('WHITE_POTION_0', 'white potion', '[34, 33, 33, 0]', 10, 60);
