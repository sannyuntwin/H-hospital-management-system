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
        self.title("H-Hospital")
        self.geometry("420x480")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.configure(bg="#1a252f")

        icon_path = os.path.join(_get_base_dir(), "assets", "h-hospital.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 210
        y = (self.winfo_screenheight() // 2) - 240
        self.geometry(f"420x480+{x}+{y}")

        self._load_logo()
        self._build_ui()

    def _load_logo(self):
        self._logo_img = None
        logo_path = os.path.join(_get_base_dir(), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = tk.PhotoImage(file=logo_path)
                self._logo_img = img.subsample(max(1, img.height() // 64))
            except Exception:
                self._logo_img = None

    def _build_ui(self):
        # ── Outer padding frame on dark background ───────────
        outer = tk.Frame(self, bg="#1a252f")
        outer.pack(fill="both", expand=True, padx=35, pady=35)

        # ── White card ────────────────────────────────────────
        card = tk.Frame(outer, bg="white")
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=30, pady=28)

        # Logo
        if self._logo_img:
            tk.Label(inner, image=self._logo_img, bg="white").pack(pady=(0, 6))

        # Title
        tk.Label(inner, text="H-Hospital", font=("Arial", 20, "bold"),
                 bg="white", fg="#2c3e50").pack()
        tk.Label(inner, text="Management System", font=("Arial", 10),
                 bg="white", fg="#95a5a6").pack(pady=(2, 20))

        # Thin divider
        tk.Frame(inner, bg="#ecf0f1", height=1).pack(fill="x", pady=(0, 18))

        # ── Username ──────────────────────────────────────────
        tk.Label(inner, text="Username", font=("Arial", 9, "bold"),
                 bg="white", fg="#2c3e50", anchor="w").pack(fill="x")
        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            inner, textvariable=self.username_var,
            font=("Arial", 11), relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#d5d8dc",
            highlightcolor="#2980b9"
        )
        self.username_entry.pack(fill="x", ipady=7, pady=(4, 14))

        # ── Password ──────────────────────────────────────────
        tk.Label(inner, text="Password", font=("Arial", 9, "bold"),
                 bg="white", fg="#2c3e50", anchor="w").pack(fill="x")

        pw_wrap = tk.Frame(inner, bg="white")
        pw_wrap.pack(fill="x", pady=(4, 22))

        self.password_var = tk.StringVar()
        self._pw_visible = False
        self.pw_entry = tk.Entry(
            pw_wrap, textvariable=self.password_var, show="*",
            font=("Arial", 11), relief="solid", bd=1,
            highlightthickness=1, highlightbackground="#d5d8dc",
            highlightcolor="#2980b9"
        )
        self.pw_entry.pack(side="left", fill="x", expand=True, ipady=7)

        self.eye_btn = tk.Button(
            pw_wrap, text="👁", bg="white", relief="flat",
            font=("Arial", 11), cursor="hand2", bd=0,
            activebackground="white", fg="#7f8c8d",
            command=self._toggle_pw
        )
        self.eye_btn.pack(side="left", padx=(4, 0))

        # ── Login button ──────────────────────────────────────
        tk.Button(
            inner, text="Login", bg="#2c3e50", fg="white",
            font=("Arial", 12, "bold"), relief="flat",
            cursor="hand2", pady=10, activebackground="#1a252f",
            activeforeground="white", command=self.login
        ).pack(fill="x")

        self.bind("<Return>", lambda e: self.login())
        self.username_entry.focus_set()

    def _toggle_pw(self):
        self._pw_visible = not self._pw_visible
        self.pw_entry.config(show="" if self._pw_visible else "*")
        self.eye_btn.config(fg="#2980b9" if self._pw_visible else "#7f8c8d")

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter username and password.", parent=self)
            return

        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                           (username, password))
            user = cursor.fetchone()

        if user:
            self.destroy()
            from ui.dashboard import Dashboard
            Dashboard(self.parent, user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.", parent=self)
            self.password_var.set("")
            self.pw_entry.focus_set()

    def on_close(self):
        self.parent.destroy()
