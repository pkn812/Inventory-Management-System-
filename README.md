# Enterprise Inventory Management System

A comprehensive, GUI-based Inventory Management System built with Python, CustomTkinter, and MySQL. This application provides robust tools for managing products, tracking orders, analyzing sales trends, and handling supply chain logistics in an enterprise environment.

## Features

- **Modern GUI Dashboard**: Built with `customtkinter` for a responsive and visually appealing dark-themed interface.
- **Role-Based Access Control (RBAC)**: Secure login system with Admin, Manager, and Read-only roles, including password hashing (SHA-256) and audit logging.
- **Advanced Data Visualization**: Built-in `matplotlib` charts for monthly earnings, top products, order status, and individual product sales trends.
- **Predictive Restocking**: Automatically calculates sales velocity, days-until-stockout, and suggests reorder quantities based on historical data.
- **Supply Chain Management**: Track suppliers, manage multiple warehouses, and handle purchase orders with delivery time tracking.
- **Point of Sale (POS) features**: Process customer orders, manage payment statuses, and generate QR codes for fast payments.
- **ERP Integration**: Export data to CSV or generate structured JSON payloads for external ERP synchronization.

## Prerequisites

- Python 3.8+
- MySQL Server 8.0+

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/abidzzz/inventory-gui.git
   cd inventory-gui-main
   ```

2. **Install required dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install customtkinter matplotlib mysql-connector-python Pillow
   ```

3. **Database Setup:**
   Ensure your MySQL server is running. The application will automatically create the `inventory` database and necessary tables, indexes, and stored procedures upon the first run.
   
   To populate the database with sample data, you can run:
   ```bash
   python load_sample_data.py
   ```

4. **Configuration:**
   Update your MySQL credentials in `main.py` (around line 10) to match your local MySQL server setup:
   ```python
   self.con = mycon.connect(host='localhost', user='root', passwd='YourPassword')
   ```

## Usage

1. **Run the application:**
   ```bash
   python main.py
   ```

2. **Default Login:**
   - You can create an initial account directly in the database or use existing credentials if the sample data was loaded. (By default, you may use `ADMIN` / `ADMIN` if legacy accounts exist).

## Screenshots

<img src="screenshots/0.png" width="400"> <img src="screenshots/01.png" width="400">

<details>
  <summary>View more</summary>
  <br>
  <p align="left">
    <img src="screenshots/Screenshot (62).png" width="400">
    <img src="screenshots/Screenshot (63).png" width="400">
    <img src="screenshots/Screenshot (64).png" width="400">
    <img src="screenshots/Screenshot (65).png" width="400">
    <img src="screenshots/Screenshot (66).png" width="400">
    <img src="screenshots/Screenshot (67).png" width="400">
  </p>
</details>

## Database Architecture
The application uses a relational schema containing tables for:
- `users` (Authentication, Roles, and Passwords)
- `products` (Inventory items, descriptions, quantities, and barcodes)
- `orders` & `order_items` (Customer transactions)
- `suppliers`, `warehouses`, `warehouse_stock` (Supply chain entities and tracking)
- `purchase_orders` & `po_items` (Restocking orders and history)

## Notes

- The graphical analytics will only render if there are matching transactions in the database. If graphs do not appear, try completing a purchase order or loading sample data.
- Ensure `mysql-connector-python` is installed, as `mysql-connector` is deprecated and may cause connection issues.

## License

This project is licensed under the [MIT License](LICENSE).
