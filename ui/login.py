import os
import sys
import tkinter as tk
from tkinter import messagebox
import database

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("H-Hospital Management System")
        self.geometry("420x320")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.configure(bg="white")

        icon_path = os.path.join(_get_base_dir(), "assets", "h-hospital.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 210
        y = (self.winfo_screenheight() // 2) - 160
        self.geometry(f"420x320+{x}+{y}")

        self._load_logo()
        self._build_ui()

    def _load_logo(self):
        self._logo_img = None
        logo_path = os.path.join(_get_base_dir(), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = tk.PhotoImage(file=logo_path)
                # Shrink to ~48px tall — adjust subsample number if logo looks too big/small
                self._logo_img = img.subsample(max(1, img.height() // 48))
            except Exception:
                self._logo_img = None

    def _build_ui(self):
        # ── Logo + Title header ──────────────────────────────
        header = tk.Frame(self, bg="white")
        header.pack(pady=(25, 10))

        if self._logo_img:
            tk.Label(header, image=self._logo_img, bg="white").pack(side="left", padx=(0, 10))

        tk.Label(header, text="H-Hospital Management System",
                 font=("Arial", 15, "bold"), bg="white").pack(side="left")

        # ── Login form ───────────────────────────────────────
        frame = tk.Frame(self, bg="white")
        frame.pack(pady=10)

        tk.Label(frame, text="Username:", width=10, anchor="e", bg="white").grid(
            row=0, column=0, pady=8, padx=5)
        self.username_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.username_var, width=25).grid(row=0, column=1)

        tk.Label(frame, text="Password:", width=10, anchor="e", bg="white").grid(
            row=1, column=0, pady=8, padx=5)
        self.password_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.password_var, show="*", width=25).grid(row=1, column=1)

        self.bind("<Return>", lambda e: self.login())

        tk.Button(self, text="Login", width=15, bg="#2c3e50", fg="white",
                  relief="flat", pady=6, cursor="hand2",
                  command=self.login).pack(pady=20)

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter username and password.")
            return

        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()

        if user:
            self.destroy()
            from ui.dashboard import Dashboard
            Dashboard(self.parent, user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def on_close(self):
        self.parent.destroy()
