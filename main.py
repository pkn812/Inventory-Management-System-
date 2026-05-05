import mysql.connector as mycon
from login import Login
from menu import Menu
from db_setup import create_advanced_objects
from db_security import setup_security

class Main:
    """Represents the main application window for the inventory management system."""
    def __init__(self) :
        self.con = mycon.connect(host='localhost', user='root', passwd='Pkn2006@')# replace with you repective user and password of mysql

        if self.con.is_connected:
            print('* Connected to MySQL server')
            self.cur = self.con.cursor()
        else:
            print('[!]  Not connected to MySQL')

        db_query = "CREATE DATABASE IF NOT EXISTS inventory"
        self.cur.execute(db_query)


        self.con.database = 'inventory'
        self.cur.execute("CREATE TABLE if not exists users (username varchar (20) PRIMARY KEY, password varchar (64) NOT NULL, account_type varchar (10) NOT NULL);")
        # Widen password column for SHA-256 hashes if it was created with old schema
        try:
            self.cur.execute("ALTER TABLE users MODIFY COLUMN password VARCHAR(64) NOT NULL;")
        except Exception:
            pass
        self.cur.execute(
            "CREATE TABLE if not exists products ("
            "product_id varchar (20) PRIMARY KEY, "
            "product_name varchar (50) NOT NULL, "
            "description varchar (255) NOT NULL, "
            "barcode varchar(64) UNIQUE, "
            "price DECIMAL(15, 2) NOT NULL, "
            "quantity INTEGER NOT NULL"
            ");"
        )
        try:
            self.cur.execute("ALTER TABLE products MODIFY COLUMN price DECIMAL(15, 2) NOT NULL;")
        except Exception:
            pass
        self.cur.execute("SHOW COLUMNS FROM products LIKE 'barcode';")
        if not self.cur.fetchall():
            self.cur.execute("ALTER TABLE products ADD COLUMN barcode varchar(64) UNIQUE AFTER description;")
        self.cur.execute("CREATE TABLE if not exists orders (order_id INTEGER PRIMARY KEY, customer varchar (20), date DATE, total_items INTEGER, total_amount DECIMAL(15, 2), payment_status varchar(20));")
        self.cur.execute("CREATE TABLE if not exists order_items (order_item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id varchar (20), quantity INTEGER NOT NULL, price DECIMAL(15, 2) NOT NULL);")
        try:
            self.cur.execute("ALTER TABLE orders MODIFY COLUMN total_amount DECIMAL(15, 2);")
            self.cur.execute("ALTER TABLE order_items MODIFY COLUMN price DECIMAL(15, 2) NOT NULL;")
        except Exception:
            pass

        # Supply Chain Tables
        self.cur.execute("CREATE TABLE IF NOT EXISTS suppliers (supplier_id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL, contact_person VARCHAR(50), phone VARCHAR(20), email VARCHAR(50), address VARCHAR(200));")
        self.cur.execute("CREATE TABLE IF NOT EXISTS warehouses (warehouse_id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(50) NOT NULL, location VARCHAR(100), capacity INTEGER);")
        self.cur.execute("CREATE TABLE IF NOT EXISTS warehouse_stock (warehouse_id INTEGER, product_id VARCHAR(20), quantity INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (warehouse_id, product_id));")
        self.cur.execute("CREATE TABLE IF NOT EXISTS purchase_orders (po_id INTEGER PRIMARY KEY AUTO_INCREMENT, supplier_id INTEGER, date DATE, received_date DATE, status VARCHAR(20), total_amount DECIMAL(15, 2));")
        try:
            self.cur.execute("ALTER TABLE purchase_orders ADD COLUMN received_date DATE AFTER date;")
        except Exception:
            pass
        self.cur.execute("CREATE TABLE IF NOT EXISTS po_items (po_item_id INTEGER PRIMARY KEY AUTO_INCREMENT, po_id INTEGER, product_id VARCHAR(20), quantity INTEGER NOT NULL, price DECIMAL(15, 2));")
        try:
            self.cur.execute("ALTER TABLE purchase_orders MODIFY COLUMN total_amount DECIMAL(15, 2);")
            self.cur.execute("ALTER TABLE po_items MODIFY COLUMN price DECIMAL(15, 2);")
        except Exception:
            pass

        # Migrate existing stock to a default warehouse
        self.cur.execute("SELECT COUNT(*) FROM warehouses;")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute("INSERT INTO warehouses (name, location, capacity) VALUES ('Main Warehouse', 'HQ', 10000);")
            
        self.cur.execute("SELECT warehouse_id FROM warehouses ORDER BY warehouse_id ASC LIMIT 1;")
        default_wh_row = self.cur.fetchone()
        if default_wh_row:
            default_wh_id = default_wh_row[0]
            # Insert any missing products into warehouse_stock with their current total quantity
            self.cur.execute(f"INSERT IGNORE INTO warehouse_stock (warehouse_id, product_id, quantity) SELECT {default_wh_id}, product_id, quantity FROM products;")

        # Create advanced database objects (indexes, views, SPs, UDFs, triggers)
        create_advanced_objects(self.cur)
        self.con.commit()

        # Setup security (roles, password hashing, audit tables)
        setup_security(self.cur, self.con)
        self.con.commit()

        self.login = Login(self.con)
        self.login.window.mainloop()
        if self.login.user:
            self.menu = Menu(self.con, self.login.user, self.login.window)
            self.menu.window.mainloop()

            if self.menu.logout == True:
                Main()

        
if __name__ == "__main__":
    m = Main()
