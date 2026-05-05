-- ============================================================
-- PROJECT 07: INVENTORY MANAGEMENT SYSTEM
-- schema.sql  —  Database Schema
-- DATCOM Lab, NEU College of Technology
-- ============================================================

CREATE DATABASE IF NOT EXISTS inventory
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE inventory;

-- -------------------------------------------------------
-- Drop tables in reverse FK order so re-runs are clean
-- -------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS data_access_log;
DROP TABLE IF EXISTS login_audit;
DROP TABLE IF EXISTS inventory_log;
DROP TABLE IF EXISTS po_items;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS warehouse_stock;
DROP TABLE IF EXISTS warehouses;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------
-- TABLE: suppliers
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id    INT          AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    contact_person VARCHAR(50),
    phone          VARCHAR(20),
    email          VARCHAR(50),
    address        VARCHAR(200)
);

-- -------------------------------------------------------
-- TABLE: products
-- NOTE: product_id is VARCHAR to support custom IDs (e.g. '1'..'10').
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id   VARCHAR(20)   PRIMARY KEY,
    product_name VARCHAR(50)   NOT NULL,
    description  VARCHAR(255)  NOT NULL,
    barcode      VARCHAR(64)   UNIQUE,
    price        DECIMAL(15,2) NOT NULL CHECK (price >= 0),
    quantity     INT           NOT NULL DEFAULT 0 CHECK (quantity >= 0)
);

-- -------------------------------------------------------
-- TABLE: warehouses
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id INT         AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(50) NOT NULL,
    location     VARCHAR(100),
    capacity     INT         DEFAULT 0 CHECK (capacity >= 0)
);

