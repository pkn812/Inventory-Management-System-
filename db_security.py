"""
db_security.py  –  Database Security & Administration
=====================================================
Manages MySQL user roles, access permissions, password hashing,
SQL injection prevention helpers, and backup/restore operations.
"""

import hashlib
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(__file__).resolve().parent / "backups"


# ═══════════════════════════════════════════════════════════════════════
#  PASSWORD HASHING  –  SHA-256 with per-user salt
# ═══════════════════════════════════════════════════════════════════════

def hash_password(password: str, salt: str = None) -> tuple:
    """Hash a password with a random salt.  Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return hashed, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against its stored hash and salt."""
    computed, _ = hash_password(password, salt)
    return computed == stored_hash


# ═══════════════════════════════════════════════════════════════════════
#  MYSQL USER ROLES & PERMISSIONS
# ═══════════════════════════════════════════════════════════════════════

def create_database_roles(cur, db_name="inventory"):
    """Create MySQL users with role-based access control.

    Roles created:
        inv_admin    – Full access (ALL PRIVILEGES)
        inv_manager  – INSERT, UPDATE, SELECT, DELETE on products/orders/order_items
        inv_readonly – SELECT only on all tables
    """

    roles = [
        {
            "user": "inv_admin",
            "password": "Admin@Secure2026",
            "privileges": f"ALL PRIVILEGES ON {db_name}.*",
            "description": "Full administrative access"
        },
        {
            "user": "inv_manager",
            "password": "Manager@Secure2026",
            "privileges": (
                f"SELECT, INSERT, UPDATE ON {db_name}.products, "
                f"SELECT, INSERT, UPDATE ON {db_name}.orders, "
                f"SELECT, INSERT, UPDATE ON {db_name}.order_items, "
                f"SELECT ON {db_name}.users, "
                f"SELECT ON {db_name}.inventory_log, "
                f"SELECT ON {db_name}.vw_stock_summary, "
                f"SELECT ON {db_name}.vw_monthly_earnings, "
                f"SELECT ON {db_name}.vw_order_history, "
                f"SELECT ON {db_name}.vw_product_sales"
            ),
            "description": "Inventory manager – read/write products & orders"
        },
        {
            "user": "inv_readonly",
            "password": "ReadOnly@Secure2026",
            "privileges": f"SELECT ON {db_name}.*",
            "description": "Read-only access for reporting"
        },
    ]

    for role in roles:
        user = role["user"]
        pwd = role["password"]
        try:
            cur.execute(f"CREATE USER IF NOT EXISTS '{user}'@'localhost' IDENTIFIED BY '{pwd}';")
        except Exception:
            # User already exists – reset password
            try:
                cur.execute(f"ALTER USER '{user}'@'localhost' IDENTIFIED BY '{pwd}';")
            except Exception:
                pass

        # Revoke existing and re-grant to ensure consistency
        try:
            cur.execute(f"REVOKE ALL PRIVILEGES, GRANT OPTION FROM '{user}'@'localhost';")
        except Exception:
            pass

        # Grant privileges (handle multi-table grants individually)
        if user == "inv_manager":
            grants = [
                f"GRANT SELECT, INSERT, UPDATE ON {db_name}.products TO '{user}'@'localhost'",
                f"GRANT SELECT, INSERT, UPDATE ON {db_name}.orders TO '{user}'@'localhost'",
                f"GRANT SELECT, INSERT, UPDATE ON {db_name}.order_items TO '{user}'@'localhost'",
                f"GRANT SELECT ON {db_name}.users TO '{user}'@'localhost'",
                f"GRANT SELECT, INSERT ON {db_name}.inventory_log TO '{user}'@'localhost'",
                f"GRANT EXECUTE ON PROCEDURE {db_name}.sp_restock_product TO '{user}'@'localhost'",
                f"GRANT EXECUTE ON PROCEDURE {db_name}.sp_low_stock_report TO '{user}'@'localhost'",
                f"GRANT EXECUTE ON PROCEDURE {db_name}.sp_calculate_inventory_value TO '{user}'@'localhost'",
                f"GRANT EXECUTE ON FUNCTION {db_name}.fn_avg_daily_sales TO '{user}'@'localhost'",
                f"GRANT EXECUTE ON FUNCTION {db_name}.fn_days_until_stockout TO '{user}'@'localhost'",
                f"GRANT EXECUTE ON FUNCTION {db_name}.fn_stock_turnover_rate TO '{user}'@'localhost'",
            ]
            for grant in grants:
                try:
                    cur.execute(grant + ";")
                except Exception as e:
                    print(f"  [!] Grant skipped: {e}")
        else:
            try:
                cur.execute(f"GRANT {role['privileges']} TO '{user}'@'localhost';")
            except Exception as e:
                print(f"  [!] Grant failed for {user}: {e}")

        try:
            cur.execute("FLUSH PRIVILEGES;")
        except Exception:
            pass

        print(f"  [+] Role '{user}' configured – {role['description']}")


