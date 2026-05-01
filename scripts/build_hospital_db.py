"""
RoadSoS — Hospital Database Builder
Converts hospital_directory.csv (30,273 rows) into an optimized SQLite database.
"""
import csv
import sqlite3
import os
import re

CSV_PATH = "hospital_directory.csv"
DB_PATH = "backend/data/hospitals.db"

def clean_phone(row):
    fields = ["Emergency_Num", "Ambulance_Phone_No", "Telephone", "Mobile_Number", "Tollfree", "Helpline"]
    for f in fields:
        val = str(row.get(f, "")).strip()
        if val and val.lower() != "nan" and len(val) > 5:
            return re.sub(r'[^0-9+, ]', '', val)
    return "102"

def map_tier(row):
    emergency = str(row.get("Emergency_Services", "")).lower()
    cat = str(row.get("Hospital_Category", "")).lower()
    if "yes" in emergency or "tertiary" in cat: return "tier_1"
    if "secondary" in cat or "hospital" in cat: return "tier_2"
    return "tier_3"

def build():
    print(f"Reading {CSV_PATH}...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY,
            name TEXT, lat REAL, lon REAL, tier TEXT, phone TEXT,
            address TEXT, state TEXT, district TEXT, specialties TEXT
        )
    """)
    count = 0
    with open(CSV_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords = row.get("Location_Coordinates", "")
            if not coords or "," not in coords: continue
            try:
                lat, lon = map(float, coords.split(","))
                if not (-90 <= lat <= 90 and -180 <= lon <= 180): continue
                cursor.execute("INSERT INTO hospitals (name, lat, lon, tier, phone, address, state, district, specialties) VALUES (?,?,?,?,?,?,?,?,?)",
                               (row.get("Hospital_Name", "Unknown"), lat, lon, map_tier(row), clean_phone(row), row.get("Location", ""), row.get("State", ""), row.get("District", ""), row.get("Specialties", "")))
                count += 1
            except: continue
    conn.commit()
    cursor.execute("CREATE INDEX idx_coords ON hospitals(lat, lon)")
    conn.close()
    print(f"Loaded {count} hospitals.")

if __name__ == "__main__": build()
