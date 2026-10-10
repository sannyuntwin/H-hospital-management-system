import tkinter as tk
from tkinter import ttk, messagebox
import database
from ui.utils import set_icon

class DoctorsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_doctors()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="Doctor Management", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="+ Add Doctor", bg="#27ae60", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.open_form).pack(side="right")

        # ── Search ───────────────────────────────────────
        search_frame = tk.Frame(self, bg="#ecf0f1")
        search_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(search_frame, text="Search:", bg="#ecf0f1").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.load_doctors())
        tk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=8)

        # ── Table ────────────────────────────────────────
        cols = ("ID", "Name", "Specialization", "Phone", "Email")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("ID", width=50)
        self.tree.column("Name", width=180, anchor="w")
        self.tree.column("Email", width=200, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, padx=20, pady=5)
        scrollbar.pack(side="right", fill="y")

        # ── Action Buttons ───────────────────────────────
        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="Edit", bg="#2980b9", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.edit_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.delete_selected).pack(side="left", padx=5)

    def load_doctors(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self.search_var.get().strip()
        with database.get_connection() as conn:
            cursor = conn.cursor()
            if search:
                cursor.execute(
                    "SELECT id, name, specialization, phone, email FROM doctors WHERE name LIKE ?",
                    (f"%{search}%",)
                )
            else:
                cursor.execute("SELECT id, name, specialization, phone, email FROM doctors")

            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)

    def open_form(self, doctor=None):
        DoctorForm(self, doctor, on_save=self.load_doctors)

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a doctor to edit.")
            return
        values = self.tree.item(selected, "values")
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE id=?", (values[0],))
            doctor = cursor.fetchone()
        self.open_form(doctor)

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a doctor to delete.")
            return
        values = self.tree.item(selected, "values")
        if messagebox.askyesno("Confirm Delete", f"Delete doctor '{values[1]}'?"):
            with database.get_connection() as conn:
                conn.execute("DELETE FROM doctors WHERE id=?", (values[0],))
                conn.commit()
            self.load_doctors()


class DoctorForm(tk.Toplevel):
    def __init__(self, parent, doctor=None, on_save=None):
        super().__init__(parent)
        self.doctor = doctor
        self.on_save = on_save
        self.title("Edit Doctor" if doctor else "Add Doctor")
        self.geometry("380x300")
        self.resizable(False, False)
        set_icon(self)
        self.grab_set()
        self._build_ui()

        if doctor:
            self._populate(doctor)

    def _build_ui(self):
        fields = [
            ("Full Name",       "name"),
            ("Specialization",  "specialization"),
            ("Phone",           "phone"),
            ("Email",           "email"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(self, text=label + ":", anchor="e", width=14).grid(
                row=i, column=0, padx=10, pady=10, sticky="e")
            var = tk.StringVar()
            self.vars[key] = var
            tk.Entry(self, textvariable=var, width=25).grid(row=i, column=1, padx=10)

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  padx=20, pady=5, command=self.save).grid(
                  row=len(fields), column=0, columnspan=2, pady=15)

    def _populate(self, doctor):
        # doctor = (id, name, specialization, phone, email)
        keys = ["name", "specialization", "phone", "email"]
        for i, key in enumerate(keys):
            self.vars[key].set(doctor[i + 1])

    def save(self):
        name = self.vars["name"].get().strip()
        if not name:
            messagebox.showwarning("Required", "Name is required.", parent=self)
            return

        data = (
            name,
            self.vars["specialization"].get().strip(),
            self.vars["phone"].get().strip(),
            self.vars["email"].get().strip(),
        )

        with database.get_connection() as conn:
            if self.doctor:
                conn.execute("""
                    UPDATE doctors SET name=?, specialization=?, phone=?, email=?
                    WHERE id=?
                """, (*data, self.doctor[0]))
            else:
                conn.execute("""
                    INSERT INTO doctors (name, specialization, phone, email)
                    VALUES (?, ?, ?, ?)
                """, data)
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