-- -------------------------------------------------------
-- TABLE: warehouse_stock  (per-warehouse stock levels)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse_stock (
    warehouse_id INT         NOT NULL,
    product_id   VARCHAR(20) NOT NULL,
    quantity     INT         NOT NULL DEFAULT 0,
    PRIMARY KEY (warehouse_id, product_id),
    CONSTRAINT fk_ws_warehouse
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ws_product
        FOREIGN KEY (product_id)   REFERENCES products(product_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- TABLE: orders
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id       INT           PRIMARY KEY,
    customer       VARCHAR(20),
    date           DATE,
    total_items    INT,
    total_amount   DECIMAL(15,2),
    payment_status VARCHAR(20)
);

-- -------------------------------------------------------
-- TABLE: order_items
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT           PRIMARY KEY,
    order_id      INT,
    product_id    VARCHAR(20),
    quantity      INT           NOT NULL,
    price         DECIMAL(15,2) NOT NULL,
    CONSTRAINT fk_oi_order
        FOREIGN KEY (order_id)   REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oi_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- TABLE: purchase_orders  (replaces StockEntries from v1)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id         INT           AUTO_INCREMENT PRIMARY KEY,
    supplier_id   INT,
    date          DATE,
    received_date DATE,
    status        VARCHAR(20),
    total_amount  DECIMAL(15,2),
    CONSTRAINT fk_po_supplier
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- TABLE: po_items
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS po_items (
    po_item_id INT           AUTO_INCREMENT PRIMARY KEY,
    po_id      INT,
    product_id VARCHAR(20),
    quantity   INT           NOT NULL,
    price      DECIMAL(15,2),
    CONSTRAINT fk_poi_po
        FOREIGN KEY (po_id)      REFERENCES purchase_orders(po_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_poi_product
        FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- TABLE: users
-- NOTE: Password hashing (SHA-256 + salt) is handled by
--       db_security.py in the Python application layer.
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    username     VARCHAR(20) PRIMARY KEY,
    password     VARCHAR(64) NOT NULL,
    account_type VARCHAR(10) NOT NULL,
    salt         VARCHAR(64) DEFAULT NULL
);

-- -------------------------------------------------------
-- TABLE: inventory_log  (unified audit + movement log)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_log (
    log_id       INT          AUTO_INCREMENT PRIMARY KEY,
    product_id   VARCHAR(20),
    warehouse_id INT,
    change_type  VARCHAR(30)  NOT NULL,
    qty_change   INT          DEFAULT 0,
    old_qty      INT          DEFAULT 0,
    new_qty      INT          DEFAULT 0,
    notes        VARCHAR(255),
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- TABLE: login_audit
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS login_audit (
    audit_id   INT         AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(20),
    login_time TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) DEFAULT 'localhost',
    success    BOOLEAN     NOT NULL,
    notes      VARCHAR(255)
);

-- -------------------------------------------------------
-- TABLE: data_access_log
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_access_log (
    log_id      INT         AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(20),
    action      VARCHAR(50),
    table_name  VARCHAR(50),
    record_id   VARCHAR(50),
    access_time TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_product_name     ON products(product_name);
CREATE INDEX idx_order_date       ON orders(date);
CREATE INDEX idx_order_customer   ON orders(customer);
CREATE INDEX idx_order_status     ON orders(payment_status);
CREATE INDEX idx_oi_order_id      ON order_items(order_id);
CREATE INDEX idx_oi_product_id    ON order_items(product_id);
CREATE INDEX idx_log_product      ON inventory_log(product_id);
CREATE INDEX idx_log_warehouse    ON inventory_log(warehouse_id);
CREATE INDEX idx_log_created      ON inventory_log(created_at);
CREATE INDEX idx_log_type         ON inventory_log(change_type);
CREATE INDEX idx_login_username   ON login_audit(username);
CREATE INDEX idx_po_supplier      ON purchase_orders(supplier_id);
CREATE INDEX idx_po_status        ON purchase_orders(status);

-- ============================================================
-- VIEWS
-- ============================================================

-- View 1: Stock summary with status labels
CREATE OR REPLACE VIEW vw_stock_summary AS
SELECT
    p.product_id,
    p.product_name,
    p.description,
    p.barcode,
    p.price,
    p.quantity,
    CASE
        WHEN p.quantity = 0  THEN 'OUT OF STOCK'
        WHEN p.quantity < 10 THEN 'LOW STOCK'
        ELSE 'IN STOCK'
    END AS stock_status
FROM products p;

-- View 2: Stock levels per warehouse (with names)
CREATE OR REPLACE VIEW vw_warehouse_stock AS
SELECT
    ws.warehouse_id,
    w.name   AS warehouse_name,
    ws.product_id,
    p.product_name,
    ws.quantity
FROM warehouse_stock ws
JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
JOIN products   p ON ws.product_id   = p.product_id;

-- View 3: Low-stock alert  (quantity < 10)
CREATE OR REPLACE VIEW vw_low_stock_alert AS
SELECT
    p.product_id,
    p.product_name,
    p.quantity,
    p.price,
    CASE
        WHEN p.quantity = 0 THEN 'OUT OF STOCK'
        ELSE 'LOW STOCK'
    END AS stock_status
FROM products p
WHERE p.quantity < 10
ORDER BY p.quantity ASC;

-- View 4: Total stock value per warehouse
CREATE OR REPLACE VIEW vw_stock_value_per_warehouse AS
SELECT
    ws.warehouse_id,
    w.name AS warehouse_name,
    ROUND(SUM(ws.quantity * p.price), 2) AS total_stock_value
FROM warehouse_stock ws
JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
JOIN products   p ON ws.product_id   = p.product_id
GROUP BY ws.warehouse_id, w.name;

-- View 5: Supplier delivery history (via purchase_orders)
CREATE OR REPLACE VIEW vw_supplier_delivery_history AS
SELECT
    po.po_id,
    po.date          AS order_date,
    po.received_date,
    s.supplier_id,
    s.name           AS supplier_name,
    poi.product_id,
    p.product_name,
    poi.quantity,
    poi.price        AS unit_cost,
    ROUND(poi.quantity * poi.price, 2) AS total_cost,
    po.status
FROM purchase_orders po
JOIN suppliers  s   ON po.supplier_id = s.supplier_id
JOIN po_items   poi ON po.po_id       = poi.po_id
JOIN products   p   ON poi.product_id = p.product_id
ORDER BY po.date DESC;

-- View 6: Full transaction / audit log (with names)
CREATE OR REPLACE VIEW vw_transaction_log AS
SELECT
    il.log_id,
    il.created_at  AS transaction_date,
    il.change_type,
    p.product_name,
    w.name         AS warehouse_name,
    il.qty_change,
    il.old_qty,
    il.new_qty,
    il.notes
FROM inventory_log il
LEFT JOIN products   p ON il.product_id   = p.product_id
LEFT JOIN warehouses w ON il.warehouse_id = w.warehouse_id
ORDER BY il.created_at DESC;

-- View 7: Monthly earnings for the current year
CREATE OR REPLACE VIEW vw_monthly_earnings AS
SELECT
    MONTH(o.date)                          AS month_num,
    MONTHNAME(o.date)                      AS month_name,
    COUNT(DISTINCT o.order_id)             AS total_orders,
    SUM(oi.quantity)                       AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.price), 2)  AS total_earnings
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE YEAR(o.date) = YEAR(CURDATE())
GROUP BY MONTH(o.date), MONTHNAME(o.date)
ORDER BY MONTH(o.date);

-- View 8: Detailed order history with product names
CREATE OR REPLACE VIEW vw_order_history AS
SELECT
    o.order_id,
    o.customer,
    o.date,
    p.product_name,
    oi.quantity,
    oi.price                          AS unit_price,
    ROUND(oi.quantity * oi.price, 2)  AS line_total,
    o.payment_status
FROM orders      o
JOIN order_items oi ON o.order_id    = oi.order_id
JOIN products    p  ON oi.product_id = p.product_id
ORDER BY o.date DESC, o.order_id;

-- View 9: Product sales summary
CREATE OR REPLACE VIEW vw_product_sales AS
SELECT
    p.product_id,
    p.product_name,
    p.quantity                                          AS current_stock,
    COALESCE(SUM(oi.quantity), 0)                       AS total_units_sold,
    ROUND(COALESCE(SUM(oi.quantity * oi.price), 0), 2)  AS total_revenue,
    MAX(o.date)                                         AS last_sale_date
FROM products    p
LEFT JOIN order_items oi ON p.product_id  = oi.product_id
LEFT JOIN orders       o  ON oi.order_id  = o.order_id
GROUP BY p.product_id, p.product_name, p.quantity
ORDER BY total_units_sold DESC;

-- View 10: Purchase order details
CREATE OR REPLACE VIEW vw_po_details AS
SELECT
    po.po_id,
    po.date,
    po.received_date,
    s.name   AS supplier_name,
    po.status,
    po.total_amount
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id;

-- ============================================================
-- STORED PROCEDURES
-- ============================================================
DELIMITER $$

-- SP 1: Restock a product (add quantity + log the change)
CREATE PROCEDURE sp_restock_product(
    IN p_product_id VARCHAR(20),
    IN p_qty        INT
)
BEGIN
    DECLARE v_old_qty INT;
    SELECT quantity INTO v_old_qty FROM products WHERE product_id = p_product_id;
    UPDATE products SET quantity = quantity + p_qty WHERE product_id = p_product_id;
    INSERT INTO inventory_log (product_id, change_type, qty_change, old_qty, new_qty, notes)
    VALUES (p_product_id, 'RESTOCK', p_qty, v_old_qty, v_old_qty + p_qty,
            CONCAT('Restocked ', p_qty, ' units'));
END$$

-- SP 2: Dispatch / sell a product (with negative-stock guard)
CREATE PROCEDURE sp_dispatch_product(
    IN p_product_id   VARCHAR(20),
    IN p_qty          INT,
    IN p_warehouse_id INT
)
BEGIN
    DECLARE v_old_qty INT;
    SELECT quantity INTO v_old_qty FROM products WHERE product_id = p_product_id;
    IF v_old_qty < p_qty THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient stock: OUT quantity exceeds current balance.';
    END IF;
    UPDATE products SET quantity = quantity - p_qty WHERE product_id = p_product_id;
    INSERT INTO inventory_log
        (product_id, warehouse_id, change_type, qty_change, old_qty, new_qty, notes)
    VALUES (p_product_id, p_warehouse_id, 'DISPATCH', -p_qty, v_old_qty, v_old_qty - p_qty,
            CONCAT('Dispatched ', p_qty, ' units from warehouse ', p_warehouse_id));
END$$

-- SP 3: Get inventory balance for a specific product/warehouse pair
CREATE PROCEDURE sp_get_inventory_balance(
    IN p_product_id   VARCHAR(20),
    IN p_warehouse_id INT
)
BEGIN
    SELECT
        p.product_id,
        p.product_name,
        w.warehouse_id,
        w.name      AS warehouse_name,
        ws.quantity AS current_stock
    FROM warehouse_stock ws
    JOIN products   p ON ws.product_id   = p.product_id
    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
    WHERE ws.product_id = p_product_id AND ws.warehouse_id = p_warehouse_id;
END$$

-- SP 4: Full inventory snapshot report (all warehouses)
CREATE PROCEDURE sp_inventory_report()
BEGIN
    SELECT
        w.name                  AS warehouse_name,
        p.product_name,
        p.price,
        ws.quantity             AS current_stock,
        ROUND(ws.quantity * p.price, 2) AS stock_value,
        CASE
            WHEN ws.quantity = 0  THEN 'OUT OF STOCK'
            WHEN ws.quantity < 10 THEN 'LOW STOCK'
            ELSE 'IN STOCK'
        END AS stock_status
    FROM warehouse_stock ws
    JOIN products   p ON ws.product_id   = p.product_id
    JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
    ORDER BY w.name, p.product_name;
END$$

-- SP 5: Low-stock report (products below a given threshold)
CREATE PROCEDURE sp_low_stock_report(
    IN p_threshold INT
)
BEGIN
    SELECT
        product_id,
        product_name,
        quantity,
        price,
        CASE
            WHEN quantity = 0          THEN 'OUT OF STOCK'
            WHEN quantity < p_threshold THEN 'LOW STOCK'
            ELSE 'IN STOCK'
        END AS stock_status
    FROM products
    WHERE quantity < p_threshold
    ORDER BY quantity ASC;
END$$

-- SP 6: Receive a purchase order into a warehouse
CREATE PROCEDURE sp_receive_po(
    IN p_po_id        INT,
    IN p_warehouse_id INT
)
BEGIN
    DECLARE done          INT DEFAULT FALSE;
    DECLARE v_product_id  VARCHAR(20);
    DECLARE v_qty         INT;
    DECLARE v_old_qty     INT;

    DECLARE cur1 CURSOR FOR
        SELECT product_id, quantity FROM po_items WHERE po_id = p_po_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN cur1;
    read_loop: LOOP
        FETCH cur1 INTO v_product_id, v_qty;
        IF done THEN LEAVE read_loop; END IF;

        SELECT quantity INTO v_old_qty FROM products WHERE product_id = v_product_id;

        INSERT INTO warehouse_stock (warehouse_id, product_id, quantity)
        VALUES (p_warehouse_id, v_product_id, v_qty)
        ON DUPLICATE KEY UPDATE quantity = quantity + v_qty;

        UPDATE products SET quantity = quantity + v_qty WHERE product_id = v_product_id;

        INSERT INTO inventory_log
            (product_id, warehouse_id, change_type, qty_change, old_qty, new_qty, notes)
        VALUES (v_product_id, p_warehouse_id, 'PO_RECEIVED', v_qty, v_old_qty, v_old_qty + v_qty,
                CONCAT('Received PO #', p_po_id));
    END LOOP;
    CLOSE cur1;

    UPDATE purchase_orders
    SET status = 'RECEIVED', received_date = CURDATE()
    WHERE po_id = p_po_id;
END$$

DELIMITER ;

-- ============================================================
-- USER DEFINED FUNCTIONS
-- ============================================================
DELIMITER $$

-- UDF 1: Stock turnover rate  (units sold / avg inventory, last 90 days)
CREATE FUNCTION fn_stock_turnover_rate(p_product_id VARCHAR(20))
RETURNS DECIMAL(10,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_sold    INT;
    DECLARE v_current INT;

    SELECT COALESCE(SUM(oi.quantity), 0) INTO v_sold
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE oi.product_id = p_product_id
      AND o.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY);

    SELECT quantity INTO v_current FROM products WHERE product_id = p_product_id;

    IF v_current + v_sold = 0 THEN RETURN 0; END IF;
    RETURN ROUND(v_sold / ((v_current + v_sold + v_current) / 2), 2);
END$$

-- UDF 2: Average daily sales volume (last 90 days)
CREATE FUNCTION fn_avg_daily_sales(p_product_id VARCHAR(20))
RETURNS DECIMAL(10,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_sold INT;
    DECLARE v_days INT;

    SELECT COALESCE(SUM(oi.quantity), 0),
           GREATEST(DATEDIFF(CURDATE(), MIN(o.date)), 1)
    INTO v_sold, v_days
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    WHERE oi.product_id = p_product_id
      AND o.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY);

    RETURN ROUND(v_sold / v_days, 2);
END$$

-- UDF 3: Estimated days until stockout based on avg daily sales
CREATE FUNCTION fn_days_until_stockout(p_product_id VARCHAR(20))
RETURNS INT
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_qty       INT;
    DECLARE v_avg_sales DECIMAL(10,2);

    SELECT quantity INTO v_qty FROM products WHERE product_id = p_product_id;
    SET v_avg_sales = fn_avg_daily_sales(p_product_id);
    IF v_avg_sales <= 0 THEN RETURN 9999; END IF;
    RETURN FLOOR(v_qty / v_avg_sales);
END$$

-- UDF 4: Average delivery time for a supplier (days: PO date → received_date)
CREATE FUNCTION fn_avg_delivery_time(p_supplier_id INT)
RETURNS DECIMAL(10,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_avg DECIMAL(10,2);
    SELECT COALESCE(AVG(DATEDIFF(received_date, date)), 0) INTO v_avg
    FROM purchase_orders
    WHERE supplier_id    = p_supplier_id
      AND status         = 'RECEIVED'
      AND received_date IS NOT NULL;
    RETURN v_avg;
END$$

-- UDF 5: Total stock value for a single warehouse
CREATE FUNCTION fn_warehouse_stock_value(p_warehouse_id INT)
RETURNS DECIMAL(18,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total DECIMAL(18,2) DEFAULT 0;
    SELECT COALESCE(SUM(ws.quantity * p.price), 0) INTO v_total
    FROM warehouse_stock ws
    JOIN products p ON ws.product_id = p.product_id
    WHERE ws.warehouse_id = p_warehouse_id;
    RETURN v_total;
END$$

DELIMITER ;

-- ============================================================
-- TRIGGERS
-- ============================================================
DELIMITER $$

-- Trigger 1: Log quantity changes on the products table
CREATE TRIGGER trg_product_stock_update
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    IF OLD.quantity <> NEW.quantity THEN
        INSERT INTO inventory_log
            (product_id, change_type, qty_change, old_qty, new_qty, notes)
        VALUES (
            NEW.product_id,
            CASE WHEN NEW.quantity > OLD.quantity THEN 'STOCK_ADDED' ELSE 'STOCK_REMOVED' END,
            NEW.quantity - OLD.quantity,
            OLD.quantity,
            NEW.quantity,
            CASE WHEN NEW.quantity > OLD.quantity
                THEN CONCAT('Added ',   NEW.quantity - OLD.quantity, ' units')
                ELSE CONCAT('Removed ', OLD.quantity - NEW.quantity, ' units')
            END
        );
    END IF;
END$$

-- Trigger 2: Prevent product quantity from going below zero
CREATE TRIGGER trg_before_stock_update
BEFORE UPDATE ON products
FOR EACH ROW
BEGIN
    IF NEW.quantity < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Insufficient stock: quantity cannot go below zero.';
    END IF;
END$$

-- Trigger 3: Log new orders placed
CREATE TRIGGER trg_order_placed
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO inventory_log
        (product_id, change_type, qty_change, old_qty, new_qty, notes)
    VALUES (NULL, 'ORDER_PLACED', 0, 0, 0,
            CONCAT('Order #', NEW.order_id, ' placed by ', NEW.customer,
                   ' | Status: ', NEW.payment_status,
                   ' | Total: ', NEW.total_amount));
END$$

-- Trigger 4: Log payment status changes on orders
CREATE TRIGGER trg_order_status_change
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
    IF OLD.payment_status <> NEW.payment_status THEN
        INSERT INTO inventory_log
            (product_id, change_type, qty_change, old_qty, new_qty, notes)
        VALUES (NULL, 'PAYMENT_STATUS_CHANGE', 0, 0, 0,
                CONCAT('Order #', NEW.order_id, ' status: ',
                       OLD.payment_status, ' -> ', NEW.payment_status));
    END IF;
END$$

-- Trigger 5: Audit log when a supplier is deleted
CREATE TRIGGER trg_after_supplier_delete
AFTER DELETE ON suppliers
FOR EACH ROW
BEGIN
    INSERT INTO inventory_log
        (product_id, change_type, qty_change, old_qty, new_qty, notes)
    VALUES (NULL, 'SUPPLIER_DELETED', 0, 0, 0,
            CONCAT('Supplier #', OLD.supplier_id, ' (', OLD.name, ') deleted'));
END$$

-- Trigger 6: Audit log when a product is deleted
CREATE TRIGGER trg_after_product_delete
AFTER DELETE ON products
FOR EACH ROW
BEGIN
    INSERT INTO inventory_log
        (product_id, change_type, qty_change, old_qty, new_qty, notes)
    VALUES (OLD.product_id, 'PRODUCT_DELETED', 0, OLD.quantity, 0,
            CONCAT('Product ', OLD.product_name, ' deleted'));
END$$

-- Trigger 7: Audit log when a warehouse is deleted
CREATE TRIGGER trg_after_warehouse_delete
AFTER DELETE ON warehouses
FOR EACH ROW
BEGIN
    INSERT INTO inventory_log
        (product_id, change_type, qty_change, old_qty, new_qty, notes)
    VALUES (NULL, 'WAREHOUSE_DELETED', 0, 0, 0,
            CONCAT('Warehouse #', OLD.warehouse_id, ' (', OLD.name, ') deleted'));
END$$

DELIMITER ;

-- ============================================================
-- USER ROLES AND SECURITY
-- ============================================================
CREATE USER IF NOT EXISTS 'inv_admin'@'localhost'    IDENTIFIED BY 'Admin@Inv2024!';
CREATE USER IF NOT EXISTS 'inv_manager'@'localhost'  IDENTIFIED BY 'Mgr@Inv2024!';
CREATE USER IF NOT EXISTS 'inv_reporter'@'localhost' IDENTIFIED BY 'Rep@Inv2024!';

-- Admin: full access
GRANT ALL PRIVILEGES ON inventory.* TO 'inv_admin'@'localhost';

-- Manager: read/write on operational tables + execute key procedures
GRANT SELECT, INSERT, UPDATE ON inventory.products        TO 'inv_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON inventory.orders          TO 'inv_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON inventory.order_items     TO 'inv_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON inventory.warehouse_stock TO 'inv_manager'@'localhost';
GRANT SELECT, INSERT         ON inventory.inventory_log   TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory.suppliers       TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory.warehouses      TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory.users           TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory.purchase_orders TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory.po_items        TO 'inv_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE inventory.sp_restock_product      TO 'inv_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE inventory.sp_dispatch_product     TO 'inv_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE inventory.sp_get_inventory_balance TO 'inv_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE inventory.sp_low_stock_report     TO 'inv_manager'@'localhost';
GRANT EXECUTE ON FUNCTION  inventory.fn_avg_daily_sales      TO 'inv_manager'@'localhost';
GRANT EXECUTE ON FUNCTION  inventory.fn_days_until_stockout  TO 'inv_manager'@'localhost';
GRANT EXECUTE ON FUNCTION  inventory.fn_stock_turnover_rate  TO 'inv_manager'@'localhost';

-- Reporter: read-only on all tables and views
GRANT SELECT ON inventory.* TO 'inv_reporter'@'localhost';

FLUSH PRIVILEGES;

-- ============================================================
-- END OF SCHEMA
-- ============================================================