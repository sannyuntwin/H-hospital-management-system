import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import database
import shutil
import os
import csv
from datetime import datetime


class BackupPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Backup & Export", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(anchor="w", padx=25, pady=(20, 5))
        tk.Label(self, text="Protect your data with a backup or export records to Excel.",
                 bg="#ecf0f1", fg="#7f8c8d", font=("Arial", 9)).pack(anchor="w", padx=25)

        # ── Database Backup ──────────────────────────────
        backup_frame = tk.LabelFrame(self, text="  Database Backup  ", bg="#ecf0f1",
                                     font=("Arial", 11, "bold"), padx=20, pady=15)
        backup_frame.pack(fill="x", padx=25, pady=(15, 5))

        tk.Label(backup_frame,
                 text="Creates a full copy of the hospital.db file. Restore it by replacing\n"
                      "hospital.db with the backup file.",
                 bg="#ecf0f1", fg="#555", font=("Arial", 9), justify="left").pack(anchor="w")

        tk.Button(backup_frame, text="💾  Backup Database", bg="#27ae60", fg="white",
                  font=("Arial", 11), relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self.backup_db).pack(anchor="w", pady=(12, 0))

        # ── Export to CSV ────────────────────────────────
        export_frame = tk.LabelFrame(self, text="  Export to CSV  ", bg="#ecf0f1",
                                     font=("Arial", 11, "bold"), padx=20, pady=15)
        export_frame.pack(fill="x", padx=25, pady=(10, 5))

        tk.Label(export_frame,
                 text="Export any table to a .csv file that opens in Excel or Google Sheets.",
                 bg="#ecf0f1", fg="#555", font=("Arial", 9)).pack(anchor="w")

        row = tk.Frame(export_frame, bg="#ecf0f1")
        row.pack(anchor="w", pady=(12, 0))

        tk.Label(row, text="Select table:", bg="#ecf0f1", font=("Arial", 10)).pack(side="left")
        self.table_var = tk.StringVar(value="patients")
        ttk.Combobox(row, textvariable=self.table_var,
                     values=["patients", "doctors", "appointments",
                             "billing", "medical_records", "users"],
                     state="readonly", width=22).pack(side="left", padx=(8, 20))

        tk.Button(row, text="📄  Export CSV", bg="#2980b9", fg="white",
                  font=("Arial", 11), relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self.export_csv).pack(side="left")

    # ── Actions ──────────────────────────────────────────

    def backup_db(self):
        src = database.DB_PATH
        if not os.path.exists(src):
            messagebox.showerror("Error", "Database file not found.", parent=self)
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"hospital_backup_{timestamp}.db"

        dest = filedialog.asksaveasfilename(
            title="Save Backup As",
            initialfile=default_name,
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if not dest:
            return

        try:
            shutil.copy2(src, dest)
            messagebox.showinfo("Backup Complete",
                                f"Database backed up successfully.\n\n{dest}", parent=self)
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e), parent=self)

    def export_csv(self):
        table = self.table_var.get()
        default_name = f"{table}_{datetime.now().strftime('%Y-%m-%d')}.csv"

        dest = filedialog.asksaveasfilename(
            title="Save CSV As",
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")]
        )
        if not dest:
            return

        try:
            with database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                headers = [desc[0] for desc in cursor.description]

            with open(dest, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

            messagebox.showinfo("Export Complete",
                                f"Exported {len(rows)} rows from '{table}'.\n\n{dest}",
                                parent=self)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self)
