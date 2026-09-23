"""
CrowdDB: SQLite Database for Citizen Pollution Reports & Hazard Mapping
Manages crowd-sourced environmental observations, AI-verified hazard impact,
community upvotes, and geo-spatial incident tracking.
"""

import os
import sqlite3
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "crowd_reports.db")

class CrowdDB:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crowd_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    location_name TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    hazard_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    symptoms TEXT,
                    upvotes INTEGER DEFAULT 1,
                    grok_ai_assessment TEXT,
                    estimated_aqi_impact TEXT,
                    status TEXT DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

            # Check if seed data exists
            cursor.execute("SELECT COUNT(*) FROM crowd_reports")
            count = cursor.fetchone()[0]
            if count == 0:
                self._seed_initial_reports(cursor)
                conn.commit()

    def _seed_initial_reports(self, cursor):
        sample_reports = [
            (
                "Delhi", "Anand Vihar ISBT & Ring Road", 28.6469, 77.3160,
                "Heavy Traffic Jam", "Severe",
                "Extreme congestion of diesel interstate buses idling for over 90 minutes. Dense black particulate exhaust filling the whole intersection.",
                "Eye irritation, chest tightness, pungent diesel odor", 24,
                "Grok AI: High-density idling diesel exhaust producing acute localized PM2.5 and NO2 surge.",
                "+45 to +60 AQI", "Active"
            ),
            (
                "Delhi", "Bawana Industrial Area, Sector 3", 28.7981, 77.0514,
                "Industrial Emission", "Hazardous",
                "Unregistered plastic recycling unit burning scrap polymers in open yard behind warehouse.",
                "Acrid toxic plastic smell, stinging eyes, coughing fit", 42,
                "Grok AI: Open combustion of synthetic polymers releasing toxic dioxins and hydrochloric aerosols. Emergency municipal intervention recommended.",
                "+65 to +90 AQI", "Investigating"
            ),
            (
                "Bengaluru", "Silk Board Junction / Outer Ring Road", 12.9172, 77.6229,
                "Heavy Traffic Jam", "Moderate",
                "Peak hour gridlock stretching from HSR Layout to Silk Board flyover ramp. Heavy PM10 dust kicking up from metro construction.",
                "Throat irritation, reduced visibility", 19,
                "Grok AI: Cumulative fine soot and resuspension of unpaved road dust along high-volume tech corridor.",
                "+25 to +35 AQI", "Active"
            ),
            (
                "Bengaluru", "Whitefield Borewell Road", 12.9698, 77.7499,
                "Construction Dust", "Moderate",
                "Uncovered sand trucks and dry batch concrete mixing blowing clouds across residential apartments without water sprinkling.",
                "Sneezing, dry throat, gritty dust on vehicles", 15,
                "Grok AI: Unmitigated mechanical particulate dispersion primarily elevating PM10 levels.",
                "+20 to +30 AQI", "Active"
            ),
            (
                "Mumbai", "Deonar Dumping Ground vicinity", 19.0635, 72.9238,
                "Garbage/Plastic Fire", "Severe",
                "Smoldering municipal solid waste flare spreading hazy gray blanket over Chembur and Govandi.",
                "Severe respiratory discomfort, headache, burning eyes", 38,
                "Grok AI: Landfill methane combustion with organic waste emitting persistent volatile organic compounds (VOCs) and PM2.5.",
                "+50 to +75 AQI", "Active"
            ),
            (
                "Kolkata", "Chitpur Railway Yard & Cossipore Road", 22.6105, 88.3753,
                "Industrial Emission", "Moderate",
                "Small foundry chimney spewing thick dark smoke near canal bank.",
                "Sulfur smell, dark soot settled on balconies", 11,
                "Grok AI: Low-efficiency coal combustion causing localized sulfur dioxide and black carbon plume.",
                "+30 to +45 AQI", "Investigating"
            ),
            (
                "Hyderabad", "Gachibowli Financial District Expressway", 17.4399, 78.3489,
                "Construction Dust", "Low",
                "Excavation for new commercial tower with high velocity dust plumes during afternoon gusts.",
                "Dust in eyes, dry cough", 8,
                "Grok AI: Coarse mineral dust elevation; standard barrier netting missing at project perimeter.",
                "+15 to +25 AQI", "Active"
            ),
            (
                "Chennai", "Manali Industrial Belt", 13.1670, 80.2625,
                "Chemical/Pungent Odor", "Severe",
                "Strong pungent chemical petrochemical odor wafting toward residential neighborhoods with onshore breeze.",
                "Nausea, dizziness, acute nasal burning", 29,
                "Grok AI: Petrochemical refinery sulfur/mercaptan release carried by evening sea breeze corridor.",
                "+40 to +55 AQI", "Investigating"
            ),
            (
                "Amritsar", "GT Road Bypass agricultural border", 31.6500, 74.8300,
                "Stubble Burning", "Severe",
                "Paddy crop residue set on fire across multiple adjacent farm plots along the highway.",
                "Thick choking haze, visibility dropped to 100 meters, watery eyes", 33,
                "Grok AI: High-intensity seasonal biomass burn producing massive spikes of PM2.5, carbon monoxide, and black carbon aerosols.",
                "+70 to +110 AQI", "Active"
            )
        ]

        cursor.executemany("""
            INSERT INTO crowd_reports (
                city, location_name, latitude, longitude, hazard_type, severity,
                description, symptoms, upvotes, grok_ai_assessment, estimated_aqi_impact, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_reports)

    def add_report(self, city, location_name, hazard_type, severity, description,
                   symptoms="", lat=None, lon=None, grok_ai_assessment="", estimated_aqi_impact=""):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO crowd_reports (
                    city, location_name, latitude, longitude, hazard_type,
                    severity, description, symptoms, upvotes, grok_ai_assessment,
                    estimated_aqi_impact, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 'Active')
            """, (
                city, location_name, lat, lon, hazard_type, severity,
                description, symptoms, grok_ai_assessment, estimated_aqi_impact
            ))
            conn.commit()
            return cursor.lastrowid

    def get_reports(self, city=None, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if city and city.lower() != "all":
                cursor.execute("""
                    SELECT * FROM crowd_reports
                    WHERE LOWER(city) = LOWER(?)
                    ORDER BY created_at DESC LIMIT ?
                """, (city, limit))
            else:
                cursor.execute("""
                    SELECT * FROM crowd_reports
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def upvote_report(self, report_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE crowd_reports
                SET upvotes = upvotes + 1
                WHERE id = ?
            """, (report_id,))
            conn.commit()
            cursor.execute("SELECT upvotes FROM crowd_reports WHERE id = ?", (report_id,))
            row = cursor.fetchone()
            return row["upvotes"] if row else None

    def get_crowd_stats(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crowd_reports")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT hazard_type, COUNT(*) as count FROM crowd_reports GROUP BY hazard_type ORDER BY count DESC")
            by_hazard = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT city, COUNT(*) as count FROM crowd_reports GROUP BY city ORDER BY count DESC LIMIT 8")
            by_city = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT severity, COUNT(*) as count FROM crowd_reports GROUP BY severity")
            by_severity = [dict(row) for row in cursor.fetchall()]

            return {
                "total_reports": total,
                "by_hazard": by_hazard,
                "by_city": by_city,
                "by_severity": by_severity
            }

# Singleton instance
crowd_db = CrowdDB()
