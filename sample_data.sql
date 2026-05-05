-- ============================================================
-- PROJECT 07: INVENTORY MANAGEMENT SYSTEM
-- sample_data.sql  —  10 records per table
-- ============================================================

USE inventory;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE data_access_log;
TRUNCATE TABLE login_audit;
TRUNCATE TABLE inventory_log;
TRUNCATE TABLE po_items;
TRUNCATE TABLE purchase_orders;
TRUNCATE TABLE order_items;
TRUNCATE TABLE orders;
TRUNCATE TABLE warehouse_stock;
TRUNCATE TABLE warehouses;
TRUNCATE TABLE products;
TRUNCATE TABLE suppliers;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 1. SUPPLIERS  (10 records)
-- ============================================================
INSERT INTO suppliers (supplier_id, name, contact_person, phone, email, address) VALUES
( 1, 'TechSource Vietnam',      NULL, '0901234567', 'contact@techsource.vn', '12 Tran Hung Dao, Hoan Kiem, Hanoi'),
( 2, 'Global Parts Ltd.',       NULL, '0912345678', 'info@globalparts.com',  '45 Nguyen Trai, District 1, Ho Chi Minh City'),
( 3, 'Viet Supply Chain Co.',   NULL, '0923456789', 'sales@vietsupply.vn',   '78 Le Loi, Hai Chau, Da Nang'),
( 4, 'Asia Electronics JSC',    NULL, '0934567890', 'asia@aelec.com',        '10 Pham Ngoc Thach, Dong Da, Hanoi'),
( 5, 'ProGoods Vietnam',        NULL, '0945678901', 'order@progoods.vn',     '22 Hai Ba Trung, District 3, HCM City'),
( 6, 'FastLog Distributors',    NULL, '0956789012', 'fast@fastlog.vn',       '5 Bach Dang, Ngo Quyen, Hai Phong'),
( 7, 'Sunrise Materials Corp.', NULL, '0967890123', 'sun@sunrise.vn',        '88 Ly Thuong Kiet, Hoan Kiem, Hanoi'),
( 8, 'Pacific Supplies Ltd.',   NULL, '0978901234', 'pac@pacific.vn',        '33 Nguyen Hue, Hai Chau, Da Nang'),
( 9, 'Mekong Traders Co.',      NULL, '0989012345', 'trade@mekong.vn',       '99 Vo Van Tan, Ninh Kieu, Can Tho'),
(10, 'Northern Hub JSC',        NULL, '0990123456', 'north@nhub.vn',         '14 Hang Bai, Hoan Kiem, Hanoi');

-- ============================================================
-- 2. WAREHOUSES  (10 records)
-- ============================================================
INSERT INTO warehouses (warehouse_id, name, location, capacity) VALUES
( 1, 'Hanoi Central WH',    'Km12 Giai Phong St, Hoang Mai, Hanoi',   5000),
( 2, 'HCM South Hub',       'VSIP I Industrial Zone, Binh Duong',     8000),
( 3, 'Da Nang Port WH',     '10 Tien Sa, Son Tra, Da Nang',           4000),
( 4, 'Can Tho Delta WH',    '22 Vo Thi Sau, Ninh Kieu, Can Tho',      3000),
( 5, 'Hai Phong Dock WH',   '5 Cat Bi Road, Ngo Quyen, Hai Phong',    4500),
( 6, 'Hanoi North WH',      '8 Xuan Thuy, Cau Giay, Hanoi',           3500),
( 7, 'Binh Duong Hub',      'VSIP II Industrial Zone, Binh Duong',    7000),
( 8, 'Nha Trang Store',     '3 Tran Phu, Loc Tho, Nha Trang',         2500),
( 9, 'Hue Distribution WH', '45 Hung Vuong, Phu Nhuan, Hue City',     2000),
(10, 'Vung Tau Depot',      '18 Le Hong Phong, Ward 4, Vung Tau',      3200);

