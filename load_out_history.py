import mysql.connector

def load_out_history():
    try:
        con = mysql.connector.connect(host='localhost', user='root', passwd='Pkn2006@', database='inventory')
        cur = con.cursor()

        history = [
            ('1', 1, 'OUT', -40, 0, 0, 'SO-001 - Laptop dispatch Hanoi', '2024-01-20 14:00:00'),
            ('5', 2, 'OUT', -50, 0, 0, 'SO-002 - Mouse corporate order HCM', '2024-02-12 10:00:00'),
            ('7', 1, 'OUT', -20, 0, 0, 'SO-003 - SSD retail sale Hanoi', '2024-02-20 11:00:00'),
            ('4', 3, 'OUT', -26, 0, 0, 'SO-004 - Monitor education order Da Nang', '2024-02-22 09:00:00'),
            ('3', 1, 'OUT', -30, 0, 0, 'SO-005 - Keyboard office bundle Hanoi', '2024-03-01 10:00:00'),
            ('2', 2, 'OUT', -15, 0, 0, 'SO-006 - USB hub e-commerce HCM', '2024-03-05 14:00:00'),
            ('6', 4, 'OUT', -100, 0, 0, 'SO-007 - HDMI cable retail Can Tho', '2024-03-08 09:30:00'),
            ('9', 3, 'OUT', -10, 0, 0, 'SO-008 - Switch SME customer Da Nang', '2024-03-12 11:00:00'),
            ('8', 2, 'OUT', -25, 0, 0, 'SO-009 - Webcam work-from-home order HCM', '2024-03-15 15:00:00'),
            ('10', 1, 'OUT', -30, 0, 0, 'SO-010 - Printer government contract Hanoi', '2024-03-18 10:00:00')
        ]

        cur.executemany(
            "INSERT INTO inventory_log (product_id, warehouse_id, change_type, qty_change, old_qty, new_qty, notes, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
            history
        )

        con.commit()
        print("[*] Historical OUT transactions successfully appended to the Audit Log!")

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        if 'con' in locals() and con.is_connected():
            cur.close()
            con.close()

if __name__ == "__main__":
    load_out_history()
