"""
db_setup.py  –  Advanced MySQL Database Objects
================================================
Creates indexes, views, stored procedures, user-defined functions,
triggers, and an audit (inventory_log) table for the Inventory
Management System.

Called once on application startup from main.py.
"""


def create_advanced_objects(cur):
    """Create all advanced database objects.  Idempotent – safe to call
    on every startup."""

    _create_audit_table(cur)
    _create_indexes(cur)
    _create_views(cur)
    _create_stored_procedures(cur)
    _create_functions(cur)
    _create_triggers(cur)
    print("[*] Advanced database objects created successfully")


# ───────────────────────────── Audit Table ─────────────────────────────

def _create_audit_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory_log (
            log_id       INT AUTO_INCREMENT PRIMARY KEY,
            product_id   VARCHAR(20),
            warehouse_id INT,
            change_type  VARCHAR(30)   NOT NULL,
            qty_change   INT           DEFAULT 0,
            old_qty      INT           DEFAULT 0,
            new_qty      INT           DEFAULT 0,
            notes        VARCHAR(255),
            created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Ensure warehouse_id exists if the table was already created
    try:
        cur.execute("ALTER TABLE inventory_log ADD COLUMN warehouse_id INT AFTER product_id;")
    except Exception:
        pass


# ───────────────────────────── Indexes ─────────────────────────────────

_INDEXES = [
    ("idx_product_name",   "products",    "product_name"),
    ("idx_order_date",     "orders",      "date"),
    ("idx_order_customer", "orders",      "customer"),
    ("idx_order_status",   "orders",      "payment_status"),
    ("idx_oi_order_id",    "order_items", "order_id"),
    ("idx_oi_product_id",  "order_items", "product_id"),
]


def _create_indexes(cur):
    for idx_name, table, column in _INDEXES:
        try:
            cur.execute(
                f"CREATE INDEX {idx_name} ON {table}({column});"
            )
        except Exception:
            # Index already exists – that's fine
            pass


# ───────────────────────────── Views ───────────────────────────────────

def _create_views(cur):
    # View 1: Stock summary with status
    cur.execute("DROP VIEW IF EXISTS vw_stock_summary;")
    cur.execute("""
        CREATE VIEW vw_stock_summary AS
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
    """)

    # View 2: Monthly earnings for current year
    cur.execute("DROP VIEW IF EXISTS vw_monthly_earnings;")
    cur.execute("""
        CREATE VIEW vw_monthly_earnings AS
        SELECT
            MONTH(o.date)                            AS month_num,
            MONTHNAME(o.date)                        AS month_name,
            COUNT(DISTINCT o.order_id)               AS total_orders,
            SUM(oi.quantity)                          AS total_units_sold,
            ROUND(SUM(oi.quantity * oi.price), 2)    AS total_earnings
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE YEAR(o.date) = YEAR(CURDATE())
        GROUP BY MONTH(o.date), MONTHNAME(o.date)
        ORDER BY MONTH(o.date);
    """)

    # View 3: Detailed order history with product names
    cur.execute("DROP VIEW IF EXISTS vw_order_history;")
    cur.execute("""
        CREATE VIEW vw_order_history AS
        SELECT
            o.order_id,
            o.customer,
            o.date,
            p.product_name,
            oi.quantity,
            oi.price            AS unit_price,
            ROUND(oi.quantity * oi.price, 2) AS line_total,
            o.payment_status
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p     ON oi.product_id = p.product_id
        ORDER BY o.date DESC, o.order_id;
    """)

    # View 4: Product sales summary
    cur.execute("DROP VIEW IF EXISTS vw_product_sales;")
    cur.execute("""
        CREATE VIEW vw_product_sales AS
        SELECT
            p.product_id,
            p.product_name,
            p.quantity                                AS current_stock,
            COALESCE(SUM(oi.quantity), 0)             AS total_units_sold,
            ROUND(COALESCE(SUM(oi.quantity * oi.price), 0), 2) AS total_revenue,
            MAX(o.date)                               AS last_sale_date
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        LEFT JOIN orders o       ON oi.order_id  = o.order_id
        GROUP BY p.product_id, p.product_name, p.quantity
        ORDER BY total_units_sold DESC;
    """)

    # View 5: Warehouse Stock
    cur.execute("DROP VIEW IF EXISTS vw_warehouse_stock;")
    cur.execute("""
        CREATE VIEW vw_warehouse_stock AS
        SELECT
            ws.warehouse_id,
            w.name AS warehouse_name,
            ws.product_id,
            p.product_name,
            ws.quantity
        FROM warehouse_stock ws
        JOIN warehouses w ON ws.warehouse_id = w.warehouse_id
        JOIN products p ON ws.product_id = p.product_id;
    """)

    # View 6: PO Details
    cur.execute("DROP VIEW IF EXISTS vw_po_details;")
    cur.execute("""
        CREATE VIEW vw_po_details AS
        SELECT
            po.po_id,
            po.date,
            s.name AS supplier_name,
            po.status,
            po.total_amount
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id;
    """)


# ───────────────────────── Stored Procedures ───────────────────────────

def _create_stored_procedures(cur):
    # SP 1: Restock a product
    cur.execute("DROP PROCEDURE IF EXISTS sp_restock_product;")
    cur.execute("""
        CREATE PROCEDURE sp_restock_product(
            IN p_product_id VARCHAR(20),
            IN p_qty        INT
        )
        BEGIN
            DECLARE v_old_qty INT;

            SELECT quantity INTO v_old_qty
            FROM products
            WHERE product_id = p_product_id;

            UPDATE products
            SET quantity = quantity + p_qty
            WHERE product_id = p_product_id;

            INSERT INTO inventory_log
                (product_id, change_type, qty_change, old_qty, new_qty, notes)
            VALUES
                (p_product_id, 'RESTOCK', p_qty, v_old_qty, v_old_qty + p_qty,
                 CONCAT('Restocked ', p_qty, ' units'));
        END
    """)

    # SP 2: Low stock report
    cur.execute("DROP PROCEDURE IF EXISTS sp_low_stock_report;")
    cur.execute("""
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
                    WHEN quantity = 0  THEN 'OUT OF STOCK'
                    WHEN quantity < p_threshold THEN 'LOW STOCK'
                    ELSE 'IN STOCK'
                END AS stock_status
            FROM products
            WHERE quantity < p_threshold
            ORDER BY quantity ASC;
        END
    """)

    # SP 3: Calculate total inventory value
    cur.execute("DROP PROCEDURE IF EXISTS sp_calculate_inventory_value;")
    cur.execute("""
        CREATE PROCEDURE sp_calculate_inventory_value()
        BEGIN
            SELECT
                COUNT(*)                              AS total_products,
                SUM(quantity)                         AS total_units,
                ROUND(SUM(quantity * price), 2)       AS total_value
            FROM products;
        END
    """)

    # SP 4: Place order atomically
    cur.execute("DROP PROCEDURE IF EXISTS sp_place_order;")
    cur.execute("""
        CREATE PROCEDURE sp_place_order(
            IN p_customer       VARCHAR(20),
            IN p_product_id     VARCHAR(20),
            IN p_qty            INT,
            IN p_payment_status VARCHAR(20)
        )
        BEGIN
            DECLARE v_order_id      INT;
            DECLARE v_order_item_id INT;
            DECLARE v_price         DECIMAL(10,2);
            DECLARE v_available     INT;

            -- Check availability
            SELECT quantity, price INTO v_available, v_price
            FROM products
            WHERE product_id = p_product_id;

            IF v_available < p_qty THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Insufficient stock for this product';
            END IF;

            -- Generate order ID
            SELECT COALESCE(MAX(order_id), 1000) + 1 INTO v_order_id FROM orders;
            SELECT COALESCE(MAX(order_item_id), 0) + 1 INTO v_order_item_id FROM order_items;

            -- Insert order
            INSERT INTO orders (order_id, customer, date, total_items, total_amount, payment_status)
            VALUES (v_order_id, p_customer, CURDATE(), 1, ROUND(v_price * p_qty, 2), p_payment_status);

            -- Insert order item
            INSERT INTO order_items (order_item_id, order_id, product_id, quantity, price)
            VALUES (v_order_item_id, v_order_id, p_product_id, p_qty, ROUND(v_price * p_qty, 2));

            -- Decrement stock
            UPDATE products
            SET quantity = quantity - p_qty
            WHERE product_id = p_product_id;
        END
    """)

    # SP 5: Receive PO
    cur.execute("DROP PROCEDURE IF EXISTS sp_receive_po;")
    cur.execute("""
        CREATE PROCEDURE sp_receive_po(
            IN p_po_id INT,
            IN p_warehouse_id INT
        )
        BEGIN
            DECLARE done INT DEFAULT FALSE;
            DECLARE v_product_id VARCHAR(20);
            DECLARE v_qty INT;
            DECLARE v_old_wh_qty INT;
            DECLARE v_old_prod_qty INT;
            
            DECLARE cur1 CURSOR FOR SELECT product_id, quantity FROM po_items WHERE po_id = p_po_id;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            OPEN cur1;

            read_loop: LOOP
                FETCH cur1 INTO v_product_id, v_qty;
                IF done THEN
                    LEAVE read_loop;
                END IF;

                -- Update or Insert warehouse stock
                SELECT quantity INTO v_old_wh_qty FROM warehouse_stock WHERE warehouse_id = p_warehouse_id AND product_id = v_product_id;
                IF v_old_wh_qty IS NULL THEN
                    SET v_old_wh_qty = 0;
                    INSERT INTO warehouse_stock (warehouse_id, product_id, quantity) VALUES (p_warehouse_id, v_product_id, v_qty);
                ELSE
                    UPDATE warehouse_stock SET quantity = quantity + v_qty WHERE warehouse_id = p_warehouse_id AND product_id = v_product_id;
                END IF;

                -- Update total product stock
                SELECT quantity INTO v_old_prod_qty FROM products WHERE product_id = v_product_id;
                UPDATE products SET quantity = quantity + v_qty WHERE product_id = v_product_id;

                -- Log transaction
                INSERT INTO inventory_log
                    (product_id, warehouse_id, change_type, qty_change, old_qty, new_qty, notes)
                VALUES
                    (v_product_id, p_warehouse_id, 'PO_RECEIVED', v_qty, v_old_prod_qty, v_old_prod_qty + v_qty,
                     CONCAT('Received PO #', p_po_id));
            END LOOP;

            CLOSE cur1;
            
            UPDATE purchase_orders SET status = 'RECEIVED', received_date = CURDATE() WHERE po_id = p_po_id;
        END
    """)


# ────────────────────── User Defined Functions ─────────────────────────

def _create_functions(cur):
    # UDF 1: Stock turnover rate (units sold / avg inventory) over last 90 days
    cur.execute("DROP FUNCTION IF EXISTS fn_stock_turnover_rate;")
    cur.execute("""
        CREATE FUNCTION fn_stock_turnover_rate(p_product_id VARCHAR(20))
        RETURNS DECIMAL(10,2)
        DETERMINISTIC
        BEGIN
            DECLARE v_sold      INT;
            DECLARE v_current   INT;
            DECLARE v_turnover  DECIMAL(10,2);

            SELECT COALESCE(SUM(oi.quantity), 0) INTO v_sold
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE oi.product_id = p_product_id
              AND o.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY);

            SELECT quantity INTO v_current
            FROM products
            WHERE product_id = p_product_id;

            IF v_current + v_sold = 0 THEN
                SET v_turnover = 0;
            ELSE
                SET v_turnover = ROUND(v_sold / ((v_current + v_sold + v_current) / 2), 2);
            END IF;

            RETURN v_turnover;
        END
    """)

    # UDF 2: Average daily sales (last 90 days)
    cur.execute("DROP FUNCTION IF EXISTS fn_avg_daily_sales;")
    cur.execute("""
        CREATE FUNCTION fn_avg_daily_sales(p_product_id VARCHAR(20))
        RETURNS DECIMAL(10,2)
        DETERMINISTIC
        BEGIN
            DECLARE v_sold  INT;
            DECLARE v_days  INT;

            SELECT COALESCE(SUM(oi.quantity), 0),
                   GREATEST(DATEDIFF(CURDATE(), MIN(o.date)), 1)
            INTO v_sold, v_days
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE oi.product_id = p_product_id
              AND o.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY);

            RETURN ROUND(v_sold / v_days, 2);
        END
    """)

    # UDF 3: Days until stockout
    cur.execute("DROP FUNCTION IF EXISTS fn_days_until_stockout;")
    cur.execute("""
        CREATE FUNCTION fn_days_until_stockout(p_product_id VARCHAR(20))
        RETURNS INT
        DETERMINISTIC
        BEGIN
            DECLARE v_qty       INT;
            DECLARE v_avg_sales DECIMAL(10,2);

            SELECT quantity INTO v_qty
            FROM products
            WHERE product_id = p_product_id;

            SET v_avg_sales = fn_avg_daily_sales(p_product_id);

            IF v_avg_sales <= 0 THEN
                RETURN 9999;
            END IF;

            RETURN FLOOR(v_qty / v_avg_sales);
        END
    """)

    # UDF 4: Average delivery time for a supplier (in days)
    cur.execute("DROP FUNCTION IF EXISTS fn_avg_delivery_time;")
    cur.execute("""
        CREATE FUNCTION fn_avg_delivery_time(p_supplier_id INT)
        RETURNS DECIMAL(10,2)
        DETERMINISTIC
        BEGIN
            DECLARE v_avg DECIMAL(10,2);
            
            SELECT COALESCE(AVG(DATEDIFF(received_date, date)), 0) INTO v_avg
            FROM purchase_orders
            WHERE supplier_id = p_supplier_id AND status = 'RECEIVED' AND received_date IS NOT NULL;
            
            RETURN v_avg;
        END
    """)


# ─────────────────────────── Triggers ──────────────────────────────────

def _create_triggers(cur):
    # Trigger 1: Log inventory changes when product quantity is updated
    cur.execute("DROP TRIGGER IF EXISTS trg_product_stock_update;")
    cur.execute("""
        CREATE TRIGGER trg_product_stock_update
        AFTER UPDATE ON products
        FOR EACH ROW
        BEGIN
            IF OLD.quantity <> NEW.quantity THEN
                INSERT INTO inventory_log
                    (product_id, change_type, qty_change, old_qty, new_qty, notes)
                VALUES (
                    NEW.product_id,
                    CASE
                        WHEN NEW.quantity > OLD.quantity THEN 'STOCK_ADDED'
                        ELSE 'STOCK_REMOVED'
                    END,
                    NEW.quantity - OLD.quantity,
                    OLD.quantity,
                    NEW.quantity,
                    CASE
                        WHEN NEW.quantity > OLD.quantity
                            THEN CONCAT('Added ', NEW.quantity - OLD.quantity, ' units')
                        ELSE CONCAT('Removed ', OLD.quantity - NEW.quantity, ' units')
                    END
                );
            END IF;
        END
    """)

    # Trigger 2: Log when a new order is placed
    cur.execute("DROP TRIGGER IF EXISTS trg_order_placed;")
    cur.execute("""
        CREATE TRIGGER trg_order_placed
        AFTER INSERT ON orders
        FOR EACH ROW
        BEGIN
            INSERT INTO inventory_log
                (product_id, change_type, qty_change, old_qty, new_qty, notes)
            VALUES (
                NULL,
                'ORDER_PLACED',
                0, 0, 0,
                CONCAT('Order #', NEW.order_id, ' placed by ', NEW.customer,
                       ' | Status: ', NEW.payment_status,
                       ' | Total: $', NEW.total_amount)
            );
        END
    """)

    # Trigger 3: Log payment status changes
    cur.execute("DROP TRIGGER IF EXISTS trg_order_status_change;")
    cur.execute("""
        CREATE TRIGGER trg_order_status_change
        AFTER UPDATE ON orders
        FOR EACH ROW
        BEGIN
            IF OLD.payment_status <> NEW.payment_status THEN
                INSERT INTO inventory_log
                    (product_id, change_type, qty_change, old_qty, new_qty, notes)
                VALUES (
                    NULL,
                    'PAYMENT_STATUS_CHANGE',
                    0, 0, 0,
                    CONCAT('Order #', NEW.order_id, ' status: ',
                           OLD.payment_status, ' -> ', NEW.payment_status)
                );
            END IF;
        END
    """)