-- ============================================================
-- 3. PRODUCTS  (10 records)
-- ============================================================
INSERT INTO products (product_id, product_name, description, barcode, price, quantity) VALUES
('1',  'Laptop Dell XPS 15',       'Intel Core i7, 16GB RAM, 512GB SSD, 15.6" FHD',        NULL, 28500000, 120),
('2',  'USB-C Hub 7-Port',         '7-in-1: HDMI 4K, USB-A x3, SD/TF reader, PD 100W',     NULL,   550000,  80),
('3',  'Mechanical Keyboard TKL',  'TKL 87-key RGB, hot-swap switches, USB Type-C',          NULL,   890000, 200),
('4',  '4K IPS Monitor 27"',       'UHD 3840x2160, IPS panel, 60Hz, HDMI 2.0 + DP 1.4',   NULL,  5800000,  45),
('5',  'Wireless Ergonomic Mouse', 'Silent 6-button ergonomic, 2.4 GHz + BT dual mode',     NULL,   320000, 350),
('6',  'HDMI 2.1 Cable 2m',        'Certified HDMI 2.1, 8K@60Hz / 4K@120Hz, braided',       NULL,    95000, 500),
('7',  'Portable SSD 1TB',         'USB 3.2 Gen2, read 1050 MB/s, rugged aluminium shell',  NULL,  1200000,  90),
('8',  'Webcam 1080p Full HD',     'Full HD 30fps, built-in stereo mic, autofocus, USB-A',   NULL,   650000, 130),
('9',  'Gigabit Switch 8-Port',    'Unmanaged 8-port GbE, plug-and-play, metal case',        NULL,   450000,  60),
('10', 'Wireless Inkjet Printer',  'A4 colour inkjet, Wi-Fi Direct, duplex, 22 ppm',         NULL,  3200000,  35);

-- ============================================================
-- 4. WAREHOUSE STOCK  (10 records — one product per warehouse)
-- ============================================================
INSERT INTO warehouse_stock (warehouse_id, product_id, quantity) VALUES
(1, '1',  120),
(2, '2',   80),
(1, '3',  200),
(3, '4',   45),
(2, '5',  350),
(4, '6',  500),
(1, '7',   90),
(2, '8',  130),
(3, '9',   60),
(1, '10',  35);

-- ============================================================
-- 5. PURCHASE ORDERS  (10 records)
-- ============================================================
INSERT INTO purchase_orders (po_id, supplier_id, date, received_date, status, total_amount) VALUES
( 1,  1, '2025-10-01', '2025-10-05', 'RECEIVED',  1350000000.00),
( 2,  2, '2025-10-10', '2025-10-14', 'RECEIVED',    44000000.00),
( 3,  3, '2025-11-01', '2025-11-06', 'RECEIVED',   178000000.00),
( 4,  4, '2025-11-15', '2025-11-20', 'RECEIVED',   261000000.00),
( 5,  5, '2025-12-01', '2025-12-06', 'RECEIVED',    96000000.00),
( 6,  6, '2026-01-05', '2026-01-09', 'RECEIVED',    47500000.00),
( 7,  7, '2026-02-01', '2026-02-07', 'RECEIVED',   108000000.00),
( 8,  8, '2026-03-01', '2026-03-05', 'RECEIVED',    84500000.00),
( 9,  9, '2026-04-01',          NULL, 'PENDING',    45000000.00),
(10, 10, '2026-04-15',          NULL, 'PENDING',   112000000.00);

-- ============================================================
-- 6. PO ITEMS  (10 records — one line per PO for simplicity)
-- ============================================================
INSERT INTO po_items (po_item_id, po_id, product_id, quantity, price) VALUES
( 1,  1, '1',   50, 27000000.00),
( 2,  2, '2',   80,   550000.00),
( 3,  3, '3',  200,   890000.00),
( 4,  4, '4',   45,  5800000.00),
( 5,  5, '5',  300,   320000.00),
( 6,  6, '6',  500,    95000.00),
( 7,  7, '7',   90,  1200000.00),
( 8,  8, '8',  130,   650000.00),
( 9,  9, '9',  100,   450000.00),
(10, 10, '10',  35,  3200000.00);

