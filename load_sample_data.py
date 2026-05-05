import mysql.connector

def load_data():
    try:
        con = mysql.connector.connect(host='localhost', user='root', passwd='Pkn2006@', database='inventory')
        cur = con.cursor()

        print("[*] Connected to database.")

        # Clear existing data safely
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cur.execute("TRUNCATE TABLE suppliers;")
        cur.execute("TRUNCATE TABLE warehouses;")
        cur.execute("TRUNCATE TABLE products;")
        cur.execute("TRUNCATE TABLE warehouse_stock;")
        cur.execute("TRUNCATE TABLE inventory_log;")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        # Widen description column for products
        cur.execute("ALTER TABLE products MODIFY COLUMN description VARCHAR(255);")
        
        print("[*] Truncated tables.")

        # Insert Suppliers
        suppliers = [
            ( 1, 'TechSource Vietnam',      None, '0901234567', 'contact@techsource.vn', '12 Tran Hung Dao, Hoan Kiem, Hanoi'),
            ( 2, 'Global Parts Ltd.',       None, '0912345678', 'info@globalparts.com', '45 Nguyen Trai, District 1, Ho Chi Minh City'),
            ( 3, 'Viet Supply Chain Co.',   None, '0923456789', 'sales@vietsupply.vn', '78 Le Loi, Hai Chau, Da Nang'),
            ( 4, 'Asia Electronics JSC',    None, '0934567890', 'asia@aelec.com', '10 Pham Ngoc Thach, Dong Da, Hanoi'),
            ( 5, 'ProGoods Vietnam',        None, '0945678901', 'order@progoods.vn', '22 Hai Ba Trung, District 3, HCM City'),
            ( 6, 'FastLog Distributors',    None, '0956789012', 'fast@fastlog.vn', '5 Bach Dang, Ngo Quyen, Hai Phong'),
            ( 7, 'Sunrise Materials Corp.', None, '0967890123', 'sun@sunrise.vn', '88 Ly Thuong Kiet, Hoan Kiem, Hanoi'),
            ( 8, 'Pacific Supplies Ltd.',   None, '0978901234', 'pac@pacific.vn', '33 Nguyen Hue, Hai Chau, Da Nang'),
            ( 9, 'Mekong Traders Co.',      None, '0989012345', 'trade@mekong.vn', '99 Vo Van Tan, Ninh Kieu, Can Tho'),
            (10, 'Northern Hub JSC',        None, '0990123456', 'north@nhub.vn', '14 Hang Bai, Hoan Kiem, Hanoi')
        ]
        cur.executemany("INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address) VALUES (%s, %s, %s, %s, %s, %s)", suppliers)

        # Insert Warehouses
        warehouses = [
            ( 1, 'Hanoi Central WH',    'Km12 Giai Phong St, Hoang Mai, Hanoi',         5000),
            ( 2, 'HCM South Hub',       'VSIP I Industrial Zone, Binh Duong',           8000),
            ( 3, 'Da Nang Port WH',     '10 Tien Sa, Son Tra, Da Nang',                 4000),
            ( 4, 'Can Tho Delta WH',    '22 Vo Thi Sau, Ninh Kieu, Can Tho',            3000),
            ( 5, 'Hai Phong Dock WH',   '5 Cat Bi Road, Ngo Quyen, Hai Phong',          4500),
            ( 6, 'Hanoi North WH',      '8 Xuan Thuy, Cau Giay, Hanoi',                 3500),
            ( 7, 'Binh Duong Hub',      'VSIP II Industrial Zone, Binh Duong',          7000),
            ( 8, 'Nha Trang Store',     '3 Tran Phu, Loc Tho, Nha Trang',               2500),
            ( 9, 'Hue Distribution WH', '45 Hung Vuong, Phu Nhuan, Hue City',           2000),
            (10, 'Vung Tau Depot',      '18 Le Hong Phong, Ward 4, Vung Tau',            3200)
        ]
        cur.executemany("INSERT INTO warehouses (warehouse_id, name, location, capacity) VALUES (%s, %s, %s, %s)", warehouses)

        # Insert Products
        products = [
            ('1', 'Laptop Dell XPS 15',       'Intel Core i7, 16GB RAM, 512GB SSD, 15.6" FHD',       None, 28500000, 120),
            ('2', 'USB-C Hub 7-Port',         '7-in-1: HDMI 4K, USB-A x3, SD/TF reader, PD 100W',      None, 550000, 80),
            ('3', 'Mechanical Keyboard TKL',  'TKL 87-key RGB, hot-swap switches, USB Type-C',          None, 890000, 200),
            ('4', '4K IPS Monitor 27"',       'UHD 3840x2160, IPS panel, 60Hz, HDMI 2.0 + DP 1.4',  None, 5800000, 45),
            ('5', 'Wireless Ergonomic Mouse', 'Silent 6-button ergonomic, 2.4 GHz + BT dual mode',     None, 320000, 350),
            ('6', 'HDMI 2.1 Cable 2m',        'Certified HDMI 2.1, 8K@60Hz / 4K@120Hz, braided',        None, 95000, 500),
            ('7', 'Portable SSD 1TB',         'USB 3.2 Gen2, read 1050 MB/s, rugged aluminium shell', None, 1200000, 90),
            ('8', 'Webcam 1080p Full HD',     'Full HD 30fps, built-in stereo mic, autofocus, USB-A',   None, 650000, 130),
            ('9', 'Gigabit Switch 8-Port',    'Unmanaged 8-port GbE, plug-and-play, metal case',        None, 450000, 60),
            ('10', 'Wireless Inkjet Printer',  'A4 colour inkjet, Wi-Fi Direct, duplex, 22 ppm',       None, 3200000, 35)
        ]
        cur.executemany("INSERT INTO products (product_id, product_name, description, barcode, price, quantity) VALUES (%s, %s, %s, %s, %s, %s)", products)

        # Insert Warehouse Stock (mapped based on where StockEntries initialized them)
        warehouse_stock = [
            (1, '1', 120),
            (2, '2', 80),
            (1, '3', 200),
            (3, '4', 45),
            (2, '5', 350),
            (4, '6', 500),
            (1, '7', 90),
            (2, '8', 130),
            (3, '9', 60),
            (1, '10', 35)
        ]
        cur.executemany("INSERT INTO warehouse_stock (warehouse_id, product_id, quantity) VALUES (%s, %s, %s)", warehouse_stock)

        con.commit()
        print("[*] Sample data successfully loaded!")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            cur.close()
            con.close()

if __name__ == "__main__":
    load_data()
