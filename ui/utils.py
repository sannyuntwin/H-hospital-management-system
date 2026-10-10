import os
import sys

def _get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def set_icon(window):
    path = os.path.join(_get_base_dir(), "assets", "h-hospital.ico")
    if os.path.exists(path):
        try:
            window.iconbitmap(path)
        except Exception:
            pass
