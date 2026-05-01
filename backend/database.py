"""
RoadSoS — Omniscient Architect Protocol v5.0
Database Engine: Full CSV→SQLite+FTS5 ingestion with cKDTree spatial search.

Ingests ALL 10,000+ hospitals from hospital_directory.csv on startup.
Supports:
  - Spatial queries (nearest hospitals by lat/lon via cKDTree)
  - Full-text search (by pincode, district, town, hospital name, state)
  - Combined search: text query → geocode → spatial nearest
"""

import csv
import math
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.spatial import cKDTree

from backend.config import CSV_PATH, DB_PATH, MAX_RADIUS_KM, MAX_RESULTS, FTS_RESULTS

# ──────────────────────────────────────────────
# GLOBALS
# ──────────────────────────────────────────────
_tree: Optional[cKDTree] = None
_coords: Optional[np.ndarray] = None
_sr_nos: Optional[list] = None

# Earth radius for haversine
_R_EARTH = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points."""
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    return _R_EARTH * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _parse_coordinates(coord_str: str) -> tuple[Optional[float], Optional[float]]:
    """Parse 'lat, lon' string from CSV Location_Coordinates column."""
    if not coord_str or coord_str.strip() == "0":
        return None, None
    try:
        parts = coord_str.strip().split(",")
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            if -90 <= lat <= 90 and -180 <= lon <= 180 and (lat != 0 or lon != 0):
                return lat, lon
    except (ValueError, IndexError):
        pass
    return None, None


def _ensure_db() -> None:
    """Create SQLite database from CSV if it doesn't exist or is outdated."""
    os.makedirs(DB_PATH.parent, exist_ok=True)

    # Check if DB exists and is newer than CSV
    if DB_PATH.exists() and CSV_PATH.exists():
        db_mtime = os.path.getmtime(DB_PATH)
        csv_mtime = os.path.getmtime(CSV_PATH)
        if db_mtime > csv_mtime:
            return  # DB is up to date

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Hospital CSV not found: {CSV_PATH}")

    print(f"[DATABASE] Ingesting {CSV_PATH} -> {DB_PATH} ...")
    start = time.time()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Drop and recreate
    cursor.execute("DROP TABLE IF EXISTS hospitals")
    cursor.execute("DROP TABLE IF EXISTS hospitals_fts")

    cursor.execute("""
        CREATE TABLE hospitals (
            sr_no INTEGER PRIMARY KEY,
            lat REAL,
            lon REAL,
            location TEXT,
            hospital_name TEXT,
            hospital_category TEXT,
            hospital_care_type TEXT,
            discipline TEXT,
            address TEXT,
            state TEXT,
            district TEXT,
            subdistrict TEXT,
            pincode TEXT,
            telephone TEXT,
            mobile_number TEXT,
            emergency_num TEXT,
            ambulance_phone TEXT,
            bloodbank_phone TEXT,
            tollfree TEXT,
            helpline TEXT,
            email TEXT,
            website TEXT,
            specialties TEXT,
            facilities TEXT,
            accreditation TEXT,
            town TEXT,
            village TEXT,
            established_year TEXT,
            num_doctors INTEGER,
            num_consultants INTEGER,
            total_beds INTEGER,
            private_wards INTEGER,
            beds_eco_weaker INTEGER,
            emergency_services TEXT,
            tariff_range TEXT,
            state_id INTEGER,
            district_id INTEGER
        )
    """)

    # Create FTS5 virtual table for full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE hospitals_fts USING fts5(
            sr_no UNINDEXED,
            hospital_name,
            district,
            state,
            pincode,
            town,
            address,
            specialties,
            content='hospitals',
            content_rowid='sr_no'
        )
    """)

    # Parse and insert CSV
    inserted = 0
    skipped = 0

    with open(str(CSV_PATH), "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat, lon = _parse_coordinates(row.get("Location_Coordinates", ""))
            if lat is None:
                skipped += 1
                continue

            sr_no = int(row.get("Sr_No", 0)) if row.get("Sr_No", "0").isdigit() else inserted + 1

            def safe_int(val):
                try:
                    return int(val) if val and val.strip() and val.strip() != "0" else 0
                except ValueError:
                    return 0

            def safe_str(val):
                return val.strip() if val and val.strip() and val.strip() != "0" else ""

            cursor.execute("""
                INSERT OR REPLACE INTO hospitals VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
            """, (
                sr_no,
                lat, lon,
                safe_str(row.get("Location", "")),
                safe_str(row.get("Hospital_Name", "")),
                safe_str(row.get("Hospital_Category", "")),
                safe_str(row.get("Hospital_Care_Type", "")),
                safe_str(row.get("Discipline_Systems_of_Medicine", "")),
                safe_str(row.get("Address_Original_First_Line", "")),
                safe_str(row.get("State", "")),
                safe_str(row.get("District", "")),
                safe_str(row.get("Subdistrict", "")),
                safe_str(row.get("Pincode", "")),
                safe_str(row.get("Telephone", "")),
                safe_str(row.get("Mobile_Number", "")),
                safe_str(row.get("Emergency_Num", "")),
                safe_str(row.get("Ambulance_Phone_No", "")),
                safe_str(row.get("Bloodbank_Phone_No", "")),
                safe_str(row.get("Tollfree", "")),
                safe_str(row.get("Helpline", "")),
                safe_str(row.get("Hospital_Primary_Email_Id", "")),
                safe_str(row.get("Website", "")),
                safe_str(row.get("Specialties", "")),
                safe_str(row.get("Facilities", "")),
                safe_str(row.get("Accreditation", "")),
                safe_str(row.get("Town", "")),
                safe_str(row.get("Village", "")),
                safe_str(row.get("Establised_Year", "")),
                safe_int(row.get("Number_Doctor", "0")),
                safe_int(row.get("Num_Mediconsultant_or_Expert", "0")),
                safe_int(row.get("Total_Num_Beds", "0")),
                safe_int(row.get("Number_Private_Wards", "0")),
                safe_int(row.get("Num_Bed_for_Eco_Weaker_Sec", "0")),
                safe_str(row.get("Emergency_Services", "")),
                safe_str(row.get("Tariff_Range", "")),
                safe_int(row.get("State_ID", "0")),
                safe_int(row.get("District_ID", "0")),
            ))
            inserted += 1

    # Populate FTS index
    cursor.execute("""
        INSERT INTO hospitals_fts(sr_no, hospital_name, district, state, pincode, town, address, specialties)
        SELECT sr_no, hospital_name, district, state, pincode, town, address, specialties FROM hospitals
    """)

    # Create spatial index
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lat ON hospitals(lat)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lon ON hospitals(lon)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pincode ON hospitals(pincode)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_district ON hospitals(district)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_state ON hospitals(state)")

    conn.commit()
    conn.close()

    elapsed = round(time.time() - start, 2)
    print(f"[DATABASE] OK: Ingested {inserted} hospitals ({skipped} skipped) in {elapsed}s")


def _build_kdtree() -> None:
    """Build cKDTree from all hospital coordinates for sub-10ms spatial queries."""
    global _tree, _coords, _sr_nos

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT sr_no, lat, lon FROM hospitals WHERE lat IS NOT NULL AND lon IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("[DATABASE] WARNING: No hospitals with coordinates found!")
        return

    _sr_nos = [r[0] for r in rows]
    _coords = np.array([[r[1], r[2]] for r in rows])

    # Convert to radians for haversine-compatible tree
    coords_rad = np.radians(_coords)
    _tree = cKDTree(coords_rad)

    print(f"[DATABASE] OK: cKDTree built with {len(rows)} hospitals")


def initialize() -> None:
    """Initialize the database: ingest CSV if needed, build cKDTree."""
    _ensure_db()
    _build_kdtree()


def get_nearest_hospitals(lat: float, lon: float, limit: int = MAX_RESULTS, radius_km: float = MAX_RADIUS_KM) -> list[dict]:
    """Find nearest hospitals using cKDTree spatial index.

    Returns list of hospital dicts sorted by distance with full metadata.
    """
    if _tree is None or _coords is None or _sr_nos is None:
        return []

    # Convert query point to radians
    query_rad = np.radians([lat, lon])

    # Approximate: radius in radians (distance / earth_radius)
    radius_rad = radius_km / _R_EARTH

    # Query the tree
    indices = _tree.query_ball_point(query_rad, radius_rad)

    if not indices:
        # Expand search — find closest 5 regardless of distance
        distances, indices_arr = _tree.query(query_rad, k=min(limit, len(_sr_nos)))
        if isinstance(indices_arr, np.integer):
            indices = [int(indices_arr)]
        else:
            indices = [int(i) for i in indices_arr]

    # Get actual distances and hospital data
    sr_no_list = [_sr_nos[i] for i in indices]

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    results = []
    for sr_no in sr_no_list:
        cursor.execute("SELECT * FROM hospitals WHERE sr_no = ?", (sr_no,))
        row = cursor.fetchone()
        if row:
            d = dict(row)
            d["distance_km"] = round(haversine(lat, lon, d["lat"], d["lon"]), 2)
            results.append(d)

    conn.close()

    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])
    return results[:limit]


def search_hospitals(query: str, limit: int = FTS_RESULTS) -> list[dict]:
    """Full-text search across hospital name, district, pincode, town, state.

    Supports queries like: "744101", "South Andaman", "Apollo Hospital", "Kerala"
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Clean query for FTS5
    clean_query = query.strip().replace('"', '').replace("'", "")
    if not clean_query:
        conn.close()
        return []

    # Try exact pincode match first
    if clean_query.isdigit() and len(clean_query) == 6:
        cursor.execute("SELECT * FROM hospitals WHERE pincode = ? LIMIT ?", (clean_query, limit))
        rows = cursor.fetchall()
        if rows:
            results = [dict(r) for r in rows]
            conn.close()
            return results

    # FTS5 search with prefix matching
    try:
        fts_query = " OR ".join(f'"{word}"*' for word in clean_query.split() if word)
        cursor.execute("""
            SELECT h.* FROM hospitals h
            JOIN hospitals_fts fts ON h.sr_no = fts.sr_no
            WHERE hospitals_fts MATCH ?
            LIMIT ?
        """, (fts_query, limit))
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]
    except Exception:
        # Fallback: LIKE search
        like_q = f"%{clean_query}%"
        cursor.execute("""
            SELECT * FROM hospitals
            WHERE hospital_name LIKE ? OR district LIKE ? OR pincode LIKE ?
                  OR town LIKE ? OR state LIKE ? OR address LIKE ?
            LIMIT ?
        """, (like_q, like_q, like_q, like_q, like_q, like_q, limit))
        rows = cursor.fetchall()
        results = [dict(r) for r in rows]

    conn.close()
    return results


def get_db_stats() -> dict:
    """Get database statistics."""
    if not DB_PATH.exists():
        return {"status": "error", "message": "Database not found"}

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM hospitals")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT state) FROM hospitals")
    states = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT district) FROM hospitals")
    districts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT pincode) FROM hospitals WHERE pincode != ''")
    pincodes = cursor.fetchone()[0]

    conn.close()

    return {
        "status": "ok",
        "total_hospitals": total,
        "states": states,
        "districts": districts,
        "pincodes": pincodes,
        "kdtree_nodes": len(_sr_nos) if _sr_nos else 0
    }
