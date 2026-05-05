import tkinter
from tkinter import ttk , messagebox, filedialog
from datetime import date
from pathlib import Path
import customtkinter as ctk
from PIL import Image

from utils import error, add_graphs, get_low_stock_items, get_restock_predictions, export_to_csv, generate_erp_json, show_trend_window
from db_security import hash_password, verify_password

ASSETS_DIR = Path(__file__).resolve().parent / "imgs"

class Menu():
    """Represents a menu for the inventory management system."""

    def __init__(self, con, user, login_win):
        # Set window theme as dark
        ctk.set_default_color_theme("dark-blue")
        ctk.set_appearance_mode("dark")
        # ctk.deactivate_automatic_dpi_awareness()
        self.login_win = login_win
        self.window =  ctk.CTkToplevel(self.login_win)
        self.window.protocol("WM_DELETE_WINDOW", exit)
        self.con = con
        self.cur = con.cursor()
        self.user = user
        self.font = 'Century Gothic'
        self.make_window()

    def make_window(self):
        """ Create window to display menu"""
        width = 1350
        height = 740
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.window.geometry("%dx%d+%d+%d" % (width, height, x, y))
        self.login_win.withdraw()
        self.make_panel()

    def make_panel(self):
        """ Create side panel or navigation panel"""
        side_panel = ctk.CTkFrame(self.window, corner_radius=0, width=250)
        side_panel.pack(fill="y", side="left")

        section_functions = {
            "dashboard": self.dashboard,
            "inventory": self.inventory,
            "orders": self.orders,
            "users": self.users,
            "shop": self.shop,
            "history": self.history,
            "suppliers": self.suppliers,
            "warehouses": self.warehouses,
            "purchase_orders": self.purchase_orders,
            "audit_log": self.audit_log,
            "logout": self.logout
        }

        # Add buttons for different sections in the side panel
        if self.user[2] == 'ADMIN':
            sections = ["dashboard", "inventory", "orders", "users", "suppliers", "warehouses", "purchase_orders", "audit_log", "logout"]
        else:
            sections = ["dashboard", "inventory", "shop", "history","logout"]

        for section in sections:
            img_path = ASSETS_DIR / f"{section}.png"
            if not img_path.exists():
                img_path = ASSETS_DIR / "inventory.png"
            img = ctk.CTkImage(Image.open(img_path).resize((30, 30)), size=(30, 30))
            button = ctk.CTkButton(side_panel, text=section.replace('_', ' ').title(), image= img, anchor="w", font=(self.font, 18),fg_color="transparent", hover_color="#212121", command=section_functions[section])
            button.pack(padx=50,pady=20)

        self.frame = ctk.CTkFrame(self.window, corner_radius=0 ,fg_color="#1a1a1a")
        self.frame.pack(fill="both", expand=True)
        self.dashboard()

    def set_title(self, title):
        """
        Sets the title of the user interface window.
        Args:
            title (str): The title to set for the window.
        """
        try:
            self.frame.forget()
            self.frame = ctk.CTkFrame(self.window, corner_radius=0 ,fg_color="#1a1a1a")
            self.frame.pack(fill="both", expand=True)

        except:
            pass
        self.window.title(title)
        heading = ctk.CTkLabel(self.frame, text=title, anchor="center", font=(self.font, 33) )
        heading.pack()

    def dashboard(self):
        """ Displays the dashboard section of the user interface."""
        self.set_title("Dashboard")

        # ── ERP Sync Button ──
        sync_btn = ctk.CTkButton(self.frame, text="Sync to ERP", command=self.sync_to_erp,
                                 fg_color="#ffcc00", text_color="black", font=(self.font, 16, "bold"), width=120)
        sync_btn.place(x=870, y=15)

        # ── Stat cards ──
        self.cur.execute("SELECT COUNT(*) FROM orders WHERE Date(date) = Curdate();")
        sales = self.cur.fetchall()[0]
        self.cur.execute("SELECT COUNT(*) FROM orders;")
        transactions = self.cur.fetchall()[0]
        self.cur.execute("SELECT COUNT(*) FROM products;")
        items = self.cur.fetchall()[0]

        low_stock = get_low_stock_items(self.cur)
        low_count = len(low_stock)

        cards = [
            ("Total Sales Today", sales, "#007fff"),
            ("Total Transactions", transactions, "#007fff"),
            ("Items in Inventory", items, "#007fff"),
            ("Low Stock Items", (low_count,), "#ff3b30" if low_count > 0 else "#34c759"),
        ]
        x = 15
        for title, value, color in cards:
            card = ctk.CTkFrame(master=self.frame, width=240, height=100, corner_radius=12, fg_color=color)
            card.place(x=x, y=55)

            lbl = ctk.CTkLabel(card, text=value[0], fg_color=color, font=(self.font, 36))
            lbl.place(relx=0.5, y=10, anchor="n")

            txt = ctk.CTkLabel(card, text=title, fg_color=color, font=(self.font, 14))
            txt.place(relx=0.5, y=62, anchor="n")

            x += 255

        # ── Charts ──
        try:
            add_graphs(self.cur, self.frame)
        except Exception as e:
            print(f"[!] Dashboard charts error: {e}")
            import traceback
            traceback.print_exc()

        # ── Restock Predictions Table ──
        try:
            predictions = get_restock_predictions(self.cur)
            # Only show items that need attention (not OK status)
            alerts = [p for p in predictions if p[5] != "✓ OK"]
            if alerts:
                restock_frame = ctk.CTkFrame(self.frame, corner_radius=10, fg_color="#2a2d2e")
                restock_frame.place(x=30, y=560, width=1000, height=130)

                header_lbl = ctk.CTkLabel(restock_frame, text="⚠  Restock Predictions",
                                          font=(self.font, 16, "bold"), text_color="#FF5A5F", anchor="w")
                header_lbl.pack(padx=15, pady=(8, 2), anchor="w")

                col_frame = ctk.CTkFrame(restock_frame, fg_color="#343638", corner_radius=6)
                col_frame.pack(fill="x", padx=10, pady=2)
                headers = ["Product", "Qty", "Sales/Day", "Days Left", "Reorder Qty", "Status"]
                widths =  [200,       70,    90,          90,          100,            90]
                for h, w in zip(headers, widths):
                    ctk.CTkLabel(col_frame, text=h, font=(self.font, 12, "bold"),
                                 width=w, anchor="w").pack(side="left", padx=6, pady=4)

                for name, qty, avg_daily, days_left, reorder_qty, status in alerts[:4]:
                    row = ctk.CTkFrame(restock_frame, fg_color="transparent", height=22)
                    row.pack(fill="x", padx=10)
                    days_str = str(days_left) if days_left < 999 else "∞"
                    vals = [name[:25], str(qty), f"{avg_daily:.1f}", days_str, str(reorder_qty), status]
                    for v, w in zip(vals, widths):
                        color = "#FF5A5F" if "❌" in v or "⚠" in v else "#FFFFFF"
                        ctk.CTkLabel(row, text=v, font=(self.font, 12), width=w,
                                     anchor="w", text_color=color).pack(side="left", padx=6)
        except Exception as e:
            print(f"[!] Restock predictions error: {e}")
            import traceback
            traceback.print_exc()

    def sync_to_erp(self):
        """Generates JSON payload for ERP sync and saves to file."""
        try:
            json_payload = generate_erp_json(self.cur)
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialfile=f"erp_sync_{date.today().strftime('%Y%m%d')}.json",
                title="Save ERP Sync Data"
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_payload)
                messagebox.showinfo("ERP Sync", f"Data successfully synced and saved to:\n{filepath}")
        except Exception as e:
            error(f"Failed to sync with ERP: {e}")

    def inventory(self):
        """ Displays the inventory section of the user interface. """
        self.set_title("Inventory")
        if self.user[2] == 'ADMIN':
            add_button = ctk.CTkButton(self.frame, width=50, command=self.add_button, text="Add Item", fg_color="#007fff", font=(self.font , 20))
            add_button.place(x=50,y=50)
            
            edit_button = ctk.CTkButton(self.frame, width=50, command=self.edit_button, text="Edit Item", fg_color="#ff9f0a", font=(self.font , 20))
            edit_button.place(x=150,y=50)

            export_btn = ctk.CTkButton(self.frame, width=50, command=self.export_inventory_csv,
                                       text="Export CSV", fg_color="#34c759", font=(self.font, 20))
            export_btn.place(x=250, y=50)
            
        trend_btn = ctk.CTkButton(self.frame, width=50, command=self.view_trend,
                                   text="View Trend", fg_color="#8ED1FC", text_color="black", font=(self.font, 20))
        trend_btn.place(x=380 if self.user[2] == 'ADMIN' else 50, y=50)

        self.make_table(("Product ID", "Product Name", "Description", "Barcode", "Price", "Quantity"), 130, "products")

    def view_trend(self):
        """Shows trend chart for the selected product."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Product", "Please select a product from the table first.")
            return
        
        values = self.tree.item(selected[0], "values")
        product_id = values[0]
        product_name = values[1]
        
        try:
            show_trend_window(self.cur, product_id, product_name, self.window)
        except Exception as e:
            error(f"Failed to show trend: {e}")

    def export_inventory_csv(self):
        """Export inventory data to a CSV file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="inventory_export.csv",
            title="Export Inventory"
        )
        if filepath:
            try:
                export_to_csv(self.cur, "products", filepath)
                messagebox.showinfo("Export Successful", f"Inventory exported to:\n{filepath}")
            except Exception as e:
                error(f"Export failed: {e}")

    def users(self):
        """ Displays the Users section of the user interface. """
        self.set_title("Users")
        if self.user[2] == 'ADMIN':
            del_button = ctk.CTkButton(self.frame, width=50, command=self.delete_user, text="Delete User", fg_color="#fb0000", font=(self.font , 20))
            del_button.place(x=50,y=50)
            
            del_all_button = ctk.CTkButton(self.frame, width=50, command=self.delete_all_users, text="Delete All Users", fg_color="#fb0000", font=(self.font , 20))
            del_all_button.place(x=200,y=50)

            edit_pwd_button = ctk.CTkButton(self.frame, width=50, command=self.edit_password, text="Edit Password", fg_color="#ff9f0a", font=(self.font , 20))
            edit_pwd_button.place(x=400,y=50)

        self.make_table(("Username", "Password", "Account Type"), 170 ,"users")

    def edit_password(self):
        selected = self.tree.selection()
        if not selected:
            error("Select a User first")
            return
            
        values = self.tree.item(selected[0], "values")
        username = values[0]

        topwin = ctk.CTkToplevel(self.window)
        topwin.title("Change Password")
        topwin.geometry("450x400")
        frame = ctk.CTkFrame(master=topwin, width=400, height=350, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        ctk.CTkLabel(frame, text=f"Change password for {username}", font=(self.font, 18)).place(x=50, y=20)

        ctk.CTkLabel(frame, text="Current Password", font=(self.font, 14)).place(x=50, y=70)
        curr_pwd = ctk.CTkEntry(master=frame, show="*", width=300, height=35)
        curr_pwd.place(x=50, y=100)

        ctk.CTkLabel(frame, text="New Password", font=(self.font, 14)).place(x=50, y=150)
        new_pwd = ctk.CTkEntry(master=frame, show="*", width=300, height=35)
        new_pwd.place(x=50, y=180)

        def save_password():
            curr_val = curr_pwd.get()
            new_val = new_pwd.get()
            
            if not curr_val or not new_val:
                error("Both fields are required")
                return
            
            self.cur.execute("SELECT password, salt FROM users WHERE username=%s", (username,))
            res = self.cur.fetchone()
            if not res:
                error("User not found")
                return
            
            stored_hash, stored_salt = res
            if not verify_password(curr_val, stored_hash, stored_salt):
                error("Incorrect current password")
                return
            
            new_hash, new_salt = hash_password(new_val)
            try:
                self.cur.execute("UPDATE users SET password=%s, salt=%s WHERE username=%s", (new_hash, new_salt, username))
                self.con.commit()
                messagebox.showinfo("Success", f"Password for {username} changed successfully!")
                topwin.destroy()
                self.tree.delete(*self.tree.get_children())
                self.render_table("users")
            except Exception as e:
                error(str(e))

        btn = ctk.CTkButton(master=frame, width=300, text="Save Password", command=save_password)
        btn.place(x=50, y=250)

    def delete_user(self):
        selected = self.tree.selection()
        if not selected:
            error("Select a User first")
            return
            
        values = self.tree.item(selected[0], "values")
        username = values[0]

        if username == self.user[0]:
            error("Cannot delete yourself")
            return
        
        if messagebox.askyesno('Alert!', f'Do you want to delete user "{username}"?'):
            try:
                self.cur.execute(f"DELETE FROM users WHERE username = '{username}';")
                self.con.commit()
                messagebox.showinfo("Success", f"User {username} deleted!")
                self.tree.delete(*self.tree.get_children())
                self.render_table("users")
            except Exception as e:
                error(str(e))

    def delete_all_users(self):
        if messagebox.askyesno('Alert!', 'Do you want to delete all users EXCEPT yourself? This action cannot be undone.'):
            try:
                self.cur.execute(f"DELETE FROM users WHERE username != '{self.user[0]}';")
                self.con.commit()
                messagebox.showinfo("Success", "All other users deleted!")
                self.tree.delete(*self.tree.get_children())
                self.render_table("users")
            except Exception as e:
                error(str(e))


    def suppliers(self):
        self.set_title("Suppliers")
        if self.user[2] == 'ADMIN':
            add_button = ctk.CTkButton(self.frame, width=50, command=self.add_supplier_button, text="Add Supplier", fg_color="#007fff", font=(self.font , 20))
            add_button.place(x=50,y=50)
            
            calc_btn = ctk.CTkButton(self.frame, width=50, command=self.calc_delivery_time, text="Delivery Time", fg_color="#34c759", font=(self.font , 20))
            calc_btn.place(x=220,y=50)

        self.make_table(("Supplier ID", "Name", "Contact", "Phone", "Email", "Address"), 130, "suppliers")

    def calc_delivery_time(self):
        selected = self.tree.selection()
        if not selected:
            error("Select a Supplier first")
            return
            
        values = self.tree.item(selected[0], "values")
        supplier_id = values[0]
        supplier_name = values[1]
        
        try:
            self.cur.execute(f"SELECT fn_avg_delivery_time({supplier_id});")
            res = self.cur.fetchone()
            if res and res[0] is not None:
                avg_time = float(res[0])
                messagebox.showinfo("Delivery Time", f"Supplier: {supplier_name}\nAverage Delivery Time: {avg_time:.1f} days")
            else:
                messagebox.showinfo("Delivery Time", f"Supplier: {supplier_name}\nNo completed delivery data available.")
        except Exception as e:
            error(f"Error calculating delivery time: {e}")

    def add_supplier_button(self):
        self.topwin = ctk.CTkToplevel(self.window)
        self.topwin.title("Add Supplier")
        self.topwin.geometry("500x500")
        frame = ctk.CTkFrame(master=self.topwin, width=450, height=470, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.supp_entries = {}
        items = ['Name', 'Contact Person', 'Phone', 'Email', 'Address']
        y = 50
        for i in items:
            label = ctk.CTkLabel(frame, text=i,font=(self.font, 14))
            label.place(x=50,y=y-25)
            entry = ctk.CTkEntry(master=frame, placeholder_text=i, width=350 , height=35)
            entry.place(x=50, y=y)
            self.supp_entries[i] = entry
            y+=70

        button = ctk.CTkButton(master=frame, width=400, text="Add", corner_radius=6, command=self.add_supplier)
        button.place(x=25, y=400)

    def add_supplier(self):
        name = self.supp_entries['Name'].get()
        contact = self.supp_entries['Contact Person'].get()
        phone = self.supp_entries['Phone'].get()
        email = self.supp_entries['Email'].get()
        address = self.supp_entries['Address'].get()

        if not name:
            error("Name is required")
            return
        
        self.cur.execute(f"INSERT INTO suppliers (name, contact_person, phone, email, address) VALUES ('{name}', '{contact}', '{phone}', '{email}', '{address}')")
        self.con.commit()
        messagebox.showinfo("Success", "Supplier added!")
        self.topwin.destroy()
        self.tree.delete(*self.tree.get_children())
        self.render_table("suppliers")


    def warehouses(self):
        self.set_title("Warehouses")
        if self.user[2] == 'ADMIN':
            add_button = ctk.CTkButton(self.frame, width=50, command=self.add_warehouse_button, text="Add Warehouse", fg_color="#007fff", font=(self.font , 20))
            add_button.place(x=50,y=50)
            
            view_stock_btn = ctk.CTkButton(self.frame, width=50, command=self.view_warehouse_stock, text="View All Stock", fg_color="#34c759", font=(self.font , 20))
            view_stock_btn.place(x=230,y=50)
            
            view_sel_stock_btn = ctk.CTkButton(self.frame, width=50, command=self.view_selected_warehouse_stock, text="View Selected Stock", fg_color="#ff9f0a", font=(self.font , 20))
            view_sel_stock_btn.place(x=400,y=50)
            
        self.make_table(("Warehouse ID", "Name", "Location", "Capacity"), 130, "warehouses")

    def add_warehouse_button(self):
        self.topwin = ctk.CTkToplevel(self.window)
        self.topwin.title("Add Warehouse")
        self.topwin.geometry("500x350")
        frame = ctk.CTkFrame(master=self.topwin, width=450, height=320, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.wh_entries = {}
        items = ['Name', 'Location', 'Capacity']
        y = 50
        for i in items:
            label = ctk.CTkLabel(frame, text=i,font=(self.font, 14))
            label.place(x=50,y=y-25)
            entry = ctk.CTkEntry(master=frame, placeholder_text=i, width=350 , height=35)
            entry.place(x=50, y=y)
            self.wh_entries[i] = entry
            y+=70

        button = ctk.CTkButton(master=frame, width=400, text="Add", corner_radius=6, command=self.add_warehouse)
        button.place(x=25, y=260)

    def add_warehouse(self):
        name = self.wh_entries['Name'].get()
        location = self.wh_entries['Location'].get()
        capacity = self.wh_entries['Capacity'].get()

        if not name:
            error("Name is required")
            return
            
        try:
            capacity = int(capacity) if capacity else 0
        except:
            error("Capacity must be a number")
            return
        
        self.cur.execute(f"INSERT INTO warehouses (name, location, capacity) VALUES ('{name}', '{location}', {capacity})")
        self.con.commit()
        messagebox.showinfo("Success", "Warehouse added!")
        self.topwin.destroy()
        self.tree.delete(*self.tree.get_children())
        self.render_table("warehouses")
        
    def view_selected_warehouse_stock(self):
        selected = self.tree.selection()
        if not selected:
            error("Select a Warehouse first")
            return
            
        values = self.tree.item(selected[0], "values")
        warehouse_id = values[0]
        warehouse_name = values[1]

        self.set_title(f"Stock for Warehouse: {warehouse_name}")
        self.make_table(("Warehouse ID", "Warehouse Name", "Product ID", "Product Name", "Quantity"), 130)
        self.render_table(query=f"SELECT * FROM vw_warehouse_stock WHERE warehouse_id = {warehouse_id};")

    def view_warehouse_stock(self):
        self.set_title("All Warehouse Stock")
        self.make_table(("Warehouse ID", "Warehouse Name", "Product ID", "Product Name", "Quantity"), 130)
        self.render_table(query="SELECT * FROM vw_warehouse_stock;")


    def purchase_orders(self):
        self.set_title("Purchase Orders")
        if self.user[2] == 'ADMIN':
            add_button = ctk.CTkButton(self.frame, width=50, command=self.add_po_button, text="Create PO", fg_color="#007fff", font=(self.font , 20))
            add_button.place(x=50,y=50)
            
            receive_btn = ctk.CTkButton(self.frame, width=50, command=self.receive_po_button, text="Receive PO", fg_color="#34c759", font=(self.font , 20))
            receive_btn.place(x=200,y=50)
            
        self.make_table(("PO ID", "Date", "Supplier Name", "Status", "Total Amount"), 130)
        self.render_table(query="SELECT * FROM vw_po_details ORDER BY po_id DESC;")
        
    def add_po_button(self):
        self.topwin = ctk.CTkToplevel(self.window)
        self.topwin.title("Create Purchase Order")
        self.topwin.geometry("500x400")
        frame = ctk.CTkFrame(master=self.topwin, width=450, height=370, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        
        self.cur.execute("SELECT supplier_id, name FROM suppliers")
        suppliers = self.cur.fetchall()
        sup_list = [f"{s[0]} - {s[1]}" for s in suppliers] if suppliers else ["No suppliers"]

        ctk.CTkLabel(frame, text="Supplier ID:", font=(self.font, 14)).place(x=50, y=30)
        self.po_sup = ctk.CTkComboBox(frame, width=350, values=sup_list)
        self.po_sup.place(x=50, y=55)
        if sup_list and sup_list[0] != "No suppliers":
            self.po_sup.set(sup_list[0])
        
        self.cur.execute("SELECT product_id, product_name FROM products")
        products = self.cur.fetchall()
        prod_list = [f"{p[0]} - {p[1]}" for p in products] if products else ["No products"]

        ctk.CTkLabel(frame, text="Product ID:", font=(self.font, 14)).place(x=50, y=100)
        self.po_prod = ctk.CTkComboBox(frame, width=350, values=prod_list)
        self.po_prod.place(x=50, y=125)
        if prod_list and prod_list[0] != "No products":
            self.po_prod.set(prod_list[0])
        
        ctk.CTkLabel(frame, text="Quantity:", font=(self.font, 14)).place(x=50, y=170)
        self.po_qty = ctk.CTkEntry(frame, width=350)
        self.po_qty.place(x=50, y=195)
        
        ctk.CTkButton(frame, text="Create", width=400, command=self.create_po).place(x=25, y=280)

    def create_po(self):
        sup_val = self.po_sup.get()
        prod_val = self.po_prod.get()
        qty = self.po_qty.get()
        
        if sup_val == "No suppliers" or prod_val == "No products":
            error("Valid Supplier and Product must be selected")
            return
            
        sup_id = sup_val.split(" - ")[0]
        prod_id = prod_val.split(" - ")[0]
        
        try:
            self.cur.execute(f"SELECT price FROM products WHERE product_id='{prod_id}'")
            res = self.cur.fetchone()
            if not res:
                error("Product not found")
                return
            price = res[0]
            
            total = float(price) * int(qty)
            self.cur.execute(f"INSERT INTO purchase_orders (supplier_id, date, status, total_amount) VALUES ({sup_id}, CURDATE(), 'PENDING', {total})")
            po_id = self.cur.lastrowid
            self.cur.execute(f"INSERT INTO po_items (po_id, product_id, quantity, price) VALUES ({po_id}, '{prod_id}', {qty}, {price})")
            self.con.commit()
            messagebox.showinfo("Success", "Purchase Order Created")
            self.topwin.destroy()
            self.tree.delete(*self.tree.get_children())
            self.render_table(query="SELECT * FROM vw_po_details ORDER BY po_id DESC;")
        except Exception as e:
            error(str(e))
            
    def receive_po_button(self):
        selected = self.tree.selection()
        if not selected:
            error("Select a PO first")
            return
        
        values = self.tree.item(selected[0], "values")
        if values[3] == 'RECEIVED':
            error("PO is already received")
            return
            
        po_id = values[0]
        self.cur.execute("SELECT warehouse_id, name FROM warehouses")
        warehouses = self.cur.fetchall()
        if not warehouses:
            error("No warehouses available.")
            return
            
        wh_list = [f"{w[0]} - {w[1]}" for w in warehouses]
        
        popup = ctk.CTkToplevel(self.window)
        popup.title("Receive Purchase Order")
        popup.geometry("400x200")
        
        ctk.CTkLabel(popup, text=f"Select Warehouse to Receive PO #{po_id}:", font=(self.font, 14)).place(x=30, y=30)
        
        wh_combo = ctk.CTkComboBox(popup, width=340, values=wh_list)
        wh_combo.place(x=30, y=70)
        wh_combo.set(wh_list[0])
        
        def confirm():
            val = wh_combo.get()
            wh_id = val.split(" - ")[0]
            try:
                self.cur.execute(f"CALL sp_receive_po({po_id}, {wh_id});")
                self.con.commit()
                messagebox.showinfo("Success", f"PO {po_id} received into Warehouse ID {wh_id}")
                popup.destroy()
                self.tree.delete(*self.tree.get_children())
                self.render_table(query="SELECT * FROM vw_po_details ORDER BY po_id DESC;")
            except Exception as e:
                error(str(e))
                
        ctk.CTkButton(popup, text="Confirm Receive", width=340, command=confirm).place(x=30, y=130)



    def shop(self):
        """ Displays the shop section of the user interface. """
        self.set_title("Shop Items")
        add_button = ctk.CTkButton(self.frame, width=50, command=self.add_item, text="Add Item to cart", fg_color="#007fff", font=(self.font , 25))
        add_button.place(x=50,y=50)

        remove = ctk.CTkButton(self.frame, width=50, command=self.remove_item, text="Remove Item", fg_color="#fb0000", font=(self.font , 25))
        remove.place(x=50,y=530)

        label = ctk.CTkLabel(self.frame, text="Total Amount :", font=(self.font, 30))
        label.place(x=700,y=530)

        button = ctk.CTkButton(master=self.frame, width=390, text="Buy Items", corner_radius=6, command=self.buy)
        button.place(x=700, y=600)
        headings = ("Product Id","Product Name", "Description", "Price", "Quantity", "Total Amount")
        self.make_table(headings, 130,height=400)


    def orders(self):
        """ Displays all the Orders placed in the system."""
        self.set_title("Orders")
        
        view_all_btn = ctk.CTkButton(self.frame, width=50, command=self.view_all_orders, text="View All", fg_color="#007fff", font=(self.font , 20))
        view_all_btn.place(x=50,y=50)
        
        view_paid_btn = ctk.CTkButton(self.frame, width=50, command=self.view_paid_orders, text="Paid", fg_color="#34c759", font=(self.font , 20))
        view_paid_btn.place(x=150,y=50)
        
        view_pending_btn = ctk.CTkButton(self.frame, width=50, command=self.view_pending_orders, text="Pending", fg_color="#ff9f0a", font=(self.font , 20))
        view_pending_btn.place(x=250,y=50)

        repay_btn = ctk.CTkButton(self.frame, width=50, command=self.repay_order, text="Repay", fg_color="#af52de", font=(self.font , 20))
        repay_btn.place(x=370,y=50)

        headings = ("Order Id", "Customer", "Date", "Total Items", "Total Amount", "Payment Status")
        self.make_table(headings, 130, "orders")

    def view_all_orders(self):
        self.tree.delete(*self.tree.get_children())
        self.render_table(query="SELECT * FROM orders;")

    def view_paid_orders(self):
        self.tree.delete(*self.tree.get_children())
        self.render_table(query="SELECT * FROM orders WHERE payment_status = 'paid';")

    def view_pending_orders(self):
        self.tree.delete(*self.tree.get_children())
        self.render_table(query="SELECT * FROM orders WHERE payment_status = 'pending';")

    def audit_log(self):
        """ Displays the full inventory audit log. """
        self.set_title("Audit Log")
        headings = ("Log ID", "Product", "Warehouse", "Type", "Qty Change", "Old Qty", "New Qty", "Notes", "Date")
        self.make_table(headings, 110, "inventory_log")


    def _history_base_query(self, status_filter=None):
        """Returns the SQL query for the current user's order history, optionally filtered."""
        query = f"""SELECT o.order_id, p.product_name, oi.quantity, oi.price, o.date, o.payment_status
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.customer = '{self.user[0]}'"""
        if status_filter:
            query += f" AND o.payment_status = '{status_filter}'"
        query += ";"
        return query

    def history(self):
        """ Displays the order history of the user. """
        self.set_title("Transactions History")

        view_all_btn = ctk.CTkButton(self.frame, width=50, command=self.history_view_all, text="View All", fg_color="#007fff", font=(self.font, 20))
        view_all_btn.place(x=50, y=50)

        view_paid_btn = ctk.CTkButton(self.frame, width=50, command=self.history_view_paid, text="Paid", fg_color="#34c759", font=(self.font, 20))
        view_paid_btn.place(x=150, y=50)

        view_pending_btn = ctk.CTkButton(self.frame, width=50, command=self.history_view_pending, text="Pending", fg_color="#ff9f0a", font=(self.font, 20))
        view_pending_btn.place(x=250, y=50)

        repay_btn = ctk.CTkButton(self.frame, width=50, command=self.repay_order, text="Repay", fg_color="#af52de", font=(self.font, 20))
        repay_btn.place(x=370, y=50)

        headings = ("Order Id", "Product Name", "Quantity", "Price", "Date", "Payment Status")
        self.make_table(headings, 130)
        self.render_table(query=self._history_base_query())

    def history_view_all(self):
        self.tree.delete(*self.tree.get_children())
        self.render_table(query=self._history_base_query())

    def history_view_paid(self):
        self.tree.delete(*self.tree.get_children())
        self.render_table(query=self._history_base_query("paid"))

    def history_view_pending(self):
        self.tree.delete(*self.tree.get_children())
        self.render_table(query=self._history_base_query("pending"))

    def repay_order(self):
        """Opens QR payment window to repay a pending order."""
        selected = self.tree.selection()
        if not selected:
            error("Select an order first")
            return

        values = self.tree.item(selected[0], "values")
        order_id = values[0]

        # Get payment status — could be last column in both Orders and History views
        payment_status = values[-1].strip().lower()
        if payment_status == "paid":
            error("This order is already paid")
            return

        # Get total amount from orders table
        self.cur.execute(f"SELECT total_amount FROM orders WHERE order_id = {order_id};")
        res = self.cur.fetchone()
        if not res:
            error("Order not found")
            return
        total_amount = float(res[0])

        # ── Repay Payment Window ──
        pay_win = ctk.CTkToplevel(self.window)
        pay_win.title(f"Repay Order #{order_id}")
        pay_win.geometry("420x780")
        pay_win.resizable(False, False)
        pay_win.grab_set()

        container = ctk.CTkFrame(pay_win, fg_color="#0d1117", corner_radius=0)
        container.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkLabel(container, text=f"💳  Repay Order #{order_id}",
                               font=(self.font, 22, "bold"), text_color="#58a6ff")
        header.pack(pady=(20, 5))

        # Total amount display
        amount_frame = ctk.CTkFrame(container, fg_color="#161b22", corner_radius=12,
                                     border_width=1, border_color="#30363d")
        amount_frame.pack(padx=30, pady=(5, 15), fill="x")

        ctk.CTkLabel(amount_frame, text="Amount Due", font=(self.font, 13),
                      text_color="#8b949e").pack(pady=(12, 0))
        ctk.CTkLabel(amount_frame, text=f"{total_amount:,.0f} VND", font=(self.font, 28, "bold"),
                      text_color="#f85149").pack(pady=(2, 12))

        # QR Code
        qr_frame = ctk.CTkFrame(container, fg_color="#f6f8fa", corner_radius=12)
        qr_frame.pack(padx=30, pady=(0, 10))

        try:
            qr_path = ASSETS_DIR / "qr_payment.jpg"
            qr_img = Image.open(qr_path)
            qr_img = qr_img.resize((300, 360), Image.LANCZOS)
            qr_ctk = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(300, 360))
            qr_label = ctk.CTkLabel(qr_frame, image=qr_ctk, text="")
            qr_label.image = qr_ctk
            qr_label.pack(padx=10, pady=10)
        except Exception as e:
            ctk.CTkLabel(qr_frame, text="QR Code not found", font=(self.font, 14),
                          text_color="#ff5555").pack(padx=40, pady=40)

        # Bank info
        info_frame = ctk.CTkFrame(container, fg_color="#161b22", corner_radius=10,
                                   border_width=1, border_color="#30363d")
        info_frame.pack(padx=30, pady=(0, 15), fill="x")

        for label_text, value_text in [("Account Holder", "PHAM KHOI NGUYEN"),
                                        ("Account Number", "109882575681"),
                                        ("Bank", "VietinBank - CN DONG DA")]:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=label_text, font=(self.font, 12),
                          text_color="#8b949e", anchor="w", width=130).pack(side="left")
            ctk.CTkLabel(row, text=value_text, font=(self.font, 12, "bold"),
                          text_color="#c9d1d9", anchor="e").pack(side="right")

        # Confirm payment button
        def confirm_repay():
            try:
                self.cur.execute(f"UPDATE orders SET payment_status = 'paid' WHERE order_id = {order_id};")
                self.con.commit()
                messagebox.showinfo("Success", f"Order #{order_id} has been marked as Paid!")
                pay_win.destroy()
                # Refresh the table
                self.tree.delete(*self.tree.get_children())
                # Re-render depending on current view
                try:
                    self.render_table("orders")
                except Exception:
                    query = f"""SELECT o.order_id, p.product_name, oi.quantity, oi.price, o.date, o.payment_status
                                FROM orders o
                                JOIN order_items oi ON o.order_id = oi.order_id
                                JOIN products p ON oi.product_id = p.product_id
                                WHERE o.customer = '{self.user[0]}';"""
                    self.render_table(query=query)
            except Exception as e:
                error(f"Failed to update payment: {e}")

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(padx=30, pady=(0, 20), fill="x")

        confirm_btn = ctk.CTkButton(btn_frame, text="✅  Confirm Payment", font=(self.font, 16, "bold"),
                                     fg_color="#238636", hover_color="#2ea043", height=42,
                                     command=confirm_repay)
        confirm_btn.pack(fill="x", pady=(0, 8))

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", font=(self.font, 16),
                                    fg_color="#30363d", hover_color="#484f58", height=42,
                                    command=pay_win.destroy)
        cancel_btn.pack(fill="x")


    def add_item(self):
        """Display another window to add items to cart"""
        new_win = ctk.CTkToplevel(self.window)
        new_win.title("Add item to Cart")
        new_win.geometry("560x560")

        self.win_frame = ctk.CTkFrame(master=new_win, width=530, height=500, corner_radius=15)
        self.win_frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        self.item_var = ctk.StringVar(value="")

        label = ctk.CTkLabel(self.win_frame, text="Select Item :", font=(self.font, 20))
        label.place(x=50, y=60)

        self.cur.execute("SELECT product_name FROM products")
        products = self.cur.fetchall()
        product_names = [p[0] for p in products  ]
        combobox = ctk.CTkComboBox(self.win_frame, values=product_names, command=self.fill_labels, variable=self.item_var, width=220)
        combobox.place(x=280, y=60)
        self.item_combobox = combobox

        barcode_label = ctk.CTkLabel(self.win_frame, text="Scan Barcode :", font=(self.font, 20))
        barcode_label.place(x=50, y=320)
        self.barcode_entry = ctk.CTkEntry(self.win_frame, width=220, placeholder_text="Barcode")
        self.barcode_entry.place(x=280, y=320)
        self.barcode_entry.bind("<Return>", self.search_by_barcode)
        scan_button = ctk.CTkButton(self.win_frame, text="Scan", width=90, command=self.start_scan_input)
        scan_button.place(x=280, y=365)
        barcode_button = ctk.CTkButton(self.win_frame, text="Find", width=90, command=self.search_by_barcode)
        barcode_button.place(x=390, y=365)
        labels = ['Available Quantity', 'Unit Price', 'Quantity']
        x, y = 50,  130
        self.entries={}
        for i in labels:
            label = ctk.CTkLabel(self.win_frame, text=f"{i} :", font=(self.font, 20))
            label.place(x=x,y=y)
            y+=60

        button = ctk.CTkButton(master=self.win_frame, width=400, text="Add", corner_radius=6, command=self.add_to_cart)
        button.place(x=65, y=440)

        if product_names:
            self.item_var.set(product_names[0])
            self.item_combobox.set(product_names[0])
            self.fill_labels(product_names[0])

    def search_by_barcode(self, event=None):
        """Select an item by barcode (supports scanner + Enter)."""
        barcode = self.barcode_entry.get().strip()
        if barcode == "":
            error("Enter or scan a barcode")
            return
        self.cur.execute(f"SELECT product_name FROM products WHERE barcode='{barcode}';")
        result = self.cur.fetchall()
        if not result:
            error("No product found for this barcode")
            return
        product_name = result[0][0]
        self.item_var.set(product_name)
        self.item_combobox.set(product_name)
        self.fill_labels(product_name)

    def start_scan_input(self):
        """Prepare barcode entry for scanner input."""
        self.barcode_entry.delete(0, tkinter.END)
        self.barcode_entry.focus_set()

    def remove_item(self):
        """ Removes selected item from the cart."""
        selected_item = self.tree.selection()

        if selected_item and messagebox.askyesno('Alert!', 'Do you want to remove this item?') == True:
            for i in selected_item:
                item = self.tree.item(i)
                self.tree.delete(i)

                values = item['values']

            p_id = values[0]
            qty = values[4]
            self.cur.execute(f"UPDATE products SET quantity = quantity + {qty} WHERE product_id = '{p_id}';")
            # Sync to default warehouse
            self.cur.execute(f"UPDATE warehouse_stock SET quantity = quantity + {qty} WHERE product_id = '{p_id}' AND warehouse_id = (SELECT warehouse_id FROM warehouses ORDER BY warehouse_id ASC LIMIT 1);")
            self.con.commit()
        self.total()

    def fill_labels(self, choice):
        """ Fills labels with data of a particular item chosen by user"""
        self.cur.execute(f"SELECT quantity, price  FROM products WHERE product_name='{choice}';")
        fetch = self.cur.fetchall()[0]
        self.available_qty = int(fetch[0])
        self.unit_price = float(fetch[1])
        value_x = 280
        try:
            self.price_label.place_forget()
            self.quantity_label.place_forget()
            self.qty_minus_btn.place_forget()
            self.qty_entry.place_forget()
            self.qty_plus_btn.place_forget()
        except:
            pass

        self.quantity_label = ctk.CTkLabel(self.win_frame, text=str(fetch[0]), font=(self.font, 20), anchor="w", width=220)
        self.quantity_label.place(x=value_x, y=130)
        self.price_label = ctk.CTkLabel(self.win_frame, text=f"{int(fetch[1]):,}", font=(self.font, 20), anchor="w", width=220)
        self.price_label.place(x=value_x, y=190)

        self.qty_var = ctk.StringVar(value="1")
        self.qty_minus_btn = ctk.CTkButton(self.win_frame, text="−", width=35, height=35,
                                           font=(self.font, 18), command=self._qty_decrement)
        self.qty_minus_btn.place(x=value_x, y=250)
        self.qty_entry = ctk.CTkEntry(self.win_frame, textvariable=self.qty_var, width=120, height=35,
                                      font=(self.font, 16), justify="center")
        self.qty_entry.place(x=value_x + 45, y=250)
        self.qty_plus_btn = ctk.CTkButton(self.win_frame, text="+", width=35, height=35,
                                          font=(self.font, 18), command=self._qty_increment)
        self.qty_plus_btn.place(x=value_x + 175, y=250)

    def _qty_decrement(self):
        try:
            val = int(self.qty_var.get())
        except ValueError:
            val = 1
        if val > 1:
            self.qty_var.set(str(val - 1))

    def _qty_increment(self):
        try:
            val = int(self.qty_var.get())
        except ValueError:
            val = 0
        if val < self.available_qty:
            self.qty_var.set(str(val + 1))

    def add_to_cart(self):
        """ Adds selected items to the shopping cart."""
        try:
            name = self.item_var.get()
            if name == '':
              error("Select an Item to add")
              return
            try:
                qty = int(self.qty_var.get())
            except ValueError:
                error('Enter a valid Quantity')
                return
            available = int(self.quantity_label.cget('text'))
            if qty <= 0 or available <= 0 or qty > available:
                error('Enter a valid Quantity')
                return
        except Exception:
            return
        self.cur.execute(f"SELECT product_id , description , price from products where product_name='{name}';")
        p_id , desc , price = self.cur.fetchall()[0]

        self.cur.execute(f"UPDATE products SET quantity = quantity - {qty} WHERE product_id = '{p_id}';")
        # Sync to default warehouse
        self.cur.execute(f"UPDATE warehouse_stock SET quantity = quantity - {qty} WHERE product_id = '{p_id}' AND warehouse_id = (SELECT warehouse_id FROM warehouses ORDER BY warehouse_id ASC LIMIT 1);")
        self.con.commit()
        self.fill_labels(name)

        amount = round(float(price) * qty, 2)
        items = [(p_id, name, desc, price ,qty, amount)]
        self.render_table(items=items)
        self.total()

    def total(self):
        """Evaluates the total amount in cart and displays it"""
        total = round(sum(float(self.tree.item(item, "values")[-1]) for item in self.tree.get_children()),2)
        try:
            self.total_label.place_forget()
        except:
            pass
        self.total_label = ctk.CTkLabel(self.frame, text=total, font=(self.font, 22))
        self.total_label.place(x=940,y=538)

    def add_button(self):
        """Creates a new window with entry fields to add a product to the inventory. """
        self.topwin = ctk.CTkToplevel(self.window)
        self.topwin.title("Add item to Inventory")
        self.topwin.geometry("500x560")
        frame = ctk.CTkFrame(master=self.topwin, width=450, height=530, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.product_entries = {}
        items = ['Product Id', 'Product Name', 'Description', 'Barcode', 'Price', 'Quantity']

        y = 50
        for i in items:
            label = ctk.CTkLabel(frame, text=i,font=(self.font, 14))
            label.place(x=50,y=y-25)
            entry = ctk.CTkEntry(master=frame, placeholder_text=i, width=350 , height=35)
            entry.place(x=50, y=y)
            self.product_entries[i] = entry
            y+=70

        button = ctk.CTkButton(master=frame, width=400, text="Add", corner_radius=6, command=self.add_product)
        button.place(x=25, y=470)

    def buy(self):
        """Function to buy items which are added to cart"""
        all_items = self.tree.get_children()
        if not all_items:
            error("No items available. Add items to cart to buy")
            return

        total_amount = round(sum(float(self.tree.item(item, "values")[-1]) for item in all_items), 2)

        # ── Payment Window ──
        pay_win = ctk.CTkToplevel(self.window)
        pay_win.title("Payment")
        pay_win.geometry("420x820")
        pay_win.resizable(False, False)
        pay_win.grab_set()

        # Main container
        container = ctk.CTkFrame(pay_win, fg_color="#0d1117", corner_radius=0)
        container.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkLabel(container, text="💳  Payment", font=(self.font, 24, "bold"),
                               text_color="#58a6ff")
        header.pack(pady=(20, 5))

        # Total amount display
        amount_frame = ctk.CTkFrame(container, fg_color="#161b22", corner_radius=12,
                                     border_width=1, border_color="#30363d")
        amount_frame.pack(padx=30, pady=(5, 15), fill="x")

        ctk.CTkLabel(amount_frame, text="Total Amount", font=(self.font, 13),
                      text_color="#8b949e").pack(pady=(12, 0))
        ctk.CTkLabel(amount_frame, text=f"{total_amount:,.0f} VND", font=(self.font, 28, "bold"),
                      text_color="#3fb950").pack(pady=(2, 12))

        # QR Code section
        qr_frame = ctk.CTkFrame(container, fg_color="#f6f8fa", corner_radius=12)
        qr_frame.pack(padx=30, pady=(0, 10))

        try:
            qr_path = ASSETS_DIR / "qr_payment.jpg"
            qr_img = Image.open(qr_path)
            # Resize proportionally to fit nicely
            qr_img = qr_img.resize((320, 380), Image.LANCZOS)
            qr_ctk = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(320, 380))
            qr_label = ctk.CTkLabel(qr_frame, image=qr_ctk, text="")
            qr_label.image = qr_ctk  # keep reference
            qr_label.pack(padx=10, pady=10)
        except Exception as e:
            ctk.CTkLabel(qr_frame, text="QR Code not found", font=(self.font, 14),
                          text_color="#ff5555").pack(padx=40, pady=40)
            print(f"[!] QR image load error: {e}")

        # Bank info
        info_frame = ctk.CTkFrame(container, fg_color="#161b22", corner_radius=10,
                                   border_width=1, border_color="#30363d")
        info_frame.pack(padx=30, pady=(0, 15), fill="x")

        bank_details = [
            ("Account Holder", "PHAM KHOI NGUYEN"),
            ("Account Number", "109882575681"),
            ("Bank", "VietinBank - CN DONG DA"),
        ]
        for label_text, value_text in bank_details:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=label_text, font=(self.font, 12),
                          text_color="#8b949e", anchor="w", width=130).pack(side="left")
            ctk.CTkLabel(row, text=value_text, font=(self.font, 12, "bold"),
                          text_color="#c9d1d9", anchor="e").pack(side="right")

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(padx=30, pady=(0, 20), fill="x")

        def place_order(status):
            pay_win.destroy()
            self._complete_order(status, all_items, total_amount)

        pay_btn = ctk.CTkButton(btn_frame, text="✅  Paid", font=(self.font, 16, "bold"),
                                 fg_color="#238636", hover_color="#2ea043", height=42,
                                 command=lambda: place_order("paid"))
        pay_btn.pack(fill="x", pady=(0, 8))

        pending_btn = ctk.CTkButton(btn_frame, text="⏳  Pay Later", font=(self.font, 16),
                                     fg_color="#30363d", hover_color="#484f58", height=42,
                                     command=lambda: place_order("pending"))
        pending_btn.pack(fill="x")

    def _complete_order(self, payment_status, all_items, total_amount):
        """Finalizes the order after payment decision."""
        try:
            query = 'select order_id from orders;'
            self.cur.execute(query)
            rows = self.cur.fetchall()
            count = self.cur.rowcount
            if count==0:
                order_id = 1001  #first account no is 1001
            else:
                order_id = rows[-1][0]+1

            query = 'select order_item_id from order_items;'
            self.cur.execute(query)
            rows = self.cur.fetchall()
            count = self.cur.rowcount
            if count==0:
                order_item_id = 1  #first account no is 1
            else:
                order_item_id = rows[-1][0] + 1

            # Insert into orders FIRST so order_id exists for order_items
            total_items = len(all_items)
            self.cur.execute(f"INSERT INTO orders (order_id, customer, date, total_items ,total_amount, payment_status) VALUES ({order_id}, '{self.user[0]}', '{date.today()}', {total_items},{total_amount}, '{payment_status}')")

            for item in all_items:
                values = self.tree.item(item, "values")
                product_id = values[0]
                quantity  = values[-2]
                price  = values[-1]
                self.cur.execute(f"INSERT INTO order_items (order_item_id ,order_id, product_id, quantity, price) VALUES ({order_item_id}, {order_id}, '{product_id}',{quantity}, {price})")
                order_item_id += 1

            self.con.commit()

            messagebox.showinfo("Success", "Order placed successfully.")
            self.tree.delete(*self.tree.get_children())
        except Exception as e:
            error(f"Failed to place order: {e}")


    def add_product(self):
        """Creates a new item in inventory by registering the provided details in MySQL. """
        p_id = self.product_entries['Product Id'].get()
        p_name = self.product_entries['Product Name'].get()
        p_desc = self.product_entries['Description'].get()
        p_barcode = self.product_entries['Barcode'].get().strip()
        p_price = self.product_entries['Price'].get()
        p_qty = self.product_entries['Quantity'].get()


        self.cur.execute(f"select * from products where product_id='{p_id}'")
        f = self.cur.fetchall()
        if f:
            error("Product Id already exist")
        else:
            if len(p_desc)>50:
                error("Description should be less than 50 letters")
                return
            if p_barcode != "":
                self.cur.execute(f"select * from products where barcode='{p_barcode}'")
                if self.cur.fetchall():
                    error("Barcode already exists")
                    return
            self.cur.execute(
                f"insert into products(product_id, product_name, description, barcode, price, quantity) "
                f"values('{p_id}','{p_name}','{p_desc}',"
                f"{'NULL' if p_barcode == '' else repr(p_barcode)},{p_price},{p_qty})"
            )
            # Add to default warehouse
            self.cur.execute(f"INSERT INTO warehouse_stock (warehouse_id, product_id, quantity) VALUES ((SELECT warehouse_id FROM warehouses ORDER BY warehouse_id ASC LIMIT 1), '{p_id}', {p_qty});")
            self.con.commit()
            messagebox.showinfo("Item Added!", "Item succesfully created!")
            self.topwin.destroy()
            self.tree.delete(*self.tree.get_children())
            self.render_table("products")

    def edit_button(self):
        selected = self.tree.selection()
        if not selected:
            error("Select a product to edit")
            return
            
        values = self.tree.item(selected[0], "values")
        
        self.topwin = ctk.CTkToplevel(self.window)
        self.topwin.title("Edit item")
        self.topwin.geometry("500x560")
        frame = ctk.CTkFrame(master=self.topwin, width=450, height=530, corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.product_entries = {}
        items = ['Product Id', 'Product Name', 'Description', 'Barcode', 'Price', 'Quantity']

        y = 50
        for idx, i in enumerate(items):
            label = ctk.CTkLabel(frame, text=i,font=(self.font, 14))
            label.place(x=50,y=y-25)
            entry = ctk.CTkEntry(master=frame, placeholder_text=i, width=350 , height=35)
            entry.place(x=50, y=y)
            if values[idx] and values[idx] != 'None':
                entry.insert(0, values[idx])
            
            # Disable Product ID and Quantity to prevent issues
            if i == 'Product Id' or i == 'Quantity':
                entry.configure(state='readonly')
                
            self.product_entries[i] = entry
            y+=70

        button = ctk.CTkButton(master=frame, width=400, text="Update", corner_radius=6, command=self.update_product)
        button.place(x=25, y=470)

    def update_product(self):
        p_id = self.product_entries['Product Id'].get().strip()
        p_name = self.product_entries['Product Name'].get().strip()
        p_desc = self.product_entries['Description'].get().strip()
        p_barcode = self.product_entries['Barcode'].get().strip()
        p_price = self.product_entries['Price'].get().strip()
        
        try:
            p_price = float(p_price)
        except ValueError:
            error("Price must be a valid number.")
            return

        try:
            self.cur.execute(
                f"UPDATE products SET product_name='{p_name}', description='{p_desc}', "
                f"barcode={'NULL' if p_barcode == '' else repr(p_barcode)}, price={p_price} "
                f"WHERE product_id='{p_id}'"
            )
            self.con.commit()
            messagebox.showinfo("Item Updated!", "Item successfully updated!")
            self.topwin.destroy()
            self.inventory()
        except Exception as e:
            error(f"Error updating item: {e}")
            
    
    def logout(self):
        self.login_win.destroy()
        self.logout = True

    def make_table(self, col, width, table=None, height=600):
        """Create a tkinter treeview table with specified columns, column widths, and optional data source table.

            Args:
                col (tuple): Tuple of column names.
                width (list): List of column widths.
                table (str, optional): Name of the table. Defaults to None.
                height (int, optional): Height of the table. Defaults to 600.
            """
        tableframe = ctk.CTkScrollableFrame(self.frame, width=1000,height=height)
        tableframe.place(x=1070, y=100, anchor=tkinter.NE )
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                            background="#2a2d2e",
                            foreground="white",
                            rowheight=25,
                            fieldbackground="#343638",
                            bordercolor="#343638",
                            borderwidth=0)
        style.map('Treeview', background=[('selected', '#007fff')])

        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat")
        style.map("Treeview.Heading",
                    background=[('active', '#3484F0')])
        self.tree = ttk.Treeview(tableframe, columns=col,
        selectmode="browse", height=100)

        for i, value in enumerate(col):
            if value == 'Description':
                w = 300
            else:
                w = 0 if i==0 else width
            self.tree.column(f'#{i}', stretch=tkinter.NO, minwidth=30, width=w)
            self.tree.heading(value, text=value, anchor=tkinter.W)

        self.tree.grid(row=1, column=0, sticky="W")
        self.tree.pack(fill="both", expand=True)
        if table:
            self.render_table(table)

    def render_table(self, table=None, items=None, query = None):
        """Render data from the database table into a Tkinter TreeView.
            Args:
                table (str, optional): Name of the table. Defaults to None.
                items (list, optional): items of the table. Defaults to None.
                query (list, optional): custom sql query. Defaults to None.
        """
        if query:
            self.cur.execute(query)
            items = self.cur.fetchall()

        if not items:
            self.cur.execute(f"SELECT * FROM {table};")
            items = self.cur.fetchall()
        for i in items:
            # Check if the item already exists in the TreeView (Table)
            existing_item = None
            for item in self.tree.get_children():
                if self.tree.item(item, 'values')[0] == i[0]:  # Assuming the first column is product_id
                    existing_item = item
                    break

            if existing_item:
                # Update the quantity of the existing item
                current_qty = int(self.tree.item(existing_item, 'values')[4])
                new_qty = current_qty + i[4]
                new_total = i[3] * new_qty  # price * qty
                self.tree.item(existing_item, values=(i[0], i[1], i[2], i[3], new_qty, new_total))
                self.total()

            else:
                # Insert a new row for the item
                self.tree.insert('', 'end', values=i)
