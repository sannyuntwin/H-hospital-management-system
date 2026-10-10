import os
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import database

def get_setting(cursor, key, default=""):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default

def generate_invoice(bill_id, output_path):
    with database.get_connection() as conn:
        cursor = conn.cursor()

        # Fetch bill + patient
        cursor.execute("""
            SELECT b.id, p.name, p.phone, p.address, b.amount, b.paid, b.date
            FROM billing b
            JOIN patients p ON b.patient_id = p.id
            WHERE b.id = ?
        """, (bill_id,))
        bill = cursor.fetchone()
        if not bill:
            return False

        # Fetch hospital settings
        hospital_name = get_setting(cursor, "hospital_name", "My Clinic")
        address       = get_setting(cursor, "address",       "")
        phone         = get_setting(cursor, "phone",         "")
        email         = get_setting(cursor, "email",         "")
        footer_note   = get_setting(cursor, "footer_note",   "Thank you.")

    bill_id, patient_name, patient_phone, patient_address, amount, paid, bill_date = bill
    status = "PAID" if paid else "UNPAID"

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            topMargin=1.5*cm, bottomMargin=1.5*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Hospital Header ──────────────────────────────────
    header_style = ParagraphStyle("header", fontSize=18, fontName="Helvetica-Bold",
                                  alignment=TA_CENTER, spaceAfter=4)
    sub_style    = ParagraphStyle("sub", fontSize=9, alignment=TA_CENTER,
                                  textColor=colors.grey, spaceAfter=2)

    story.append(Paragraph(hospital_name, header_style))
    story.append(Paragraph(address, sub_style))
    story.append(Paragraph(f"Phone: {phone}  |  Email: {email}", sub_style))
    story.append(Spacer(1, 0.4*cm))

    # Divider
    story.append(Table([[""]], colWidths=[17*cm],
                        style=[("LINEABOVE", (0,0), (-1,-1), 1, colors.HexColor("#2c3e50"))]))
    story.append(Spacer(1, 0.4*cm))

    # ── Invoice Title ────────────────────────────────────
    title_style = ParagraphStyle("title", fontSize=14, fontName="Helvetica-Bold",
                                 alignment=TA_CENTER, spaceAfter=10)
    story.append(Paragraph("INVOICE", title_style))

    # ── Invoice Meta ─────────────────────────────────────
    meta_data = [
        ["Invoice #:", f"INV-{bill_id:04d}",   "Date:",   bill_date],
        ["Status:",    status,                  "",        ""],
    ]
    meta_table = Table(meta_data, colWidths=[3*cm, 5*cm, 3*cm, 6*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("TEXTCOLOR", (1,0), (1,0),  colors.HexColor("#27ae60") if paid else colors.HexColor("#e74c3c")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Patient Info ─────────────────────────────────────
    story.append(Paragraph("Bill To:", ParagraphStyle("section", fontSize=11,
                           fontName="Helvetica-Bold", spaceAfter=4)))
    patient_data = [
        ["Name:",    patient_name],
        ["Phone:",   patient_phone or "—"],
        ["Address:", patient_address or "—"],
    ]
    patient_table = Table(patient_data, colWidths=[3*cm, 14*cm])
    patient_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Items Table ──────────────────────────────────────
    items_data = [
        ["Description", "Amount (MMK)"],
        ["Medical Service / Consultation", f"{amount:,.0f}"],
    ]
    items_table = Table(items_data, colWidths=[12*cm, 5*cm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  colors.HexColor("#2c3e50")),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 10),
        ("ALIGN",         (1,0), (1,-1),  "RIGHT"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.HexColor("#ecf0f1"), colors.white]),
        ("GRID",          (0,0), (-1,-1), 0.5, colors.HexColor("#bdc3c7")),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Total Row ────────────────────────────────────────
    total_data = [["", "TOTAL:", f"{amount:,.0f} MMK"]]
    total_table = Table(total_data, colWidths=[9*cm, 4*cm, 4*cm])
    total_table.setStyle(TableStyle([
        ("FONTNAME",  (1,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (1,0), (-1,-1), 12),
        ("ALIGN",     (1,0), (-1,-1), "RIGHT"),
        ("TEXTCOLOR", (2,0), (2,0),   colors.HexColor("#27ae60") if paid else colors.HexColor("#e74c3c")),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 1*cm))

    # ── Footer ───────────────────────────────────────────
    story.append(Table([[""]], colWidths=[17*cm],
                        style=[("LINEABOVE", (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(footer_note,
                            ParagraphStyle("footer", fontSize=9,
                                           alignment=TA_CENTER, textColor=colors.grey)))

    doc.build(story)
    return True
