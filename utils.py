import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
from tkinter import messagebox
import traceback
import json
import customtkinter as ctk
import datetime

def error(text):
    """Creates an error message box and print the error."""

    print(f"[!]   {text}!")
    messagebox.showerror("[ Error ]", text)


def add_graphs(cur, frame):
    import matplotlib
    matplotlib.use("TkAgg")
    plt.style.use("dark_background")
    for param in ['text.color', 'axes.labelcolor', 'xtick.color', 'ytick.color']:
        plt.rcParams[param] = '0.9'

    for param in ['figure.facecolor', 'axes.facecolor', 'savefig.facecolor']:
        plt.rcParams[param] = '#1a1a1a'

    # Store references on the frame to prevent garbage collection
    if not hasattr(frame, '_chart_refs'):
        frame._chart_refs = []

    # ── Bar chart: Monthly Earnings (left side) ──
    try:
        fig_bar = plt.Figure(figsize=(3.9, 3.2), dpi=100)
        fig_bar.subplots_adjust(left=0.18, right=0.96, top=0.88, bottom=0.22)
        ax_bar = fig_bar.add_subplot(1, 1, 1)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        earnings = [0] * 12
        try:
            cur.execute("""
                SELECT MONTH(o.date) AS month_num, SUM(oi.quantity * oi.price) AS earnings
                FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                WHERE YEAR(o.date) = YEAR(CURDATE())
                GROUP BY MONTH(o.date)
                ORDER BY MONTH(o.date);
            """)
            results = cur.fetchall()
            for month_num, earning in results:
                if month_num and 1 <= int(month_num) <= 12:
                    earnings[int(month_num) - 1] = float(earning)
        except Exception as e:
            print(f"[!] Earnings query failed: {e}")

        max_earning = max(earnings) if earnings else 0
        display_scale = 1.0
        y_label = "Earnings ($)"
        if max_earning >= 1_000_000:
            display_scale = 1_000_000
            y_label = "Earnings ($M)"
        elif max_earning >= 1_000:
            display_scale = 1_000
            y_label = "Earnings ($K)"

        display_earnings = [value / display_scale for value in earnings]
        ax_bar.bar(months, display_earnings, color="#51E898")
        ax_bar.set_xlabel("Months")
        ax_bar.set_ylabel(y_label)
        ax_bar.set_title("Monthly Earnings")
        ax_bar.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.1f}" if value != int(value) else f"{int(value):,}"))
        plt.setp(ax_bar.get_xticklabels(), rotation=45, ha="right")

        canvas_bar = FigureCanvasTkAgg(fig_bar, master=frame)
        canvas_bar.draw()
        canvas_bar.get_tk_widget().place(x=15, y=200)
        frame._chart_refs.append((fig_bar, canvas_bar))
        print("[*] Bar chart rendered successfully")
    except Exception as e:
        print(f"[!] Bar chart error: {e}")
        traceback.print_exc()

    # ── Horizontal Bar chart: Top 5 Products (middle) ──
    try:
        cur.execute("""
            SELECT p.product_name, SUM(oi.quantity) as sold
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY sold ASC
            LIMIT 5;
        """)
        results = cur.fetchall()
        if results:
            fig_top = plt.Figure(figsize=(3.4, 3.2), dpi=100)
            fig_top.subplots_adjust(left=0.45, right=0.95, top=0.88, bottom=0.15)
            ax_top = fig_top.add_subplot(1, 1, 1)
            
            names = [r[0][:18] + ".." if len(r[0]) > 18 else r[0] for r in results]
            sold = [float(r[1]) for r in results]
            
            ax_top.barh(names, sold, color="#FF9F0A")
            ax_top.set_xlabel("Units Sold")
            ax_top.set_title("Top 5 Products")
            
            canvas_top = FigureCanvasTkAgg(fig_top, master=frame)
            canvas_top.draw()
            canvas_top.get_tk_widget().place(x=420, y=200)
            frame._chart_refs.append((fig_top, canvas_top))
            print("[*] Top 5 products chart rendered successfully")
    except Exception as e:
        print(f"[!] Top 5 products chart error: {e}")
        traceback.print_exc()

    # ── Pie chart: Order Status (right side) ──
    try:
        cur.execute("""
            SELECT LOWER(TRIM(payment_status)) AS status, COUNT(*) AS count
            FROM orders
            GROUP BY LOWER(TRIM(payment_status))
        """)
        payments = dict(cur.fetchall())
        paid_count = int(payments.get("paid", 0))
        pending_count = int(payments.get("pending", 0))
        order_count = [paid_count, pending_count]

        if sum(order_count) > 0:
            # Filter out zero-value slices so the chart looks clean
            labels = ["Paid", "Pending"]
            chart_colors = ["#FF5A5F", "#0079BF"]
            filtered = [(l, c, v) for l, c, v in zip(labels, chart_colors, order_count) if v > 0]
            f_labels, f_colors, f_values = zip(*filtered)

            fig_pie = plt.Figure(figsize=(2.6, 3.2), dpi=100)
            fig_pie.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
            ax_pie = fig_pie.add_subplot(1, 1, 1)
            ax_pie.pie(
                f_values,
                labels=f_labels,
                autopct="%1.1f%%",
                colors=f_colors,
                startangle=90,
            )
            ax_pie.set_title("Order Status")

            canvas_pie = FigureCanvasTkAgg(fig_pie, master=frame)
            canvas_pie.draw()
            canvas_pie.get_tk_widget().place(x=775, y=200)
            frame._chart_refs.append((fig_pie, canvas_pie))
            print("[*] Pie chart rendered successfully")
    except Exception as e:
        print(f"[!] Pie chart error: {e}")
        traceback.print_exc()


