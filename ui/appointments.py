import tkinter as tk
from tkinter import ttk, messagebox
import database
from ui.utils import set_icon

class AppointmentsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_appointments()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="Appointments", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="+ Book Appointment", bg="#27ae60", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.open_form).pack(side="right")

        # ── Filter by status ─────────────────────────────
        filter_frame = tk.Frame(self, bg="#ecf0f1")
        filter_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(filter_frame, text="Filter:", bg="#ecf0f1").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        statuses = ["All", "scheduled", "completed", "cancelled"]
        ttk.Combobox(filter_frame, textvariable=self.filter_var,
                     values=statuses, state="readonly", width=15).pack(side="left", padx=8)
        tk.Button(filter_frame, text="Apply", relief="flat", bg="#2980b9", fg="white",
                  padx=8, command=self.load_appointments).pack(side="left")

        # ── Table ────────────────────────────────────────
        cols = ("ID", "Patient", "Doctor", "Date", "Time", "Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor="center")
        self.tree.column("ID", width=50)
        self.tree.column("Patient", width=180, anchor="w")
        self.tree.column("Doctor",  width=180, anchor="w")

        # Color-code rows by status
        self.tree.tag_configure("completed", background="#d5f5e3")
        self.tree.tag_configure("cancelled", background="#fadbd8")
        self.tree.tag_configure("scheduled", background="#fef9e7")

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
        tk.Button(btn_frame, text="Mark Completed", bg="#27ae60", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=lambda: self.change_status("completed")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", bg="#e67e22", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=lambda: self.change_status("cancelled")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.delete_selected).pack(side="left", padx=5)

    def load_appointments(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        status_filter = self.filter_var.get()
        with database.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT a.id, p.name, d.name, a.date, a.time, a.status
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors  d ON a.doctor_id  = d.id
            """
            if status_filter != "All":
                cursor.execute(query + " WHERE a.status=? ORDER BY a.date, a.time",
                               (status_filter,))
            else:
                cursor.execute(query + " ORDER BY a.date, a.time")

            for row in cursor.fetchall():
                tag = row[5]  # status column
                self.tree.insert("", "end", values=row, tags=(tag,))

    def open_form(self, appointment=None):
        AppointmentForm(self, appointment, on_save=self.load_appointments)

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an appointment to edit.")
            return
        values = self.tree.item(selected, "values")
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM appointments WHERE id=?", (values[0],))
            appointment = cursor.fetchone()
        self.open_form(appointment)

    def change_status(self, new_status):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an appointment.")
            return
        values = self.tree.item(selected, "values")
        with database.get_connection() as conn:
            conn.execute("UPDATE appointments SET status=? WHERE id=?",
                         (new_status, values[0]))
            conn.commit()
        self.load_appointments()

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an appointment to delete.")
            return
        values = self.tree.item(selected, "values")
        if messagebox.askyesno("Confirm Delete", f"Delete appointment for '{values[1]}'?"):
            with database.get_connection() as conn:
                conn.execute("DELETE FROM appointments WHERE id=?", (values[0],))
                conn.commit()
            self.load_appointments()


class AppointmentForm(tk.Toplevel):
    def __init__(self, parent, appointment=None, on_save=None):
        super().__init__(parent)
        self.appointment = appointment
        self.on_save = on_save
        self.title("Edit Appointment" if appointment else "Book Appointment")
        self.geometry("400x340")
        self.resizable(False, False)
        set_icon(self)
        self.grab_set()
        self._load_options()
        self._build_ui()

        if appointment:
            self._populate(appointment)

    def _load_options(self):
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM patients ORDER BY name")
            self.patients = cursor.fetchall()  # [(id, name), ...]
            cursor.execute("SELECT id, name FROM doctors ORDER BY name")
            self.doctors = cursor.fetchall()

    def _build_ui(self):
        self.vars = {}

        # Patient dropdown
        tk.Label(self, text="Patient:", anchor="e", width=12).grid(
            row=0, column=0, padx=10, pady=10, sticky="e")
        self.vars["patient"] = tk.StringVar()
        patient_names = [f"{p[0]} - {p[1]}" for p in self.patients]
        ttk.Combobox(self, textvariable=self.vars["patient"],
                     values=patient_names, state="readonly", width=25).grid(
                     row=0, column=1, padx=10)

        # Doctor dropdown
        tk.Label(self, text="Doctor:", anchor="e", width=12).grid(
            row=1, column=0, padx=10, pady=10, sticky="e")
        self.vars["doctor"] = tk.StringVar()
        doctor_names = [f"{d[0]} - {d[1]}" for d in self.doctors]
        ttk.Combobox(self, textvariable=self.vars["doctor"],
                     values=doctor_names, state="readonly", width=25).grid(
                     row=1, column=1, padx=10)

        # Date
        tk.Label(self, text="Date:", anchor="e", width=12).grid(
            row=2, column=0, padx=10, pady=10, sticky="e")
        self.vars["date"] = tk.StringVar()
        tk.Entry(self, textvariable=self.vars["date"], width=27).grid(
            row=2, column=1, padx=10)
        tk.Label(self, text="Format: YYYY-MM-DD", font=("Arial", 8),
                 fg="gray").grid(row=3, column=1, sticky="w", padx=10)

        # Time
        tk.Label(self, text="Time:", anchor="e", width=12).grid(
            row=4, column=0, padx=10, pady=10, sticky="e")
        self.vars["time"] = tk.StringVar()
        tk.Entry(self, textvariable=self.vars["time"], width=27).grid(
            row=4, column=1, padx=10)
        tk.Label(self, text="Format: HH:MM (e.g. 09:30)", font=("Arial", 8),
                 fg="gray").grid(row=5, column=1, sticky="w", padx=10)

        # Status
        tk.Label(self, text="Status:", anchor="e", width=12).grid(
            row=6, column=0, padx=10, pady=10, sticky="e")
        self.vars["status"] = tk.StringVar(value="scheduled")
        ttk.Combobox(self, textvariable=self.vars["status"],
                     values=["scheduled", "completed", "cancelled"],
                     state="readonly", width=25).grid(row=6, column=1, padx=10)

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  padx=20, pady=5, command=self.save).grid(
                  row=7, column=0, columnspan=2, pady=15)

    def _populate(self, appointment):
        # appointment = (id, patient_id, doctor_id, date, time, status)
        for i, p in enumerate(self.patients):
            if p[0] == appointment[1]:
                self.vars["patient"].set(f"{p[0]} - {p[1]}")
        for i, d in enumerate(self.doctors):
            if d[0] == appointment[2]:
                self.vars["doctor"].set(f"{d[0]} - {d[1]}")
        self.vars["date"].set(appointment[3])
        self.vars["time"].set(appointment[4])
        self.vars["status"].set(appointment[5])

    def save(self):
        patient_str = self.vars["patient"].get()
        doctor_str  = self.vars["doctor"].get()
        date        = self.vars["date"].get().strip()
        time        = self.vars["time"].get().strip()
        status      = self.vars["status"].get()

        if not all([patient_str, doctor_str, date, time]):
            messagebox.showwarning("Required", "All fields are required.", parent=self)
            return

        patient_id = int(patient_str.split(" - ")[0])
        doctor_id  = int(doctor_str.split(" - ")[0])

        with database.get_connection() as conn:
            if self.appointment:
                conn.execute("""
                    UPDATE appointments
                    SET patient_id=?, doctor_id=?, date=?, time=?, status=?
                    WHERE id=?
                """, (patient_id, doctor_id, date, time, status, self.appointment[0]))
            else:
                conn.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (patient_id, doctor_id, date, time, status))
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
