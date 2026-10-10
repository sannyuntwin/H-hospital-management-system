import tkinter as tk
from tkinter import ttk, messagebox
import database
from ui.utils import set_icon


class UsersPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="User Management", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="+ Add User", bg="#27ae60", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.open_form).pack(side="right")

        cols = ("ID", "Username", "Role")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("ID", width=50)
        self.tree.column("Username", width=250, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill="both", expand=True, padx=20, pady=5)
        scrollbar.pack(side="right", fill="y")

        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="Edit", bg="#2980b9", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.edit_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.delete_selected).pack(side="left", padx=5)

    def load_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users ORDER BY id")
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)

    def open_form(self, user=None):
        UserForm(self, user, on_save=self.load_users)

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to edit.")
            return
        values = self.tree.item(selected, "values")
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role FROM users WHERE id=?", (values[0],))
            user = cursor.fetchone()
        self.open_form(user)

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to delete.")
            return
        values = self.tree.item(selected, "values")
        if values[1] == "admin":
            messagebox.showerror("Not Allowed", "Cannot delete the admin account.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete user '{values[1]}'?"):
            with database.get_connection() as conn:
                conn.execute("DELETE FROM users WHERE id=?", (values[0],))
                conn.commit()
            self.load_users()


class UserForm(tk.Toplevel):
    def __init__(self, parent, user=None, on_save=None):
        super().__init__(parent)
        self.user = user  # (id, username, role) — no password shown on edit
        self.on_save = on_save
        self.title("Edit User" if user else "Add User")
        self.geometry("360x260")
        self.resizable(False, False)
        set_icon(self)
        self.grab_set()
        self._build_ui()
        if user:
            self._populate(user)

    def _build_ui(self):
        tk.Label(self, text="Username:", anchor="e", width=14).grid(
            row=0, column=0, padx=10, pady=12, sticky="e")
        self.username_var = tk.StringVar()
        tk.Entry(self, textvariable=self.username_var, width=25).grid(
            row=0, column=1, padx=10)

        tk.Label(self, text="Password:", anchor="e", width=14).grid(
            row=1, column=0, padx=10, pady=12, sticky="e")
        self.password_var = tk.StringVar()
        tk.Entry(self, textvariable=self.password_var, show="*", width=25).grid(
            row=1, column=1, padx=10)
        if self.user:
            tk.Label(self, text="Leave blank to keep current",
                     font=("Arial", 8), fg="gray").grid(row=2, column=1, sticky="w", padx=10)

        tk.Label(self, text="Role:", anchor="e", width=14).grid(
            row=3, column=0, padx=10, pady=12, sticky="e")
        self.role_var = tk.StringVar(value="receptionist")
        ttk.Combobox(self, textvariable=self.role_var,
                     values=["admin", "receptionist"],
                     state="readonly", width=23).grid(row=3, column=1, padx=10)

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  padx=20, pady=5, command=self.save).grid(
                  row=4, column=0, columnspan=2, pady=15)

    def _populate(self, user):
        self.username_var.set(user[1])
        self.role_var.set(user[2])

    def save(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        role     = self.role_var.get()

        if not username:
            messagebox.showwarning("Required", "Username is required.", parent=self)
            return
        if not self.user and not password:
            messagebox.showwarning("Required", "Password is required for new users.", parent=self)
            return
        if password and len(password) < 6:
            messagebox.showwarning("Too Short", "Password must be at least 6 characters.", parent=self)
            return

        with database.get_connection() as conn:
            if self.user:
                if password:
                    conn.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
                                 (username, password, role, self.user[0]))
                else:
                    conn.execute("UPDATE users SET username=?, role=? WHERE id=?",
                                 (username, role, self.user[0]))
            else:
                try:
                    conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                                 (username, password, role))
                except Exception:
                    messagebox.showerror("Duplicate", "Username already exists.", parent=self)
                    return
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
