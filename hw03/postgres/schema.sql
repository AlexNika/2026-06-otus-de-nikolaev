CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    title      TEXT NOT NULL,
    price      NUMERIC(10,2) NOT NULL CHECK (price >= 0)
);

CREATE TABLE orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- Star A --

CREATE TABLE order_items (
    order_id   INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    qty        INT NOT NULL CHECK (qty > 0),
    PRIMARY KEY (order_id, product_id)
);

-- Star A ----------------------------------------------

-- Star C --

CREATE TABLE big_orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT now()
);

-- Star C ----------------------------------------------