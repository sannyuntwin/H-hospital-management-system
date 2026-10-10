import tkinter as tk
from tkinter import ttk, messagebox
import database
from ui.utils import set_icon

class PatientsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_patients()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="Patient Management", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="+ Add Patient", bg="#27ae60", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.open_form).pack(side="right")

        # ── Search ───────────────────────────────────────
        search_frame = tk.Frame(self, bg="#ecf0f1")
        search_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(search_frame, text="Search:", bg="#ecf0f1").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.load_patients())
        tk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=8)

        # ── Table ────────────────────────────────────────
        cols = ("ID", "Name", "Age", "Gender", "Phone", "Blood Type")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.column("ID", width=50)
        self.tree.column("Name", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, padx=20, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.empty_label = tk.Label(self.tree, text="No patients found.",
                                    bg="white", fg="#95a5a6", font=("Arial", 12))

        # ── Action Buttons ───────────────────────────────
        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="Edit", bg="#2980b9", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.edit_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.delete_selected).pack(side="left", padx=5)

    def load_patients(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self.search_var.get().strip()
        with database.get_connection() as conn:
            cursor = conn.cursor()
            if search:
                cursor.execute(
                    "SELECT id, name, age, gender, phone, blood_type FROM patients WHERE name LIKE ?",
                    (f"%{search}%",)
                )
            else:
                cursor.execute("SELECT id, name, age, gender, phone, blood_type FROM patients")

            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)

        if not self.tree.get_children():
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

    def open_form(self, patient=None):
        PatientForm(self, patient, on_save=self.load_patients)

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a patient to edit.")
            return
        values = self.tree.item(selected, "values")
        # Fetch full record
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE id=?", (values[0],))
            patient = cursor.fetchone()
        self.open_form(patient)

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a patient to delete.")
            return
        values = self.tree.item(selected, "values")
        if messagebox.askyesno("Confirm Delete", f"Delete patient '{values[1]}'?"):
            with database.get_connection() as conn:
                conn.execute("DELETE FROM patients WHERE id=?", (values[0],))
                conn.commit()
            self.load_patients()


class PatientForm(tk.Toplevel):
    def __init__(self, parent, patient=None, on_save=None):
        super().__init__(parent)
        self.patient = patient
        self.on_save = on_save
        self.title("Edit Patient" if patient else "Add Patient")
        self.geometry("380x380")
        self.resizable(False, False)
        set_icon(self)
        self.grab_set()  # modal
        self._build_ui()

        if patient:
            self._populate(patient)

    def _build_ui(self):
        self.vars = {}

        def row(r, label, widget_fn):
            tk.Label(self, text=label + ":", anchor="e", width=12,
                     font=("Arial", 10)).grid(row=r, column=0, padx=10, pady=8, sticky="e")
            return widget_fn(r)

        def entry(r):
            var = tk.StringVar()
            tk.Entry(self, textvariable=var, width=27, font=("Arial", 10)).grid(
                row=r, column=1, padx=10, sticky="w")
            return var

        def combo(r, values):
            var = tk.StringVar()
            ttk.Combobox(self, textvariable=var, values=values,
                         state="readonly", width=25).grid(
                row=r, column=1, padx=10, sticky="w")
            return var

        self.vars["name"]       = row(0, "Full Name",  entry)
        self.vars["age"]        = row(1, "Age",         entry)
        self.vars["gender"]     = row(2, "Gender",      lambda r: combo(r, ["Male", "Female", "Other"]))
        self.vars["phone"]      = row(3, "Phone",       entry)
        self.vars["address"]    = row(4, "Address",     entry)
        self.vars["blood_type"] = row(5, "Blood Type",  lambda r: combo(r, ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]))

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  font=("Arial", 11), padx=20, pady=6, command=self.save).grid(
                  row=6, column=0, columnspan=2, pady=15)

    def _populate(self, patient):
        # patient = (id, name, age, gender, phone, address, blood_type)
        keys = ["name", "age", "gender", "phone", "address", "blood_type"]
        for i, key in enumerate(keys):
            self.vars[key].set(patient[i + 1])

    def save(self):
        name = self.vars["name"].get().strip()
        if not name:
            messagebox.showwarning("Required", "Name is required.", parent=self)
            return

        age_str = self.vars["age"].get().strip()
        age = None
        if age_str:
            try:
                age = int(age_str)
                if age < 0 or age > 150:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Age", "Age must be a whole number (0–150).", parent=self)
                return

        data = (
            name,
            age,
            self.vars["gender"].get().strip(),
            self.vars["phone"].get().strip(),
            self.vars["address"].get().strip(),
            self.vars["blood_type"].get().strip(),
        )

        with database.get_connection() as conn:
            if self.patient:
                conn.execute("""
                    UPDATE patients SET name=?, age=?, gender=?, phone=?, address=?, blood_type=?
                    WHERE id=?
                """, (*data, self.patient[0]))
            else:
                conn.execute("""
                    INSERT INTO patients (name, age, gender, phone, address, blood_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, data)
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
