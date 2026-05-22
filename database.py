import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

class PatientDatabase:
    def __init__(self, db_path: str= "data/patients.db" ) -> None:
        self.db_path = db_path
        self.conn = None
        self._connect = ()
        self._create_tables = ()

    def _connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _create_tables(self) -> None:
        self.conn.execute('''CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT NOT NULL,
        owner_surname TEXT NOT NULL,
        breed TEXT DEFAULT 'Kavalír King Chares španěl',
        weight kg real,
        created_at TEXT,
        updated_at TEXT,
        UNIQUE(patient_name, owner_surname)
        )
    ''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        exam_date TEXT NOT NULL,
        plax_image TEXT,
        psax_image TEXT,
        lvidd_mm REAL,
        la_ao_ratio REAL,
        stage TEXT,
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    ''')

        self.conn.commit()

    def find_patient(self, patient_name: str, owner_surname: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT FROM patients WHERE patient_name = ? AND owner_surname = ?",
            (patient_name, owner_surname)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    def find_patient_by_id(self, patient_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT FROM patients WHERE patient_id = ?",
            (patient_id)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

 def get_all_patients(self) -> List[Dict[str, Any]]:
     cursor = self.conn.execute("SELECT * FROM patients ORDER BY patient_name")
     return [dict(row) for row in cursor.fetchall()]


    def get_all_patients_names(self) -> List[str]:
        cursor = self.conn.execute("SELECT patient_name FROM patients ORDER BY patient_name")
        return [row[0] for row in cursor.fetchall()]

    def get_all_patients_display_names(self) -> List[str]:
        cursor = self.conn.execute(
            "SELECT patient_name, owner_surname FROM patients ORDER BY patient_name"
        )
        return[f"{row[0]} ({row[1]}" for row in cursor.fetchall()]

    def find_patient_by_display_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        if "(" not in display_name or not display_name.endswith(")"):
            return None
        patient_name = display_name.split("(")[0]
        owner_surname = display_name.split("(")[1].rstrip(")")

        return self.find_patient(patient_name, owner_surname)

    def create_patient(self, patient_name: str, owner_surname: str,
                       breed_name: str = "Kavalír King Charles španěl",
                       weight_kg: Optional[float] = None) -> int:
        now = datetime.now().isoformat()
        cursor = self.conn.execute("""
            INSERT INTO patients (patient_name, owner_surname, breed, weight_kg, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_name, owner_surname, breed_name, now, now))
        self.conn.commit()
        return cursor.lastrowid

    def update_weight(self, patient_id: int, weight_kg: float) -> None:
