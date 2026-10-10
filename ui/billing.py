import os
import subprocess
import sys
from pdf_generator import generate_invoice

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import database
from ui.utils import set_icon

class BillingPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ecf0f1")
        self._build_ui()
        self.load_bills()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────
        header = tk.Frame(self, bg="#ecf0f1")
        header.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(header, text="Billing", font=("Arial", 16, "bold"),
                 bg="#ecf0f1").pack(side="left")
        tk.Button(header, text="+ New Invoice", bg="#27ae60", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.open_form).pack(side="right")
        tk.Button(header, text="Print Invoice", bg="#8e44ad", fg="white",
                  font=("Arial", 10), relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self.print_invoice).pack(side="right", padx=(0, 8))

        # ── Summary bar ──────────────────────────────────
        self.summary_frame = tk.Frame(self, bg="#ecf0f1")
        self.summary_frame.pack(fill="x", padx=20, pady=5)

        self.lbl_total    = tk.Label(self.summary_frame, text="Total: 0",
                                     bg="#ecf0f1", font=("Arial", 10))
        self.lbl_paid     = tk.Label(self.summary_frame, text="Paid: 0",
                                     bg="#ecf0f1", fg="#27ae60", font=("Arial", 10))
        self.lbl_unpaid   = tk.Label(self.summary_frame, text="Unpaid: 0",
                                     bg="#ecf0f1", fg="#e74c3c", font=("Arial", 10))
        for lbl in (self.lbl_total, self.lbl_paid, self.lbl_unpaid):
            lbl.pack(side="left", padx=15)

        # ── Filter ───────────────────────────────────────
        filter_frame = tk.Frame(self, bg="#ecf0f1")
        filter_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(filter_frame, text="Filter:", bg="#ecf0f1").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self.filter_var,
                     values=["All", "Paid", "Unpaid"],
                     state="readonly", width=12).pack(side="left", padx=8)
        tk.Button(filter_frame, text="Apply", relief="flat", bg="#2980b9", fg="white",
                  padx=8, command=self.load_bills).pack(side="left")

        # ── Table ────────────────────────────────────────
        cols = ("ID", "Patient", "Amount (MMK)", "Status", "Date")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=13)

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("ID", width=50)
        self.tree.column("Patient", width=200, anchor="w")

        self.tree.tag_configure("paid",   background="#d5f5e3")
        self.tree.tag_configure("unpaid", background="#fadbd8")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, padx=20, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.empty_label = tk.Label(self.tree, text="No invoices found.",
                                    bg="white", fg="#95a5a6", font=("Arial", 12))

        # ── Action Buttons ───────────────────────────────
        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(pady=8)

        tk.Button(btn_frame, text="Mark as Paid", bg="#27ae60", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.mark_paid).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit", bg="#2980b9", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.edit_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white",
                  relief="flat", padx=15, pady=4, cursor="hand2",
                  command=self.delete_selected).pack(side="left", padx=5)


    def load_bills(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        filter_val = self.filter_var.get()
        with database.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT b.id, p.name, b.amount, b.paid, b.date
                FROM billing b
                JOIN patients p ON b.patient_id = p.id
            """
            if filter_val == "Paid":
                cursor.execute(query + " WHERE b.paid=1 ORDER BY b.date DESC")
            elif filter_val == "Unpaid":
                cursor.execute(query + " WHERE b.paid=0 ORDER BY b.date DESC")
            else:
                cursor.execute(query + " ORDER BY b.date DESC")

            rows = cursor.fetchall()

        total_amount  = 0
        paid_amount   = 0
        unpaid_amount = 0

        for row in rows:
            bill_id, patient, amount, paid, bill_date = row
            status = "Paid" if paid else "Unpaid"
            tag    = "paid" if paid else "unpaid"
            self.tree.insert("", "end",
                             values=(bill_id, patient, f"{amount:,.0f}", status, bill_date),
                             tags=(tag,))
            total_amount += amount
            if paid:
                paid_amount += amount
            else:
                unpaid_amount += amount

        if not self.tree.get_children():
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_label.place_forget()

        self.lbl_total.config( text=f"Total: {total_amount:,.0f} MMK")
        self.lbl_paid.config(  text=f"Paid: {paid_amount:,.0f} MMK")
        self.lbl_unpaid.config(text=f"Unpaid: {unpaid_amount:,.0f} MMK")

    def open_form(self, bill=None):
        BillingForm(self, bill, on_save=self.load_bills)

    def mark_paid(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an invoice.")
            return
        values = self.tree.item(selected, "values")
        if values[3] == "Paid":
            messagebox.showinfo("Already Paid", "This invoice is already marked as paid.")
            return
        with database.get_connection() as conn:
            conn.execute("UPDATE billing SET paid=1 WHERE id=?", (values[0],))
            conn.commit()
        self.load_bills()

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an invoice to edit.")
            return
        values = self.tree.item(selected, "values")
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM billing WHERE id=?", (values[0],))
            bill = cursor.fetchone()
        self.open_form(bill)

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an invoice to delete.")
            return
        values = self.tree.item(selected, "values")
        if messagebox.askyesno("Confirm Delete", f"Delete invoice #{values[0]}?"):
            with database.get_connection() as conn:
                conn.execute("DELETE FROM billing WHERE id=?", (values[0],))
                conn.commit()
            self.load_bills()

    def print_invoice(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an invoice to print.")
            return

        values = self.tree.item(selected, "values")
        bill_id = values[0]

        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", f"invoice_{bill_id}.pdf"
        )
        output_path = os.path.normpath(output_path)

        success = generate_invoice(bill_id, output_path)
        if success:
            if sys.platform == "win32":
                os.startfile(output_path)
            messagebox.showinfo("Done", f"Invoice saved and opened:\n{output_path}")
        else:
            messagebox.showerror("Error", "Could not generate invoice.")


try:
    from tkcalendar import DateEntry as _DateEntry
    _HAS_CAL = True
except ImportError:
    _HAS_CAL = False


class BillingForm(tk.Toplevel):
    def __init__(self, parent, bill=None, on_save=None):
        super().__init__(parent)
        self.bill = bill
        self.on_save = on_save
        self.title("Edit Invoice" if bill else "New Invoice")
        self.geometry("400x260")
        self.resizable(False, False)
        set_icon(self)
        self.grab_set()
        self._load_patients()
        self._build_ui()

        if bill:
            self._populate(bill)

    def _load_patients(self):
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM patients ORDER BY name")
            self.patients = cursor.fetchall()

    def _build_ui(self):
        self.vars = {}
        lbl_opts = dict(anchor="e", width=13, font=("Arial", 10))

        # Patient
        tk.Label(self, text="Patient:", **lbl_opts).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.vars["patient"] = tk.StringVar()
        patient_names = [f"{p[0]} - {p[1]}" for p in self.patients]
        ttk.Combobox(self, textvariable=self.vars["patient"],
                     values=patient_names, state="readonly", width=27).grid(row=0, column=1, padx=10)

        # Amount
        tk.Label(self, text="Amount (MMK):", **lbl_opts).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.vars["amount"] = tk.StringVar()
        tk.Entry(self, textvariable=self.vars["amount"], width=29,
                 font=("Arial", 10)).grid(row=1, column=1, padx=10)

        # Date
        tk.Label(self, text="Date:", **lbl_opts).grid(row=2, column=0, padx=10, pady=10, sticky="e")
        if _HAS_CAL:
            self.date_entry = _DateEntry(self, width=16, date_pattern="yyyy-mm-dd",
                                         font=("Arial", 10), background="#2980b9",
                                         foreground="white", borderwidth=2)
            self.date_entry.grid(row=2, column=1, padx=10, sticky="w")
        else:
            self.vars["date"] = tk.StringVar(value=str(date.today()))
            tk.Entry(self, textvariable=self.vars["date"], width=29,
                     font=("Arial", 10)).grid(row=2, column=1, padx=10)

        # Paid status
        tk.Label(self, text="Status:", **lbl_opts).grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.vars["paid"] = tk.StringVar(value="Unpaid")
        ttk.Combobox(self, textvariable=self.vars["paid"],
                     values=["Unpaid", "Paid"],
                     state="readonly", width=27).grid(row=3, column=1, padx=10)

        tk.Button(self, text="Save", bg="#27ae60", fg="white", relief="flat",
                  font=("Arial", 11), padx=20, pady=6, command=self.save).grid(
                  row=4, column=0, columnspan=2, pady=15)

    def _get_date(self):
        if _HAS_CAL:
            return self.date_entry.get_date().strftime("%Y-%m-%d")
        return self.vars["date"].get().strip()

    def _set_date(self, val):
        if _HAS_CAL and val:
            try:
                from datetime import datetime as _dt
                self.date_entry.set_date(_dt.strptime(val, "%Y-%m-%d").date())
            except Exception:
                pass
        elif not _HAS_CAL:
            self.vars["date"].set(val or str(date.today()))

    def _populate(self, bill):
        for p in self.patients:
            if p[0] == bill[1]:
                self.vars["patient"].set(f"{p[0]} - {p[1]}")
        self.vars["amount"].set(bill[2])
        self._set_date(bill[4])
        self.vars["paid"].set("Paid" if bill[3] else "Unpaid")

    def save(self):
        patient_str = self.vars["patient"].get()
        amount_str  = self.vars["amount"].get().strip()
        bill_date   = self._get_date()
        paid        = 1 if self.vars["paid"].get() == "Paid" else 0

        if not all([patient_str, amount_str, bill_date]):
            messagebox.showwarning("Required", "All fields are required.", parent=self)
            return

        try:
            amount = float(amount_str.replace(",", ""))
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a valid number.", parent=self)
            return

        patient_id = int(patient_str.split(" - ")[0])

        with database.get_connection() as conn:
            if self.bill:
                conn.execute("""
                    UPDATE billing SET patient_id=?, amount=?, paid=?, date=?
                    WHERE id=?
                """, (patient_id, amount, paid, bill_date, self.bill[0]))
            else:
                conn.execute("""
                    INSERT INTO billing (patient_id, amount, paid, date)
                    VALUES (?, ?, ?, ?)
                """, (patient_id, amount, paid, bill_date))
            conn.commit()

        if self.on_save:
            self.on_save()
        self.destroy()
