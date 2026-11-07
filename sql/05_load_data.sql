
USE ecommerce_customer_intelligence;

-- IMPORTANT:
-- Run this script only after creating the database schema.
-- All destination tables must be empty.
-- Files must exist in the MySQL secure_file_priv Uploads directory.

-- 1. CUSTOMERS

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_customers_dataset.csv'
INTO TABLE customers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @customer_id,
    @customer_unique_id,
    @zip_code,
    @city,
    @state
)
SET
    customer_id = TRIM(@customer_id),
    customer_unique_id = TRIM(@customer_unique_id),
    customer_zip_code_prefix = TRIM(@zip_code),
    customer_city = TRIM(@city),
    customer_state = TRIM(@state);


-- 2. PRODUCTS

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_products_dataset.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @product_id,
    @category,
    @name_length,
    @description_length,
    @photos_qty,
    @weight_g,
    @length_cm,
    @height_cm,
    @width_cm
)
SET
    product_id = TRIM(@product_id),
    product_category_name = NULLIF(TRIM(@category), ''),
    product_name_lenght = NULLIF(TRIM(@name_length), ''),
    product_description_lenght = NULLIF(TRIM(@description_length), ''),
    product_photos_qty = NULLIF(TRIM(@photos_qty), ''),
    product_weight_g = NULLIF(TRIM(@weight_g), ''),
    product_length_cm = NULLIF(TRIM(@length_cm), ''),
    product_height_cm = NULLIF(TRIM(@height_cm), ''),
    product_width_cm = NULLIF(TRIM(@width_cm), '');


-- 3. SELLERS

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_sellers_dataset.csv'
INTO TABLE sellers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @seller_id,
    @zip_code,
    @city,
    @state
)
SET
    seller_id = TRIM(@seller_id),
    seller_zip_code_prefix = TRIM(@zip_code),
    seller_city = TRIM(@city),
    seller_state = TRIM(@state);


-- 4. ORDERS

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_orders_dataset.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @order_id,
    @customer_id,
    @order_status,
    @purchase_timestamp,
    @approved_at,
    @carrier_date,
    @delivered_date,
    @estimated_date
)
SET
    order_id = TRIM(@order_id),
    customer_id = TRIM(@customer_id),
    order_status = TRIM(@order_status),
    order_purchase_timestamp =
        STR_TO_DATE(NULLIF(TRIM(@purchase_timestamp), ''), '%Y-%m-%d %H:%i:%s'),
    order_approved_at =
        STR_TO_DATE(NULLIF(TRIM(@approved_at), ''), '%Y-%m-%d %H:%i:%s'),
    order_delivered_carrier_date =
        STR_TO_DATE(NULLIF(TRIM(@carrier_date), ''), '%Y-%m-%d %H:%i:%s'),
    order_delivered_customer_date =
        STR_TO_DATE(NULLIF(TRIM(@delivered_date), ''), '%Y-%m-%d %H:%i:%s'),
    order_estimated_delivery_date =
        STR_TO_DATE(NULLIF(TRIM(@estimated_date), ''), '%Y-%m-%d %H:%i:%s');


-- 5. CATEGORY TRANSLATION

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/product_category_name_translation.csv'
INTO TABLE category_translation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @category_name,
    @english_name
)
SET
    product_category_name = TRIM(@category_name),
    product_category_name_english = TRIM(@english_name);


-- 6. GEOLOCATION

-- Coordinate precision: DECIMAL(23,20)

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_geolocation_dataset.csv'
INTO TABLE geolocation
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @zip_code,
    @latitude,
    @longitude,
    @city,
    @state
)
SET
    geolocation_zip_code_prefix = TRIM(@zip_code),
    geolocation_lat = NULLIF(TRIM(@latitude), ''),
    geolocation_lng = NULLIF(TRIM(@longitude), ''),
    geolocation_city = TRIM(@city),
    geolocation_state = TRIM(@state);


-- 7. ORDER ITEMS

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_order_items_dataset.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @order_id,
    @order_item_id,
    @product_id,
    @seller_id,
    @shipping_limit_date,
    @price,
    @freight_value
)
SET
    order_id = TRIM(@order_id),
    order_item_id = CAST(TRIM(@order_item_id) AS UNSIGNED),
    product_id = TRIM(@product_id),
    seller_id = TRIM(@seller_id),
    shipping_limit_date =
        STR_TO_DATE(NULLIF(TRIM(@shipping_limit_date), ''), '%Y-%m-%d %H:%i:%s'),
    price = NULLIF(TRIM(@price), ''),
    freight_value = NULLIF(TRIM(@freight_value), '');


-- 8. PAYMENTS

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_order_payments_dataset.csv'
INTO TABLE payments
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @order_id,
    @payment_sequential,
    @payment_type,
    @payment_installments,
    @payment_value
)
SET
    order_id = TRIM(@order_id),
    payment_sequential =
        CAST(NULLIF(TRIM(@payment_sequential), '') AS UNSIGNED),
    payment_type = TRIM(@payment_type),
    payment_installments =
        CAST(NULLIF(TRIM(@payment_installments), '') AS UNSIGNED),
    payment_value = NULLIF(TRIM(@payment_value), '');


-- 9. REVIEWS

-- Handles Windows CRLF line endings and multiline quoted comments.
-- Whitespace-only comments are normalized to NULL.

LOAD DATA INFILE
'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/olist_order_reviews_dataset.csv'
INTO TABLE reviews
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(
    @review_id,
    @order_id,
    @review_score,
    @comment_title,
    @comment_message,
    @creation_date,
    @answer_timestamp
)
SET
    review_id = TRIM(@review_id),
    order_id = TRIM(@order_id),
    review_score =
        CAST(NULLIF(TRIM(@review_score), '') AS UNSIGNED),
    review_comment_title =
        NULLIF(TRIM(@comment_title), ''),
    review_comment_message =
        CASE
            WHEN TRIM(
                REPLACE(
                    REPLACE(
                        REPLACE(COALESCE(@comment_message, ''), CHAR(13), ''),
                        CHAR(10), ''
                    ),
                    CHAR(9), ''
                )
            ) = ''
            THEN NULL
            ELSE TRIM(@comment_message)
        END,
    review_creation_date =
        STR_TO_DATE(NULLIF(TRIM(@creation_date), ''), '%Y-%m-%d %H:%i:%s'),
    review_answer_timestamp =
        STR_TO_DATE(NULLIF(TRIM(@answer_timestamp), ''), '%Y-%m-%d %H:%i:%s');


-- RECONCILE THE FIRST REVIEW RECORD
-- Insert only if the composite key is not already present.

INSERT INTO reviews (
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp
)
SELECT
    '7bc2406110b926393aa56f80a40eba40',
    '73fc7af87114b39712e6da79b0a377eb',
    4,
    NULL,
    NULL,
    '2018-01-18 00:00:00',
    '2018-01-18 21:46:59'
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM reviews
    WHERE review_id = '7bc2406110b926393aa56f80a40eba40'
      AND order_id = '73fc7af87114b39712e6da79b0a377eb'
);


-- FINAL ROW COUNT VALIDATION

SELECT 'customers' AS table_name, COUNT(*) AS total_rows FROM customers
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'sellers', COUNT(*) FROM sellers
UNION ALL
SELECT 'geolocation', COUNT(*) FROM geolocation
UNION ALL
SELECT 'category_translation', COUNT(*) FROM category_translation;
