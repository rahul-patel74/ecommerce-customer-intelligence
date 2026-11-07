CREATE TABLE customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state CHAR(2)
);


CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    order_status VARCHAR(30),
    order_purchase_timestamp DATETIME,
    order_approved_at DATETIME,
    order_delivered_carrier_date DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME,

    CONSTRAINT fk_orders_customers
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT
);


CREATE TABLE sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(10),
    seller_city VARCHAR(100),
    seller_state CHAR(2)
);


CREATE TABLE order_items (
    order_id VARCHAR(32) NOT NULL,
    order_item_id INT NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    seller_id VARCHAR(32) NOT NULL,
    shipping_limit_date DATETIME,
    price DECIMAL(10,2),
    freight_value DECIMAL(10,2),

    PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT fk_items_orders
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_items_products
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT fk_items_sellers
        FOREIGN KEY (seller_id)
        REFERENCES sellers(seller_id)
);


CREATE TABLE payments (
    order_id VARCHAR(32) NOT NULL,
    payment_sequential INT NOT NULL,
    payment_type VARCHAR(30),
    payment_installments INT,
    payment_value DECIMAL(10,2),

    PRIMARY KEY (order_id, payment_sequential),

    CONSTRAINT fk_payments_orders
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
);


CREATE TABLE reviews (
    review_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    review_score INT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date DATETIME,
    review_answer_timestamp DATETIME,

    PRIMARY KEY (review_id, order_id),

    CONSTRAINT fk_reviews_orders
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT chk_review_score
        CHECK (review_score BETWEEN 1 AND 5)
);


CREATE TABLE category_translation (
    product_category_name VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100)
);


CREATE TABLE geolocation (
    geolocation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    geolocation_zip_code_prefix VARCHAR(10),
    geolocation_lat DECIMAL(23,20),
    geolocation_lng DECIMAL(23,20),
    geolocation_city VARCHAR(100),
    geolocation_state CHAR(2)
);


