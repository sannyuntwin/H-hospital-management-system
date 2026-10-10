import tkinter as tk
from tkinter import ttk
import database

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class ReportsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_reports()

    def _build_ui(self):
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="Reports", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="Refresh", bg="#2980b9", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.load_reports).pack(side="right")

        # Summary cards row
        self.cards_frame = tk.Frame(self, bg="#ecf0f1")
        self.cards_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_revenue    = self._make_card("Total Revenue",    "0 MMK",   "#27ae60")
        self.lbl_patients   = self._make_card("Total Patients",   "0",       "#2980b9")
        self.lbl_appts      = self._make_card("Total Appointments","0",      "#8e44ad")
        self.lbl_unpaid     = self._make_card("Unpaid Invoices",  "0 MMK",   "#e74c3c")

        # Chart canvas
        self.fig = Figure(figsize=(10, 4.5), dpi=90, facecolor="#ecf0f1")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _make_card(self, title, value, color):
        frame = tk.Frame(self.cards_frame, bg=color, padx=15, pady=10)
        frame.pack(side="left", expand=True, fill="x", padx=5)
        tk.Label(frame, text=title, bg=color, fg="white",
                 font=("Arial", 9)).pack()
        lbl = tk.Label(frame, text=value, bg=color, fg="white",
                       font=("Arial", 13, "bold"))
        lbl.pack()
        return lbl

    def load_reports(self):
        with database.get_connection() as conn:
            cursor = conn.cursor()

            # Summary totals
            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM billing WHERE paid=1")
            total_revenue = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM patients")
            total_patients = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM appointments")
            total_appts = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(amount),0) FROM billing WHERE paid=0")
            unpaid = cursor.fetchone()[0]

            # Monthly revenue (last 6 months)
            cursor.execute("""
                SELECT strftime('%Y-%m', date) as month, SUM(amount)
                FROM billing WHERE paid=1
                GROUP BY month ORDER BY month DESC LIMIT 6
            """)
            revenue_rows = cursor.fetchall()[::-1]

            # Patients per month (last 6 months)
            cursor.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COUNT(*)
                FROM patients
                WHERE created_at IS NOT NULL
                GROUP BY month ORDER BY month DESC LIMIT 6
            """)
            patient_rows = [r for r in cursor.fetchall() if r[0] is not None][::-1]

            # Appointment status breakdown
            cursor.execute("""
                SELECT status, COUNT(*) FROM appointments GROUP BY status
            """)
            appt_status = cursor.fetchall()

        # Update cards
        self.lbl_revenue.config(text=f"{total_revenue:,.0f} MMK")
        self.lbl_patients.config(text=str(total_patients))
        self.lbl_appts.config(text=str(total_appts))
        self.lbl_unpaid.config(text=f"{unpaid:,.0f} MMK")

        # Draw charts
        self.fig.clear()

        ax1 = self.fig.add_subplot(131)
        ax2 = self.fig.add_subplot(132)
        ax3 = self.fig.add_subplot(133)

        self.fig.patch.set_facecolor("#ecf0f1")
        for ax in (ax1, ax2, ax3):
            ax.set_facecolor("#ffffff")

        # Chart 1 — Monthly Revenue
        if revenue_rows:
            months  = [r[0] for r in revenue_rows]
            amounts = [r[1] for r in revenue_rows]
            bars = ax1.bar(months, amounts, color="#27ae60", edgecolor="white")
            ax1.set_title("Monthly Revenue (MMK)", fontsize=9, fontweight="bold")
            ax1.tick_params(axis="x", labelsize=7, rotation=30)
            ax1.tick_params(axis="y", labelsize=7)
            for bar, amt in zip(bars, amounts):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                         f"{amt:,.0f}", ha="center", va="bottom", fontsize=6)
        else:
            ax1.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax1.transAxes)
            ax1.set_title("Monthly Revenue (MMK)", fontsize=9, fontweight="bold")

        # Chart 2 — Patients per Month
        if patient_rows:
            months  = [r[0] for r in patient_rows]
            counts  = [r[1] for r in patient_rows]
            ax2.bar(months, counts, color="#2980b9", edgecolor="white")
            ax2.set_title("New Patients per Month", fontsize=9, fontweight="bold")
            ax2.tick_params(axis="x", labelsize=7, rotation=30)
            ax2.tick_params(axis="y", labelsize=7)
        else:
            ax2.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax2.transAxes)
            ax2.set_title("New Patients per Month", fontsize=9, fontweight="bold")

        # Chart 3 — Appointment Status Pie
        if appt_status:
            labels = [r[0].capitalize() for r in appt_status]
            sizes  = [r[1] for r in appt_status]
            colors = {"Scheduled": "#f39c12", "Completed": "#27ae60", "Cancelled": "#e74c3c"}
            pie_colors = [colors.get(l, "#95a5a6") for l in labels]
            ax3.pie(sizes, labels=labels, autopct="%1.0f%%",
                    colors=pie_colors, textprops={"fontsize": 8})
            ax3.set_title("Appointment Status", fontsize=9, fontweight="bold")
        else:
            ax3.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax3.transAxes)
            ax3.set_title("Appointment Status", fontsize=9, fontweight="bold")

        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()
