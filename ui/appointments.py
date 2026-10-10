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

        self.empty_label = tk.Label(self.tree, text="No appointments found.",
                                    bg="white", fg="#95a5a6", font=("Arial", 12))

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

        if not self.tree.get_children():
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

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


try:
    from tkcalendar import DateEntry
    _HAS_CAL = True
except ImportError:
    _HAS_CAL = False


class AppointmentForm(tk.Toplevel):
    def __init__(self, parent, appointment=None, on_save=None):
        super().__init__(parent)
        self.appointment = appointment
        self.on_save = on_save
        self.title("Edit Appointment" if appointment else "Book Appointment")
        self.geometry("420x320")
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
            self.patients = cursor.fetchall()
            cursor.execute("SELECT id, name FROM doctors ORDER BY name")
            self.doctors = cursor.fetchall()

    def _build_ui(self):
        self.vars = {}

        lbl_opts = dict(anchor="e", width=12, font=("Arial", 10))

        # Patient
        tk.Label(self, text="Patient:", **lbl_opts).grid(row=0, column=0, padx=10, pady=9, sticky="e")
        self.vars["patient"] = tk.StringVar()
        patient_names = [f"{p[0]} - {p[1]}" for p in self.patients]
        ttk.Combobox(self, textvariable=self.vars["patient"],
                     values=patient_names, state="readonly", width=27).grid(row=0, column=1, padx=10, columnspan=2, sticky="w")

        # Doctor
        tk.Label(self, text="Doctor:", **lbl_opts).grid(row=1, column=0, padx=10, pady=9, sticky="e")
        self.vars["doctor"] = tk.StringVar()
        doctor_names = [f"{d[0]} - {d[1]}" for d in self.doctors]
        ttk.Combobox(self, textvariable=self.vars["doctor"],
                     values=doctor_names, state="readonly", width=27).grid(row=1, column=1, padx=10, columnspan=2, sticky="w")

        # Date
        tk.Label(self, text="Date:", **lbl_opts).grid(row=2, column=0, padx=10, pady=9, sticky="e")
        if _HAS_CAL:
            from datetime import date as _date
            self.date_entry = DateEntry(self, width=16, date_pattern="yyyy-mm-dd",
                                        font=("Arial", 10), background="#2980b9",
                                        foreground="white", borderwidth=2)
            self.date_entry.grid(row=2, column=1, padx=10, columnspan=2, sticky="w")
        else:
            self.vars["date"] = tk.StringVar()
            tk.Entry(self, textvariable=self.vars["date"], width=18,
                     font=("Arial", 10)).grid(row=2, column=1, padx=10, columnspan=2, sticky="w")

        # Time — hour + minute spinboxes
        tk.Label(self, text="Time:", **lbl_opts).grid(row=3, column=0, padx=10, pady=9, sticky="e")
        time_frame = tk.Frame(self)
        time_frame.grid(row=3, column=1, padx=10, columnspan=2, sticky="w")
        self.hour_var   = tk.StringVar(value="09")
        self.minute_var = tk.StringVar(value="00")
        hours   = [f"{h:02d}" for h in range(0, 24)]
        minutes = [f"{m:02d}" for m in range(0, 60, 5)]
        ttk.Combobox(time_frame, textvariable=self.hour_var,   values=hours,
                     state="readonly", width=4, font=("Arial", 10)).pack(side="left")
        tk.Label(time_frame, text=" : ", font=("Arial", 11, "bold")).pack(side="left")
        ttk.Combobox(time_frame, textvariable=self.minute_var, values=minutes,
                     state="readonly", width=4, font=("Arial", 10)).pack(side="left")
        tk.Label(time_frame, text="  (HH : MM)", fg="gray",
                 font=("Arial", 8)).pack(side="left", padx=4)

        # Status
        tk.Label(self, text="Status:", **lbl_opts).grid(row=4, column=0, padx=10, pady=9, sticky="e")
        self.vars["status"] = tk.StringVar(value="scheduled")
        ttk.Combobox(self, textvariable=self.vars["status"],
                     values=["scheduled", "completed", "cancelled"],
                     state="readonly", width=27).grid(row=4, column=1, padx=10, columnspan=2, sticky="w")

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  font=("Arial", 11), padx=20, pady=6, command=self.save).grid(
                  row=5, column=0, columnspan=3, pady=15)

    def _get_date(self):
        if _HAS_CAL:
            return self.date_entry.get_date().strftime("%Y-%m-%d")
        return self.vars["date"].get().strip()

    def _set_date(self, val):
        if _HAS_CAL and val:
            try:
                from datetime import datetime
                self.date_entry.set_date(datetime.strptime(val, "%Y-%m-%d").date())
            except Exception:
                pass
        elif not _HAS_CAL:
            self.vars["date"].set(val or "")

    def _populate(self, appointment):
        for p in self.patients:
            if p[0] == appointment[1]:
                self.vars["patient"].set(f"{p[0]} - {p[1]}")
        for d in self.doctors:
            if d[0] == appointment[2]:
                self.vars["doctor"].set(f"{d[0]} - {d[1]}")
        self._set_date(appointment[3])
        if appointment[4]:
            parts = str(appointment[4]).split(":")
            self.hour_var.set(parts[0].zfill(2) if parts else "09")
            # round minute to nearest 5
            min_val = int(parts[1]) if len(parts) > 1 else 0
            self.minute_var.set(f"{(min_val // 5) * 5:02d}")
        self.vars["status"].set(appointment[5])

    def save(self):
        patient_str = self.vars["patient"].get()
        doctor_str  = self.vars["doctor"].get()
        appt_date   = self._get_date()
        appt_time   = f"{self.hour_var.get()}:{self.minute_var.get()}"
        status      = self.vars["status"].get()

        if not all([patient_str, doctor_str, appt_date]):
            messagebox.showwarning("Required", "Patient, Doctor, and Date are required.", parent=self)
            return

        patient_id = int(patient_str.split(" - ")[0])
        doctor_id  = int(doctor_str.split(" - ")[0])

        with database.get_connection() as conn:
            if self.appointment:
                conn.execute("""
                    UPDATE appointments
                    SET patient_id=?, doctor_id=?, date=?, time=?, status=?
                    WHERE id=?
                """, (patient_id, doctor_id, appt_date, appt_time, status, self.appointment[0]))
            else:
                conn.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (patient_id, doctor_id, appt_date, appt_time, status))
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
