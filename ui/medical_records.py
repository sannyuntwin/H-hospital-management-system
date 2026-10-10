import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import database
from ui.utils import set_icon

try:
    from tkcalendar import DateEntry
    _HAS_CAL = True
except ImportError:
    _HAS_CAL = False

class MedicalRecordsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_records()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="Medical Records", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="+ Add Record", bg="#27ae60", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.open_form).pack(side="right")

        # ── Search by patient ────────────────────────────
        search_frame = tk.Frame(self, bg="#ecf0f1")
        search_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(search_frame, text="Search Patient:", bg="#ecf0f1").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.load_records())
        tk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side="left", padx=8)

        # ── Table ────────────────────────────────────────
        cols = ("ID", "Patient", "Doctor", "Visit Date", "Diagnosis")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=12)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("ID",         width=50)
        self.tree.column("Patient",    width=180, anchor="w")
        self.tree.column("Doctor",     width=160, anchor="w")
        self.tree.column("Diagnosis",  width=220, anchor="w")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, padx=20, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.empty_label = tk.Label(self.tree, text="No medical records found.",
                                    bg="white", fg="#95a5a6", font=("Arial", 12))

        self.tree.bind("<Double-1>", lambda e: self.view_selected())

        # ── Action Buttons ───────────────────────────────
        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="View / Edit", bg="#2980b9", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.view_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.delete_selected).pack(side="left", padx=5)

        tk.Label(self, text="Tip: Double-click a record to view full details",
                 bg="#ecf0f1", fg="#95a5a6", font=("Arial", 8)).pack(pady=(0, 5))

    def load_records(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self.search_var.get().strip()
        with database.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT r.id, p.name, COALESCE(d.name, 'N/A'), r.visit_date, r.diagnosis
                FROM medical_records r
                JOIN patients p ON r.patient_id = p.id
                LEFT JOIN doctors d ON r.doctor_id = d.id
            """
            if search:
                cursor.execute(query + " WHERE p.name LIKE ? ORDER BY r.visit_date DESC",
                               (f"%{search}%",))
            else:
                cursor.execute(query + " ORDER BY r.visit_date DESC")

            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)

        if not self.tree.get_children():
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

    def open_form(self, record=None):
        MedicalRecordForm(self, record, on_save=self.load_records)

    def view_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record.")
            return
        values = self.tree.item(selected, "values")
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medical_records WHERE id=?", (values[0],))
            record = cursor.fetchone()
        self.open_form(record)

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record to delete.")
            return
        values = self.tree.item(selected, "values")
        if messagebox.askyesno("Confirm Delete",
                               f"Delete record for '{values[1]}' on {values[3]}?"):
            with database.get_connection() as conn:
                conn.execute("DELETE FROM medical_records WHERE id=?", (values[0],))
                conn.commit()
            self.load_records()


class MedicalRecordForm(tk.Toplevel):
    def __init__(self, parent, record=None, on_save=None):
        super().__init__(parent)
        self.record = record
        self.on_save = on_save
        self.title("Edit Record" if record else "Add Medical Record")
        self.geometry("480x460")
        self.resizable(False, False)
        set_icon(self)
        self.grab_set()
        self._load_options()
        self._build_ui()

        if record:
            self._populate(record)

    def _load_options(self):
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM patients ORDER BY name")
            self.patients = cursor.fetchall()
            cursor.execute("SELECT id, name FROM doctors ORDER BY name")
            self.doctors = cursor.fetchall()

    def _build_ui(self):
        self.vars = {}

        # Patient
        tk.Label(self, text="Patient:", anchor="e", width=14).grid(
            row=0, column=0, padx=10, pady=8, sticky="e")
        self.vars["patient"] = tk.StringVar()
        patient_names = [f"{p[0]} - {p[1]}" for p in self.patients]
        ttk.Combobox(self, textvariable=self.vars["patient"],
                     values=patient_names, state="readonly", width=30).grid(
                     row=0, column=1, padx=10, sticky="w")

        # Doctor
        tk.Label(self, text="Doctor:", anchor="e", width=14).grid(
            row=1, column=0, padx=10, pady=8, sticky="e")
        self.vars["doctor"] = tk.StringVar()
        doctor_names = [f"{d[0]} - {d[1]}" for d in self.doctors]
        ttk.Combobox(self, textvariable=self.vars["doctor"],
                     values=doctor_names, state="readonly", width=30).grid(
                     row=1, column=1, padx=10, sticky="w")

        # Visit Date
        tk.Label(self, text="Visit Date:", anchor="e", width=14).grid(
            row=2, column=0, padx=10, pady=8, sticky="e")
        if _HAS_CAL:
            self.date_entry = DateEntry(self, width=16, date_pattern="yyyy-mm-dd",
                                        font=("Arial", 10), background="#2980b9",
                                        foreground="white", borderwidth=2)
            self.date_entry.grid(row=2, column=1, padx=10, sticky="w")
        else:
            self.vars["visit_date"] = tk.StringVar(value=str(date.today()))
            tk.Entry(self, textvariable=self.vars["visit_date"], width=32).grid(
                row=2, column=1, padx=10, sticky="w")

        # Diagnosis
        tk.Label(self, text="Diagnosis:", anchor="e", width=14).grid(
            row=3, column=0, padx=10, pady=8, sticky="ne")
        self.diagnosis_text = tk.Text(self, width=30, height=4, font=("Arial", 10))
        self.diagnosis_text.grid(row=3, column=1, padx=10, pady=8, sticky="w")

        # Prescription
        tk.Label(self, text="Prescription:", anchor="e", width=14).grid(
            row=4, column=0, padx=10, pady=8, sticky="ne")
        self.prescription_text = tk.Text(self, width=30, height=4, font=("Arial", 10))
        self.prescription_text.grid(row=4, column=1, padx=10, pady=8, sticky="w")

        # Notes
        tk.Label(self, text="Notes:", anchor="e", width=14).grid(
            row=5, column=0, padx=10, pady=8, sticky="ne")
        self.notes_text = tk.Text(self, width=30, height=3, font=("Arial", 10))
        self.notes_text.grid(row=5, column=1, padx=10, pady=8, sticky="w")

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  padx=20, pady=5, command=self.save).grid(
                  row=6, column=0, columnspan=2, pady=10)

    def _get_date(self):
        if _HAS_CAL:
            return self.date_entry.get_date().strftime("%Y-%m-%d")
        return self.vars["visit_date"].get().strip()

    def _set_date(self, val):
        if _HAS_CAL and val:
            try:
                from datetime import datetime as _dt
                self.date_entry.set_date(_dt.strptime(val, "%Y-%m-%d").date())
            except Exception:
                pass
        elif not _HAS_CAL:
            self.vars["visit_date"].set(val or str(date.today()))

    def _populate(self, record):
        # record = (id, patient_id, doctor_id, visit_date, diagnosis, prescription, notes)
        for p in self.patients:
            if p[0] == record[1]:
                self.vars["patient"].set(f"{p[0]} - {p[1]}")
        for d in self.doctors:
            if d[0] == record[2]:
                self.vars["doctor"].set(f"{d[0]} - {d[1]}")
        self._set_date(record[3])
        if record[4]:
            self.diagnosis_text.insert("1.0", record[4])
        if record[5]:
            self.prescription_text.insert("1.0", record[5])
        if record[6]:
            self.notes_text.insert("1.0", record[6])

    def save(self):
        patient_str  = self.vars["patient"].get()
        visit_date   = self._get_date()
        diagnosis    = self.diagnosis_text.get("1.0", "end").strip()
        prescription = self.prescription_text.get("1.0", "end").strip()
        notes        = self.notes_text.get("1.0", "end").strip()

        if not patient_str or not visit_date:
            messagebox.showwarning("Required", "Patient and Visit Date are required.", parent=self)
            return

        patient_id = int(patient_str.split(" - ")[0])
        doctor_str = self.vars["doctor"].get()
        doctor_id  = int(doctor_str.split(" - ")[0]) if doctor_str else None

        with database.get_connection() as conn:
            if self.record:
                conn.execute("""
                    UPDATE medical_records
                    SET patient_id=?, doctor_id=?, visit_date=?,
                        diagnosis=?, prescription=?, notes=?
                    WHERE id=?
                """, (patient_id, doctor_id, visit_date,
                      diagnosis, prescription, notes, self.record[0]))
            else:
                conn.execute("""
                    INSERT INTO medical_records
                        (patient_id, doctor_id, visit_date, diagnosis, prescription, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (patient_id, doctor_id, visit_date, diagnosis, prescription, notes))
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
