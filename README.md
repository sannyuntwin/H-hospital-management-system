<p align="center">
  <img src="assets/logo.png" alt="H-Hospital Logo" width="80"/>
</p>

# H-Hospital Management System

A desktop hospital/clinic management system built with Python. Runs as a standalone `.exe` on Windows — no internet connection or server required.

---

## Features

| Module | Description |
|---|---|
| **Dashboard** | Overview stats: total patients, doctors, today's appointments, unpaid invoices |
| **Patients** | Add, edit, delete patient records with search |
| **Doctors** | Manage doctor profiles and specializations |
| **Appointments** | Schedule appointments, mark completed or cancelled |
| **Medical Records** | Link diagnoses and prescriptions to patients |
| **Billing** | Create invoices in MMK, track paid/unpaid, print PDF invoices |
| **Settings** | Configure hospital name, address, phone, email for invoices |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10 |
| GUI | Tkinter + ttk (built-in) |
| Database | SQLite 3 (single file `hospital.db`) |
| PDF Generation | ReportLab |
| Packaging | PyInstaller (produces `.exe`) |

No web framework, no external database server, no internet required.

---

## Requirements

- Python 3.10
- pip packages:

```
reportlab
Pillow
pyinstaller
```

---

## Run from Source

**1. Clone or download the project**

**2. Create a virtual environment**

```powershell
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```powershell
pip install reportlab Pillow pyinstaller
```

**4. Run the app**

```powershell
python main.py
```

**Default login:**
- Username: `admin`
- Password: `admin123`

---

## Build as .exe (Windows)

> **Note:** If you are on Python 3.10.0 exactly, apply the fix below before building.

**Fix for Python 3.10.0 (skip if on 3.10.1+)**

Open `venv\Lib\site-packages\PyInstaller\lib\modulegraph\util.py` and replace line 36:

```python
# Before
yield from (i for i in get_instructions(code_object) if i.opname != "EXTENDED_ARG")

# After
try:
    yield from (i for i in get_instructions(code_object) if i.opname != "EXTENDED_ARG")
except (IndexError, Exception):
    pass
```

**Build command:**

```powershell
pyinstaller --onefile --windowed --name="HospitalManager" `
  --add-data "assets/h-hospital.ico;assets" `
  --add-data "assets/logo.png;assets" `
  --icon="assets/h-hospital.ico" `
  --hidden-import=ui.home `
  --hidden-import=ui.patients `
  --hidden-import=ui.doctors `
  --hidden-import=ui.appointments `
  --hidden-import=ui.billing `
  --hidden-import=ui.medical_records `
  --hidden-import=ui.settings_page `
  --hidden-import=pdf_generator `
  main.py
```

Output: `dist\HospitalManager.exe`

The `.exe` is fully self-contained. Copy it anywhere and run — the database (`hospital.db`) is created automatically in the same folder on first launch.

---

## Project Structure

```
clinic-hospital-manage/
├── main.py               # Entry point
├── database.py           # SQLite setup, all table definitions
├── pdf_generator.py      # PDF invoice generator (ReportLab)
├── assets/
│   ├── logo.png          # App logo (shown on login screen)
│   └── h-hospital.ico    # Window & taskbar icon
└── ui/
    ├── login.py          # Login window
    ├── dashboard.py      # Main window with sidebar
    ├── home.py           # Dashboard stats page
    ├── patients.py       # Patient management
    ├── doctors.py        # Doctor management
    ├── appointments.py   # Appointment scheduling
    ├── medical_records.py# Medical records
    ├── billing.py        # Billing & invoices
    └── settings_page.py  # Hospital settings
```

---

## Database

SQLite database file `hospital.db` is created automatically on first run in the same directory as the app. No setup needed.

Tables: `users`, `patients`, `doctors`, `appointments`, `billing`, `medical_records`, `settings`

---

## License

For commercial use — contact the developer.
