import os
import sys
import tkinter as tk
from tkinter import ttk

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Dashboard(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.parent = parent
        self.user = user  # (id, username, password, role)
        self.title("Hospital Management System")
        self.geometry("1000x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        icon_path = os.path.join(_get_base_dir(), "assets", "h-hospital.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 500
        y = (self.winfo_screenheight() // 2) - 300
        self.geometry(f"1000x600+{x}+{y}")

        self._build_ui()
        self.show_page("home")  # default page on open

    def _build_ui(self):
        # ── Sidebar ──────────────────────────────────────
        sidebar = tk.Frame(self, bg="#2c3e50", width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🏥 Hospital", bg="#2c3e50", fg="white",
                 font=("Arial", 14, "bold")).pack(pady=20)

        tk.Label(sidebar, text=f"👤 {self.user[1]}", bg="#2c3e50",
                 fg="#bdc3c7", font=("Arial", 9)).pack(pady=(0, 15))

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=10)

        # Sidebar buttons
        pages = [
            ("Home",          "home"), 
            ("Patients",      "patients"),
            ("Doctors",       "doctors"),
            ("Medical Records", "medical_records"),
            ("Appointments",  "appointments"),
            ("Billing",       "billing"),
            ("Settings", "settings"),
        ]
        for label, page_name in pages:
            tk.Button(
                sidebar, text=label, bg="#34495e", fg="white",
                font=("Arial", 11), relief="flat", cursor="hand2",
                activebackground="#1abc9c", activeforeground="white",
                width=18, pady=8,
                command=lambda p=page_name: self.show_page(p)
            ).pack(pady=2, padx=10)

        tk.Button(
            sidebar, text="Logout", bg="#e74c3c", fg="white",
            font=("Arial", 10), relief="flat", cursor="hand2",
            width=18, pady=6, command=self.logout
        ).pack(side="bottom", pady=20, padx=10)

        # ── Content Area ──────────────────────────────────
        self.content = tk.Frame(self, bg="#ecf0f1")
        self.content.pack(side="right", fill="both", expand=True)

        self.pages = {}

    def show_page(self, name):
        # Lazy-load pages on first visit
        if name not in self.pages:
            if name == "home":
                from ui.home import HomePage
                self.pages[name] = HomePage(self.content)
            elif name == "patients":
                from ui.patients import PatientsPage
                self.pages[name] = PatientsPage(self.content)
            elif name == "doctors":
                from ui.doctors import DoctorsPage
                self.pages[name] = DoctorsPage(self.content)
            elif name == "medical_records":
                from ui.medical_records import MedicalRecordsPage
                self.pages[name] = MedicalRecordsPage(self.content)
            elif name == "appointments":
                from ui.appointments import AppointmentsPage
                self.pages[name] = AppointmentsPage(self.content)
            elif name == "billing":
                from ui.billing import BillingPage
                self.pages[name] = BillingPage(self.content)
                
            elif name == "settings":
                from ui.settings_page import SettingsPage
                self.pages[name] = SettingsPage(self.content)


        # Hide all, show the selected one
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)

    def logout(self):
        self.destroy()
        from ui.login import LoginWindow
        LoginWindow(self.parent)

    def on_close(self):
        self.parent.destroy()