-- ============================================================
-- 7. ORDERS  (10 records, current year dates for dashboard charts)
-- NOTE: Update the year below if running in a different year.
-- ============================================================
INSERT INTO orders (order_id, customer, date, total_items, total_amount, payment_status) VALUES
( 1, 'Nguyen Van A',  '2026-01-15',  2, 57000000.00, 'paid'),
( 2, 'Tran Thi B',    '2026-01-22', 10,  6050000.00, 'paid'),
( 3, 'Le Van C',      '2026-02-05',  1,  5800000.00, 'pending'),
( 4, 'Pham Thi D',    '2026-02-18',  5,  3050000.00, 'paid'),
( 5, 'Hoang Van E',   '2026-03-03', 10,   950000.00, 'paid'),
( 6, 'Do Thi F',      '2026-03-20',  3,  7600000.00, 'pending'),
( 7, 'Vu Van G',      '2026-04-05',  4,  1800000.00, 'paid'),
( 8, 'Bui Thi H',     '2026-04-15',  4, 32100000.00, 'paid'),
( 9, 'Nguyen Van A',  '2026-04-28', 20,  6400000.00, 'pending'),
(10, 'Tran Thi B',    '2026-05-02', 15,  5400000.00, 'paid');

-- ============================================================
-- 8. ORDER ITEMS  (15 records — multi-item orders)
-- ============================================================
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, price) VALUES
( 1,  1, '1',   2, 28500000.00),   -- Order 1: 2× Laptop
( 2,  2, '5',   5,   320000.00),   -- Order 2: 5× Mouse
( 3,  2, '3',   5,   890000.00),   --          5× Keyboard
( 4,  3, '4',   1,  5800000.00),   -- Order 3: 1× Monitor
( 5,  4, '8',   3,   650000.00),   -- Order 4: 3× Webcam
( 6,  4, '2',   2,   550000.00),   --          2× USB Hub
( 7,  5, '6',  10,    95000.00),   -- Order 5: 10× HDMI Cable
( 8,  6, '10',  2,  3200000.00),   -- Order 6: 2× Printer
( 9,  6, '7',   1,  1200000.00),   --          1× SSD
(10,  7, '9',   4,   450000.00),   -- Order 7: 4× Switch
(11,  8, '1',   1, 28500000.00),   -- Order 8: 1× Laptop
(12,  8, '7',   3,  1200000.00),   --          3× SSD
(13,  9, '5',  20,   320000.00),   -- Order 9: 20× Mouse
(14, 10, '3',   5,   890000.00),   -- Order 10: 5× Keyboard
(15, 10, '6',  10,    95000.00);   --           10× HDMI Cable

-- ============================================================
-- 9. USERS  (10 records)
-- NOTE: Passwords are managed by the Python application layer
--       (SHA-256 + random salt via db_security.py).
--       The ADMIN user is auto-created/reset by login.py on startup.
--       These placeholder rows allow the table to be pre-populated;
--       users log in normally through the application.
-- ============================================================
INSERT INTO users (username, password, account_type, salt) VALUES
('ADMIN',       'placeholder', 'ADMIN', NULL),
('nguyen_van_a','placeholder', 'USER',  NULL),
('tran_thi_b',  'placeholder', 'USER',  NULL),
('le_van_c',    'placeholder', 'USER',  NULL),
('pham_thi_d',  'placeholder', 'USER',  NULL),
('hoang_van_e', 'placeholder', 'USER',  NULL),
('do_thi_f',    'placeholder', 'USER',  NULL),
('vu_van_g',    'placeholder', 'USER',  NULL),
('bui_thi_h',   'placeholder', 'USER',  NULL),
('superadmin',  'placeholder', 'ADMIN', NULL);

-- ============================================================
-- 10. INVENTORY LOG  (10 records — historical IN/OUT movements)
-- ============================================================
INSERT INTO inventory_log
    (product_id, warehouse_id, change_type, qty_change, old_qty, new_qty, notes, created_at)
