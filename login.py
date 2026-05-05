import tkinter 
from tkinter import messagebox
from pathlib import Path
import customtkinter as ctk
from PIL import Image

from utils import error 
from db_security import hash_password, verify_password

ASSETS_DIR = Path(__file__).resolve().parent / "imgs"

class Login:
    """Represents a login window for user authentication."""
    def __init__(self, con):
        ctk.set_default_color_theme("dark-blue")
        ctk.set_appearance_mode("dark")
        self.window =  ctk.CTk() 
        self.window.title("Sign In")
        self.window.geometry("500x600")
        self.con = con
        self.cur = con.cursor()
        self.user = None
        self.login_window()

    def login_window(self, event=None):
        """ Function to create login window."""
        self.window.title("Sign In")
        self.window.bind('<Return>', self.login)
        
        img_path = ASSETS_DIR / "bg.jpg"
        img = ctk.CTkImage(dark_image=Image.open(img_path).resize((500, 600)), size=(500, 600))
        bg = ctk.CTkLabel(master=self.window,image=img)
        bg.place(x=0,y=0)

        self.frame = ctk.CTkFrame(master=bg, width=320, height=360, corner_radius=15)
        self.frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        self.login_label = ctk.CTkLabel(master=self.frame, text="Log in", font=('Century Gothic',30))
        self.login_label.place(x=100, y=45)

        self.username = ctk.CTkEntry(master=self.frame, width=220, placeholder_text='Username')
        self.username.place(x=50, y=110)

        self.password = ctk.CTkEntry(master=self.frame, width=220, placeholder_text='Password', show="*")
        self.password.place(x=50, y=165)

        self.label_link = ctk.CTkLabel(master=self.frame, text="Don't have an account? Register",font=('Century Gothic',13))
        self.label_link.place(x=60,y=210)
        self.label_link.bind("<Button-1>", self.register_window)

        # Create Login button
        button = ctk.CTkButton(master=self.frame, width=220, text="Login", command=self.login, corner_radius=6)
        button.place(x=50, y=250)

    def register_window(self, event=None):
        """ Function to display register window."""
        self.window.title("Create an account")
        self.window.bind('<Return>',self.register)
        self.login_label.configure(text="Register")
        self.label_link.configure(text="Already have an Account? Sign in")
        self.label_link.bind("<Button-1>", self.login_window)
        button = ctk.CTkButton(master=self.frame, width=220, text="Continue", command=self.register, corner_radius=6)
        button.place(x=50, y=250)
        

    def _log_login_attempt(self, username, success, notes=""):
        """Record login attempt to the login_audit table."""
        try:
            self.cur.execute(
                "INSERT INTO login_audit (username, success, notes) VALUES (%s, %s, %s);",
                (username, success, notes)
            )
            self.con.commit()
        except Exception:
            pass

    def login(self, event=None):
        """Authenticate the user by checking the provided username and password with MySQL. """
        uname = self.username.get()
        pwd = self.password.get()
        # Ensure default admin credentials always exist and stay valid.
        # Hash the default admin password
        admin_hash, admin_salt = hash_password("ADMIN", "ADMIN_FIXED_SALT")
        self.cur.execute(
            "INSERT INTO users (username, password, account_type, salt) "
            "VALUES (%s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE password=%s, account_type='ADMIN', salt=%s;",
            ("ADMIN", admin_hash, "ADMIN", admin_salt, admin_hash, admin_salt)
        )
        self.con.commit()

        # Use parameterized query to prevent SQL injection
        self.cur.execute(
            "SELECT username, password, account_type, salt FROM users WHERE username = %s;",
            (uname,)
        )
        f = self.cur.fetchall()
        if f:
            stored_user = f[0]
            stored_hash = stored_user[1]
            stored_salt = stored_user[3]

            if stored_salt and verify_password(pwd, stored_hash, stored_salt):
                # Hashed password match
                print("Logged in as {}".format(uname))
                self._log_login_attempt(uname, True, "Successful login")
                self.window.quit()
                self.user = (stored_user[0], stored_user[1], stored_user[2])
            elif not stored_salt and stored_hash == pwd:
                # Legacy plaintext password (pre-migration) — accept and migrate
                print("Logged in as {} (legacy password)".format(uname))
                new_hash, new_salt = hash_password(pwd)
                self.cur.execute(
                    "UPDATE users SET password = %s, salt = %s WHERE username = %s;",
                    (new_hash, new_salt, uname)
                )
                self.con.commit()
                self._log_login_attempt(uname, True, "Legacy login + password migrated")
                self.window.quit()
                self.user = (stored_user[0], stored_user[1], stored_user[2])
            else:
                self._log_login_attempt(uname, False, "Invalid password")
                error("Invalid Username or Password")
        else:
            self._log_login_attempt(uname, False, "Username not found")
            error("Invalid Username or Password")

    def register(self):
        """Create a new user account by registering the provided username and password in MySQL. """
        uname = self.username.get()
        pwd = self.password.get()
        
        # Use parameterized query to prevent SQL injection
        self.cur.execute("SELECT * FROM users WHERE username = %s;", (uname,))
        f = self.cur.fetchall()
        if f:
            error("Username already exist")

        else:    
            if(len(uname) == 0 or len(pwd) == 0):
                error("Length of the Username and Password should be greater than 0")
                return
            elif len(uname)>20 or len(pwd)>20 :
                error("Length of the Username and Password should be less than 20")
                return
            
            # Hash the password before storing
            hashed, salt = hash_password(pwd)
            self.cur.execute(
                "INSERT INTO users (username, password, account_type, salt) VALUES (%s, %s, %s, %s);",
                (uname, hashed, "USER", salt)
            )
            self.con.commit()
            self._log_login_attempt(uname, True, "Account registered")
            messagebox.showinfo("Account created", "Your account has been succesfully created!")
            self.window.quit()
            self.user = (uname, hashed, 'USER')