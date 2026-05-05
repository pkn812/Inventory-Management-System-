import mysql.connector
from db_setup import create_advanced_objects
from db_security import setup_security

def init_db():
    con = mysql.connector.connect(host='localhost', user='root', passwd='Pkn2006@')
    cur = con.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS inventory")
    con.database = 'inventory'

    cur.execute("CREATE TABLE if not exists users (username varchar (20) PRIMARY KEY, password varchar (64) NOT NULL, account_type varchar (10) NOT NULL);")
    try:
        cur.execute("ALTER TABLE users MODIFY COLUMN password VARCHAR(64) NOT NULL;")
    except Exception:
        pass
    cur.execute(
        "CREATE TABLE if not exists products ("
        "product_id varchar (20) PRIMARY KEY, "
        "product_name varchar (50) NOT NULL, "
        "description varchar (50) NOT NULL, "
        "barcode varchar(64) UNIQUE, "
        "price DECIMAL(10, 2) NOT NULL, "
        "quantity INTEGER NOT NULL"
        ");"
    )
    cur.execute("SHOW COLUMNS FROM products LIKE 'barcode';")
    if not cur.fetchall():
        cur.execute("ALTER TABLE products ADD COLUMN barcode varchar(64) UNIQUE AFTER description;")
    cur.execute("CREATE TABLE if not exists orders (order_id INTEGER PRIMARY KEY, customer varchar (20), date DATE, total_items INTEGER, total_amount DECIMAL(10, 2), payment_status varchar(20));")
    cur.execute("CREATE TABLE if not exists order_items (order_item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id varchar (20), quantity INTEGER NOT NULL, price DECIMAL(10, 2) NOT NULL);")

    # Supply Chain Tables
    cur.execute("CREATE TABLE IF NOT EXISTS suppliers (supplier_id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL, contact_person VARCHAR(50), phone VARCHAR(20), email VARCHAR(50), address VARCHAR(200));")
    cur.execute("CREATE TABLE IF NOT EXISTS warehouses (warehouse_id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(50) NOT NULL, location VARCHAR(100), capacity INTEGER);")
    cur.execute("CREATE TABLE IF NOT EXISTS warehouse_stock (warehouse_id INTEGER, product_id VARCHAR(20), quantity INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (warehouse_id, product_id));")
    cur.execute("CREATE TABLE IF NOT EXISTS purchase_orders (po_id INTEGER PRIMARY KEY AUTO_INCREMENT, supplier_id INTEGER, date DATE, received_date DATE, status VARCHAR(20), total_amount DECIMAL(10, 2));")
    try:
        cur.execute("ALTER TABLE purchase_orders ADD COLUMN received_date DATE AFTER date;")
    except Exception:
        pass
    cur.execute("CREATE TABLE IF NOT EXISTS po_items (po_item_id INTEGER PRIMARY KEY AUTO_INCREMENT, po_id INTEGER, product_id VARCHAR(20), quantity INTEGER NOT NULL, price DECIMAL(10, 2));")

    # Migrate existing stock to a default warehouse
    cur.execute("SELECT COUNT(*) FROM warehouses;")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO warehouses (name, location, capacity) VALUES ('Main Warehouse', 'HQ', 10000);")
        
    cur.execute("SELECT warehouse_id FROM warehouses ORDER BY warehouse_id ASC LIMIT 1;")
    default_wh_row = cur.fetchone()
    if default_wh_row:
        default_wh_id = default_wh_row[0]
        cur.execute(f"INSERT IGNORE INTO warehouse_stock (warehouse_id, product_id, quantity) SELECT {default_wh_id}, product_id, quantity FROM products;")

    # Create advanced database objects (indexes, views, SPs, UDFs, triggers)
    create_advanced_objects(cur)
    con.commit()

    # Setup security (roles, password hashing, audit tables)
    setup_security(cur, con)
    con.commit()

    print("DB initialized")

if __name__ == '__main__':
    init_db()
