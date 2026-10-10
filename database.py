import sqlite3
import os
import sys

if getattr(sys, 'frozen', False):
    # Running as .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as normal Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "hospital.db")


# DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'staff'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                address TEXT,
                blood_type TEXT,
                created_at TEXT DEFAULT (date('now'))
            )
        """)
        # Add created_at to existing databases that don't have it
        try:
            cursor.execute("ALTER TABLE patients ADD COLUMN created_at TEXT DEFAULT (date('now'))")
        except Exception:
            pass

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT,
                phone TEXT,
                email TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                doctor_id INTEGER,
                date TEXT,
                time TEXT,
                status TEXT DEFAULT 'scheduled',
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                amount REAL,
                paid INTEGER DEFAULT 0,
                date TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)

        # Insert default admin if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")

        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER,
                visit_date TEXT,
                diagnosis TEXT,
                prescription TEXT,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Default hospital settings
        defaults = [
            ("hospital_name",    "My Clinic"),
            ("address",          "123 Main Street"),
            ("phone",            "09123456789"),
            ("email",            "clinic@email.com"),
            ("footer_note",      "Thank you for choosing our clinic."),
        ]
        for key, value in defaults:
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

        
        
        conn.commit()

if __name__ == "__main__":
    create_tables()
    print("Database created successfully!")
    print("Default login -> username: admin | password: admin123")
