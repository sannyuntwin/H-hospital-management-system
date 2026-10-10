import tkinter as tk
from tkinter import messagebox
import database

class SettingsPage(tk.Frame):
    def __init__(self, parent, user=None):
        super().__init__(parent, bg="#ecf0f1")
        self.user = user  # (id, username, password, role)
        self._build_ui()
        self.load_settings()

    def _build_ui(self):
        tk.Label(self, text="Hospital Settings", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(anchor="w", padx=25, pady=(20, 5))
        tk.Label(self, text="These details appear on printed invoices.",
                 bg="#ecf0f1", fg="#7f8c8d", font=("Arial", 9)).pack(anchor="w", padx=25)

        form = tk.Frame(self, bg="#ecf0f1")
        form.pack(padx=40, pady=20, anchor="w")

        self.vars = {}

        fields = [
            ("Hospital Name",  "hospital_name"),
            ("Address",        "address"),
            ("Phone",          "phone"),
            ("Email",          "email"),
        ]

        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label + ":", anchor="e", width=16,
                     bg="#ecf0f1", font=("Arial", 10)).grid(
                     row=i, column=0, pady=10, padx=10, sticky="e")
            var = tk.StringVar()
            self.vars[key] = var
            tk.Entry(form, textvariable=var, width=40,
                     font=("Arial", 10)).grid(row=i, column=1, padx=10)

        # Footer note — multiline
        tk.Label(form, text="Footer Note:", anchor="e", width=16,
                 bg="#ecf0f1", font=("Arial", 10)).grid(
                 row=len(fields), column=0, pady=10, padx=10, sticky="ne")
        self.footer_text = tk.Text(form, width=38, height=3, font=("Arial", 10))
        self.footer_text.grid(row=len(fields), column=1, padx=10, pady=10)

        tk.Button(form, text="Save Settings", bg="#27ae60", fg="white",
                  font=("Arial", 11), relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self.save_settings).grid(
                  row=len(fields)+1, column=1, sticky="e", pady=10, padx=10)

        # ── Change Password ──────────────────────────────
        tk.Label(self, text="Change Password", font=("Arial", 13, "bold"),
                 bg="#ecf0f1").pack(anchor="w", padx=25, pady=(10, 5))

        pw_form = tk.Frame(self, bg="#ecf0f1")
        pw_form.pack(padx=40, anchor="w")

        pw_fields = [
            ("Current Password",  "current_pw"),
            ("New Password",      "new_pw"),
            ("Confirm Password",  "confirm_pw"),
        ]
        self.pw_vars = {}
        for i, (label, key) in enumerate(pw_fields):
            tk.Label(pw_form, text=label + ":", anchor="e", width=16,
                     bg="#ecf0f1", font=("Arial", 10)).grid(
                     row=i, column=0, pady=8, padx=10, sticky="e")
            var = tk.StringVar()
            self.pw_vars[key] = var
            tk.Entry(pw_form, textvariable=var, show="*", width=30,
                     font=("Arial", 10)).grid(row=i, column=1, padx=10)

        tk.Button(pw_form, text="Change Password", bg="#2980b9", fg="white",
                  font=("Arial", 11), relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self.change_password).grid(
                  row=len(pw_fields), column=1, sticky="e", pady=10, padx=10)

    def load_settings(self):
        with database.get_connection() as conn:
            cursor = conn.cursor()
            for key, var in self.vars.items():
                cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
                row = cursor.fetchone()
                var.set(row[0] if row else "")

            cursor.execute("SELECT value FROM settings WHERE key='footer_note'")
            row = cursor.fetchone()
            self.footer_text.delete("1.0", "end")
            if row:
                self.footer_text.insert("1.0", row[0])

    def save_settings(self):
        with database.get_connection() as conn:
            for key, var in self.vars.items():
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    (key, var.get().strip())
                )
            footer = self.footer_text.get("1.0", "end").strip()
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("footer_note", footer)
            )
            conn.commit()

        messagebox.showinfo("Saved", "Settings saved successfully.")

    def change_password(self):
        current = self.pw_vars["current_pw"].get()
        new_pw  = self.pw_vars["new_pw"].get()
        confirm = self.pw_vars["confirm_pw"].get()

        if not all([current, new_pw, confirm]):
            messagebox.showwarning("Required", "All password fields are required.", parent=self)
            return
        if len(new_pw) < 6:
            messagebox.showwarning("Too Short", "New password must be at least 6 characters.", parent=self)
            return
        if new_pw != confirm:
            messagebox.showerror("Mismatch", "New password and confirm password do not match.", parent=self)
            return

        username = self.user[1] if self.user else "admin"
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, current))
            if not cursor.fetchone():
                messagebox.showerror("Wrong Password", "Current password is incorrect.", parent=self)
                return
            conn.execute("UPDATE users SET password=? WHERE username=?", (new_pw, username))
            conn.commit()

        for var in self.pw_vars.values():
            var.set("")
        messagebox.showinfo("Done", "Password changed successfully.")
