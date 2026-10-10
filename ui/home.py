import tkinter as tk
from tkinter import ttk
from datetime import date
import database

class HomePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_stats()

    def _build_ui(self):
        # ── Welcome Header ───────────────────────────────
        tk.Label(self, text="Dashboard", font=("Arial", 18, "bold"),
                 bg="#ecf0f1").pack(anchor="w", padx=25, pady=(20, 5))
        tk.Label(self, text=f"Today: {date.today().strftime('%A, %d %B %Y')}",
                 font=("Arial", 10), bg="#ecf0f1", fg="#7f8c8d").pack(anchor="w", padx=25)

        # ── Stat Cards ───────────────────────────────────
        cards_frame = tk.Frame(self, bg="#ecf0f1")
        cards_frame.pack(fill="x", padx=25, pady=20)

        self.stat_vars = {}
        cards = [
            ("Total Patients",     "patients",     "#3498db"),
            ("Total Doctors",      "doctors",      "#9b59b6"),
            ("Today's Appts",      "appts_today",  "#e67e22"),
            ("Unpaid Invoices",    "unpaid",        "#e74c3c"),
        ]

        for i, (label, key, color) in enumerate(cards):
            card = tk.Frame(cards_frame, bg=color, width=160, height=100)
            card.grid(row=0, column=i, padx=10, pady=5)
            card.pack_propagate(False)

            var = tk.StringVar(value="0")
            self.stat_vars[key] = var

            tk.Label(card, textvariable=var, font=("Arial", 28, "bold"),
                     bg=color, fg="white").pack(expand=True)
            tk.Label(card, text=label, font=("Arial", 9),
                     bg=color, fg="white").pack(pady=(0, 10))

        # ── Today's Appointments Table ───────────────────
        tk.Label(self, text="Today's Appointments", font=("Arial", 13, "bold"),
                 bg="#ecf0f1").pack(anchor="w", padx=25, pady=(10, 5))

        cols = ("Patient", "Doctor", "Time", "Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180, anchor="center")
        self.tree.column("Patient", anchor="w")
        self.tree.column("Doctor",  anchor="w")

        self.tree.tag_configure("completed", background="#d5f5e3")
        self.tree.tag_configure("cancelled", background="#fadbd8")
        self.tree.tag_configure("scheduled", background="#fef9e7")

        self.tree.pack(fill="both", expand=True, padx=25, pady=5)

        # ── Refresh Button ───────────────────────────────
        tk.Button(self, text="Refresh", bg="#2980b9", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.load_stats).pack(anchor="e", padx=25, pady=8)

    def load_stats(self):
        today = str(date.today())

        with database.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM patients")
            self.stat_vars["patients"].set(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM doctors")
            self.stat_vars["doctors"].set(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM appointments WHERE date=?", (today,))
            self.stat_vars["appts_today"].set(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM billing WHERE paid=0")
            self.stat_vars["unpaid"].set(cursor.fetchone()[0])

            # Today's appointments detail
            for row in self.tree.get_children():
                self.tree.delete(row)

            cursor.execute("""
                SELECT p.name, d.name, a.time, a.status
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors  d ON a.doctor_id  = d.id
                WHERE a.date = ?
                ORDER BY a.time
            """, (today,))

            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row, tags=(row[3],))
