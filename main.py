import os
import sys
import tkinter as tk
from database import create_tables
from ui.login import LoginWindow

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    create_tables()
    root = tk.Tk()

    icon_path = os.path.join(get_base_dir(), "assets", "h-hospital.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    root.withdraw()
    LoginWindow(root)
    root.mainloop()
