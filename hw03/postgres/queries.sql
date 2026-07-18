INSERT INTO customers (name, email) VALUES
    ('Иван Петров', 'ivan@example.com'),
    ('Мария Сидорова', 'maria@example.com'),
    ('Пётр Кузнецов', 'petr@example.com');

INSERT INTO products (title, price) VALUES
    ('Ноутбук', 89999.00),
    ('Мышь', 1499.00),
    ('Монитор', 24999.00);

INSERT INTO orders (customer_id) VALUES (1), (1), (2), (3);

SELECT p.title, p.price
FROM products p
WHERE p.price > 2000 ORDER BY p.price DESC;

SELECT *
FROM orders
WHERE customer_id = 1 ORDER BY created_at;

SELECT c.name, c.email, o.order_id, o.created_at
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
ORDER BY c.name;

-- Star A --

INSERT INTO order_items (order_id, product_id, qty) VALUES
    (1, 1, 2), (1, 2, 1), (2, 3, 1);

SELECT o.order_id, c.name, SUM(p.price * oi.qty) AS total
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p ON p.product_id = oi.product_id
GROUP BY o.order_id, c.name
ORDER BY o.order_id;

-- Star A ----------------------------------------------

-- Star C --

INSERT INTO big_orders (customer_id)
SELECT (random() * 10000)::int
FROM generate_series(1, 100000);

EXPLAIN SELECT * FROM big_orders WHERE customer_id = 42;

CREATE INDEX idx_big_orders_customer_id ON big_orders (customer_id);

EXPLAIN SELECT * FROM big_orders WHERE customer_id = 42;

-- Star C ----------------------------------------------