# ═══════════════════════════════════════════════════════════════════════
#  SECURITY HARDENING  –  Encrypted columns, audit controls
# ═══════════════════════════════════════════════════════════════════════

def setup_security_tables(cur):
    """Add security-related columns and tables."""

    # Add salt column to users table for hashed passwords
    try:
        cur.execute("SHOW COLUMNS FROM users LIKE 'salt';")
        if not cur.fetchall():
            cur.execute("ALTER TABLE users ADD COLUMN salt VARCHAR(64) DEFAULT NULL;")
            print("  [+] Added salt column to users table")
    except Exception as e:
        print(f"  [!] Salt column setup: {e}")

    # Create login_audit table to track login attempts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_audit (
            audit_id    INT AUTO_INCREMENT PRIMARY KEY,
            username    VARCHAR(20),
            login_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address  VARCHAR(45) DEFAULT 'localhost',
            success     BOOLEAN NOT NULL,
            notes       VARCHAR(255)
        );
    """)
    print("  [+] Login audit table ready")

    # Create a data access log for sensitive queries
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_access_log (
            log_id      INT AUTO_INCREMENT PRIMARY KEY,
            username    VARCHAR(20),
            action      VARCHAR(50),
            table_name  VARCHAR(50),
            record_id   VARCHAR(50),
            access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  [+] Data access log table ready")


def migrate_passwords_to_hashed(cur, con):
    """Migrate existing plaintext passwords to hashed passwords.
    Only runs once – skips users that already have a salt."""
    try:
        cur.execute("SELECT username, password, salt FROM users WHERE salt IS NULL;")
        users = cur.fetchall()
        for username, plain_pwd, _ in users:
            hashed, salt = hash_password(plain_pwd)
            cur.execute(
                "UPDATE users SET password = %s, salt = %s WHERE username = %s;",
                (hashed, salt, username)
            )
        if users:
            con.commit()
            print(f"  [+] Migrated {len(users)} user passwords to hashed format")
    except Exception as e:
        print(f"  [!] Password migration: {e}")


# ═══════════════════════════════════════════════════════════════════════
#  PARAMETERIZED QUERY HELPERS  –  SQL injection prevention
# ═══════════════════════════════════════════════════════════════════════

def safe_query(cur, query, params=None):
    """Execute a parameterized query safely."""
    cur.execute(query, params or ())
    return cur


def safe_fetchall(cur, query, params=None):
    """Execute a parameterized query and return all results."""
    cur.execute(query, params or ())
    return cur.fetchall()


def safe_fetchone(cur, query, params=None):
    """Execute a parameterized query and return one result."""
    cur.execute(query, params or ())
    return cur.fetchone()


# ═══════════════════════════════════════════════════════════════════════
#  BACKUP & RECOVERY
# ═══════════════════════════════════════════════════════════════════════

def find_mysqldump():
    """Locate the mysqldump executable."""
    # Check PATH first
    mysqldump = shutil.which("mysqldump")
    if mysqldump:
        return mysqldump

    # Common Windows locations
    common_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe",
        r"C:\xampp\mysql\bin\mysqldump.exe",
        r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysqldump.exe",
    ]
    for p in common_paths:
        if Path(p).exists():
            return p

    return None


def find_mysql():
    """Locate the mysql client executable."""
    mysql = shutil.which("mysql")
    if mysql:
        return mysql

    common_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
        r"C:\xampp\mysql\bin\mysql.exe",
        r"C:\wamp64\bin\mysql\mysql8.0.31\bin\mysql.exe",
    ]
    for p in common_paths:
        if Path(p).exists():
            return p

    return None


def backup_database(host="localhost", user="root", password="",
                    db_name="inventory", backup_dir=None):
    """Create a full SQL dump backup of the database.

    Returns the path to the backup file or raises an exception.
    """
    mysqldump = find_mysqldump()
    if not mysqldump:
        raise FileNotFoundError(
            "mysqldump not found. Install MySQL or add it to PATH."
        )

    if backup_dir is None:
        backup_dir = BACKUP_DIR
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{db_name}_backup_{timestamp}.sql"
    filepath = backup_dir / filename

    cmd = [
        mysqldump,
        f"--host={host}",
        f"--user={user}",
        f"--password={password}",
        "--routines",           # Include stored procedures & functions
        "--triggers",           # Include triggers
        "--single-transaction", # Consistent snapshot without locking
        "--add-drop-table",
        db_name,
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"mysqldump failed: {result.stderr}")

    size_kb = filepath.stat().st_size / 1024
    print(f"  [+] Backup created: {filepath} ({size_kb:.1f} KB)")
    return str(filepath)


def restore_database(backup_path, host="localhost", user="root",
                     password="", db_name="inventory"):
    """Restore a database from a SQL dump file.

    WARNING: This will overwrite existing data in the target database.
    """
    mysql_bin = find_mysql()
    if not mysql_bin:
        raise FileNotFoundError(
            "mysql client not found. Install MySQL or add it to PATH."
        )

    if not Path(backup_path).exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    cmd = [
        mysql_bin,
        f"--host={host}",
        f"--user={user}",
        f"--password={password}",
        db_name,
    ]

    with open(backup_path, "r", encoding="utf-8") as f:
        result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Restore failed: {result.stderr}")

    print(f"  [+] Database restored from: {backup_path}")
    return True


def list_backups(backup_dir=None):
    """List all available backup files, newest first."""
    if backup_dir is None:
        backup_dir = BACKUP_DIR
    backup_dir = Path(backup_dir)

    if not backup_dir.exists():
        return []

    backups = sorted(
        backup_dir.glob("*.sql"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return [str(b) for b in backups]


def cleanup_old_backups(keep=5, backup_dir=None):
    """Remove old backups, keeping only the most recent ones."""
    all_backups = list_backups(backup_dir)
    removed = 0
    for old in all_backups[keep:]:
        Path(old).unlink()
        removed += 1
    if removed:
        print(f"  [+] Cleaned up {removed} old backup(s)")
    return removed


# ═══════════════════════════════════════════════════════════════════════
#  QUERY OPTIMIZATION  –  EXPLAIN helpers
# ═══════════════════════════════════════════════════════════════════════

def explain_query(cur, query, params=None):
    """Run EXPLAIN on a query and return the execution plan."""
    cur.execute(f"EXPLAIN {query}", params or ())
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    return [dict(zip(columns, row)) for row in rows]


def show_index_usage(cur, db_name="inventory"):
    """Show index usage statistics for all tables."""
    cur.execute(f"""
        SELECT TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME,
               CARDINALITY, INDEX_TYPE
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = '{db_name}'
        ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
    """)
    return cur.fetchall()


# ═══════════════════════════════════════════════════════════════════════
#  MASTER SETUP  –  Called from main.py
# ═══════════════════════════════════════════════════════════════════════

def setup_security(cur, con, db_name="inventory"):
    """Run all security setup steps."""
    print("[*] Setting up database security...")
    setup_security_tables(cur)
    con.commit()

    try:
        create_database_roles(cur, db_name)
    except Exception as e:
        print(f"  [!] Role creation requires root privileges: {e}")

    migrate_passwords_to_hashed(cur, con)
    print("[*] Database security setup complete")
