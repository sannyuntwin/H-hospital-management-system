import os
import sys
import tkinter as tk


def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AboutPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()

    def _build_ui(self):
        # Center card
        outer = tk.Frame(self, bg="#ecf0f1")
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(outer, bg="white", padx=50, pady=40)
        card.pack()

        # Logo
        logo_path = os.path.join(_get_base_dir(), "assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                img = tk.PhotoImage(file=logo_path)
                self._logo = img.subsample(max(1, img.height() // 72))
                tk.Label(card, image=self._logo, bg="white").pack(pady=(0, 10))
            except Exception:
                pass

        tk.Label(card, text="H-Hospital", font=("Arial", 22, "bold"),
                 bg="white", fg="#2c3e50").pack()
        tk.Label(card, text="Hospital Management System",
                 font=("Arial", 11), bg="white", fg="#7f8c8d").pack(pady=(2, 4))

        tk.Label(card, text="Version 1.0.0",
                 font=("Arial", 10, "bold"), bg="white", fg="#2980b9").pack()

        tk.Frame(card, bg="#ecf0f1", height=1).pack(fill="x", pady=20)

        info = [
            ("Built with", "Python · Tkinter · SQLite"),
            ("PDF Engine",  "ReportLab"),
            ("Charts",      "Matplotlib"),
            ("Date Picker", "tkcalendar"),
        ]
        for label, value in info:
            row = tk.Frame(card, bg="white")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label + ":", font=("Arial", 9, "bold"),
                     bg="white", fg="#2c3e50", width=14, anchor="e").pack(side="left")
            tk.Label(row, text=value, font=("Arial", 9),
                     bg="white", fg="#555").pack(side="left", padx=6)

        tk.Frame(card, bg="#ecf0f1", height=1).pack(fill="x", pady=20)

        tk.Label(card, text="© 2024 H-Hospital. All rights reserved.",
                 font=("Arial", 8), bg="white", fg="#95a5a6").pack()