VALUES
('1',  1, 'STOCK_ADDED',   50,   70, 120, 'Q1 initial laptop stock – Hanoi Central',   '2026-01-10 08:00:00'),
('2',  2, 'STOCK_ADDED',   80,    0,  80, 'USB hub reorder batch – HCM South Hub',      '2026-01-12 09:30:00'),
('3',  1, 'STOCK_ADDED',  200,    0, 200, 'Keyboard bulk shipment – Hanoi Central',     '2026-01-15 10:00:00'),
('4',  3, 'STOCK_ADDED',   45,    0,  45, '4K monitor quarterly order – Da Nang',       '2026-02-01 08:30:00'),
('5',  2, 'STOCK_ADDED',  350,    0, 350, 'Wireless mouse bulk purchase – HCM',         '2026-02-05 11:00:00'),
('1',  1, 'STOCK_REMOVED', -2, 120, 118, 'SO-001 Laptop sale Nguyen Van A',             '2026-01-15 14:00:00'),
('5',  2, 'STOCK_REMOVED', -5, 350, 345, 'SO-002 Mouse sale Tran Thi B',                '2026-01-22 10:00:00'),
('4',  3, 'STOCK_REMOVED', -1,  45,  44, 'SO-003 Monitor sale Le Van C',                '2026-02-05 09:00:00'),
('8',  2, 'STOCK_REMOVED', -3, 130, 127, 'SO-004 Webcam sale Pham Thi D',               '2026-02-18 15:00:00'),
('6',  4, 'STOCK_REMOVED',-10, 500, 490, 'SO-005 HDMI cable sale Hoang Van E',          '2026-03-03 09:30:00');

-- ============================================================
-- 11. LOGIN AUDIT  (5 records)
-- ============================================================
INSERT INTO login_audit (username, login_time, ip_address, success, notes) VALUES
('ADMIN',       '2026-01-10 08:00:00', 'localhost', TRUE,  'Initial system setup'),
('nguyen_van_a','2026-01-15 09:00:00', 'localhost', TRUE,  'Successful login'),
('tran_thi_b',  '2026-02-01 08:30:00', 'localhost', TRUE,  'Successful login'),
('unknown_user','2026-03-10 14:00:00', 'localhost', FALSE, 'Username not found'),
('ADMIN',       '2026-04-01 07:55:00', 'localhost', TRUE,  'Successful login');

-- ============================================================
-- 12. DATA ACCESS LOG  (5 records)
-- ============================================================
INSERT INTO data_access_log (username, action, table_name, record_id, access_time) VALUES
('ADMIN',       'SELECT', 'products',        NULL,  '2026-01-10 08:05:00'),
('nguyen_van_a','INSERT', 'orders',           '1',   '2026-01-15 14:05:00'),
('tran_thi_b',  'INSERT', 'orders',           '2',   '2026-01-22 10:05:00'),
('nguyen_van_a','UPDATE', 'products',         '1',   '2026-02-10 11:30:00'),
('ADMIN',       'SELECT', 'inventory_log',   NULL,  '2026-04-01 08:00:00');

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================
SELECT 'suppliers'       AS TableName, COUNT(*) AS RecordCount FROM suppliers
UNION ALL SELECT 'warehouses',      COUNT(*) FROM warehouses
UNION ALL SELECT 'products',        COUNT(*) FROM products
UNION ALL SELECT 'warehouse_stock', COUNT(*) FROM warehouse_stock
UNION ALL SELECT 'orders',          COUNT(*) FROM orders
UNION ALL SELECT 'order_items',     COUNT(*) FROM order_items
UNION ALL SELECT 'purchase_orders', COUNT(*) FROM purchase_orders
UNION ALL SELECT 'po_items',        COUNT(*) FROM po_items
UNION ALL SELECT 'users',           COUNT(*) FROM users
UNION ALL SELECT 'inventory_log',   COUNT(*) FROM inventory_log
UNION ALL SELECT 'login_audit',     COUNT(*) FROM login_audit
UNION ALL SELECT 'data_access_log', COUNT(*) FROM data_access_log;

-- Preview stock summary
SELECT * FROM vw_stock_summary ORDER BY product_id;

-- Preview monthly earnings (should show data for Jan–May of current year)
SELECT * FROM vw_monthly_earnings;

-- Preview low-stock alert
SELECT * FROM vw_low_stock_alert;

-- Preview total stock value per warehouse
SELECT * FROM vw_stock_value_per_warehouse ORDER BY warehouse_id;

-- ============================================================
-- END OF SAMPLE DATA
-- ============================================================