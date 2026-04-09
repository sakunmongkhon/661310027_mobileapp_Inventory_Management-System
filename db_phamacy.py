# db_phamacy.py
"""
สคริปต์สำหรับสร้างข้อมูลทดสอบในฐานข้อมูลคลังยา
"""

import sqlite3
from datetime import datetime, timedelta

# สร้าง/เชื่อมต่อฐานข้อมูล
conn = sqlite3.connect('pharmacy.db')
cursor = conn.cursor()

# สร้างตารางยา
cursor.execute('''
CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    lot TEXT,
    quantity INTEGER,
    expire_date DATE,
    status TEXT
)
''')

# ข้อมูลทดสอบ
sample_data = [
    ("Paracetamol 500mg", "MED001", "LOT202604", 100, (datetime.now() + timedelta(days=40)).strftime('%Y-%m-%d'), "ปกติ"),
    ("Amoxicillin 250mg", "MED002", "LOT202603", 50, (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'), "ใกล้หมดอายุ"),
    ("Ibuprofen 200mg", "MED003", "LOT202602", 0, (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'), "หมดสต็อก"),
    ("Cough Syrup", "MED004", "LOT202601", 30, (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'), "หมดอายุ"),
]

# ลบข้อมูลเดิม
cursor.execute('DELETE FROM medicines')

# เพิ่มข้อมูลใหม่
cursor.executemany('''
INSERT INTO medicines (name, code, lot, quantity, expire_date, status)
VALUES (?, ?, ?, ?, ?, ?)
''', sample_data)

conn.commit()
conn.close()

print("สร้างข้อมูลทดสอบในฐานข้อมูล pharmacy.db เรียบร้อยแล้ว")