# ── Predictive Restocking Helpers ──

LOW_STOCK_THRESHOLD = 10

def get_low_stock_items(cur, threshold=LOW_STOCK_THRESHOLD):
    """Return products whose quantity is below the threshold."""
    cur.execute(
        f"SELECT product_id, product_name, quantity FROM products WHERE quantity < {threshold} ORDER BY quantity ASC;"
    )
    return cur.fetchall()


def get_restock_predictions(cur, threshold=LOW_STOCK_THRESHOLD):
    """Calculate sales velocity, days-to-stockout, and reorder qty for each product.

    Returns a list of tuples:
        (product_name, current_qty, avg_sales_per_day, days_until_stockout, reorder_qty, status)
    """
    # Average daily sales over the last 90 days per product
    cur.execute("""
        SELECT p.product_id, p.product_name, p.quantity,
               COALESCE(SUM(oi.quantity), 0) AS total_sold,
               DATEDIFF(CURDATE(), MIN(o.date)) AS span_days
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.order_id
              AND o.date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
        GROUP BY p.product_id, p.product_name, p.quantity
        ORDER BY p.quantity ASC;
    """)
    rows = cur.fetchall()

    predictions = []
    for product_id, name, qty, total_sold, span_days in rows:
        qty = int(qty)
        total_sold = int(total_sold)
        span_days = int(span_days) if span_days and int(span_days) > 0 else 90

        avg_daily = round(total_sold / span_days, 2) if span_days > 0 else 0
        days_left = int(qty / avg_daily) if avg_daily > 0 else 999
        # Suggest enough stock for 30 days
        reorder_qty = max(0, int(avg_daily * 30) - qty)

        if qty == 0:
            status = "❌ Out"
        elif qty < threshold:
            status = "⚠ Low"
        elif days_left <= 14:
            status = "⏳ Soon"
        else:
            status = "✓ OK"

        predictions.append((name, qty, avg_daily, days_left, reorder_qty, status))

    return predictions


def export_to_csv(cur, table, filepath):
    """Export a database table to a CSV file."""
    import csv
    cur.execute(f"SELECT * FROM {table};")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    return filepath


def generate_erp_json(cur):
    """Generate a structured JSON payload of current products and orders for ERP sync."""
    payload = {
        "export_date": datetime.datetime.now().isoformat(),
        "products": [],
        "orders": []
    }

    # Fetch products
    cur.execute("SELECT product_id, product_name, barcode, price, quantity FROM products;")
    for pid, pname, bcode, price, qty in cur.fetchall():
        payload["products"].append({
            "product_id": pid,
            "product_name": pname,
            "barcode": bcode,
            "price": float(price),
            "quantity": int(qty)
        })

    # Fetch orders
    cur.execute("SELECT order_id, customer, date, total_items, total_amount, payment_status FROM orders;")
    for oid, cust, date_obj, items, amt, status in cur.fetchall():
        payload["orders"].append({
            "order_id": oid,
            "customer": cust,
            "date": str(date_obj),
            "total_items": int(items),
            "total_amount": float(amt),
            "payment_status": status
        })

    return json.dumps(payload, indent=4)


def show_trend_window(cur, product_id, product_name, parent_window):
    """Open a new window displaying a line chart of sales over time for a product."""
    cur.execute("""
        SELECT DATE_FORMAT(o.date, '%Y-%m') AS month, SUM(oi.quantity) AS units_sold
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE oi.product_id = %s AND o.date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        GROUP BY month
        ORDER BY month ASC;
    """, (product_id,))
    
    results = cur.fetchall()
    if not results:
        messagebox.showinfo("No Data", f"No sales data found for {product_name} in the last 12 months.")
        return

    months = [row[0] for row in results]
    sales = [int(row[1]) for row in results]

    # Create top level window
    trend_win = ctk.CTkToplevel(parent_window)
    trend_win.title(f"Sales Trend: {product_name}")
    trend_win.geometry("600x400")
    trend_win.attributes("-topmost", True)
    
    fig = plt.Figure(figsize=(6, 4), dpi=100)
    fig.subplots_adjust(left=0.15, right=0.95, top=0.85, bottom=0.15)
    ax = fig.add_subplot(1, 1, 1)
    
    # Configure colors
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    ax.tick_params(colors='0.9')
    ax.xaxis.label.set_color('0.9')
    ax.yaxis.label.set_color('0.9')
    ax.title.set_color('0.9')
    for spine in ax.spines.values():
        spine.set_edgecolor('0.5')

    ax.plot(months, sales, color="#FF5A5F", marker="o", linestyle="-", linewidth=2, markersize=6)
    ax.set_xlabel("Month")
    ax.set_ylabel("Units Sold")
    ax.set_title(f"Monthly Sales Trend - {product_name}")
    
    # Rotate x labels if many months
    if len(months) > 6:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    canvas = FigureCanvasTkAgg(fig, master=trend_win)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)