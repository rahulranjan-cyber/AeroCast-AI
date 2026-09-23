"""
Automated System Verification Tests
Tests all backend modules, ML pipelines, CrowdDB, Grok AI logic, and Flask API endpoints.
"""

import unittest
import json
from app import app
from ml_service import ml_service
from weather_service import weather_service
from grok_service import grok_service
from crowd_db import crowd_db

class TestAeroCastSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    def test_01_ml_service_prediction(self):
        """Test ML model AQI prediction and CPCB bucket classification"""
        sample_pollutants = {
            "PM2.5": 92.5,
            "PM10": 178.0,
            "NO2": 45.2,
            "SO2": 18.1,
            "CO": 1.45,
            "O3": 28.0,
            "NH3": 14.0
        }
        res = ml_service.predict_aqi(sample_pollutants)
        self.assertIn("aqi", res)
        self.assertIn("bucket", res)
        self.assertIn("color", res)
        self.assertIn("primary_pollutant", res)
        self.assertGreater(res["aqi"], 0)
        print(f"[PASS] ML Prediction: AQI={res['aqi']}, Bucket={res['bucket']}, Primary={res['primary_pollutant']}")

    def test_02_ml_service_forecast(self):
        """Test 7-day city forecasting"""
        forecast = ml_service.forecast_city("Delhi", days=7)
        self.assertEqual(len(forecast), 7)
        self.assertTrue(forecast[0]["is_today"])
        self.assertIn("predicted_aqi", forecast[0])
        print(f"[PASS] 7-Day Forecast: Day 1={forecast[0]['predicted_aqi']} AQI, Day 7={forecast[6]['predicted_aqi']} AQI")

    def test_03_weather_service_pollution(self):
        """Test WeatherService live/calibrated pollutant payload"""
        city_prof = ml_service.city_profiles.get("Bengaluru")
        res = weather_service.get_live_pollution("Bengaluru", city_prof)
        self.assertIn("pollutants", res)
        self.assertIn("PM2.5", res["pollutants"])
        self.assertIn("coordinates", res)
        print(f"[PASS] WeatherService: Source={res['source']}, PM2.5={res['pollutants']['PM2.5']}")

    def test_04_crowd_db_operations(self):
        """Test CrowdDB addition, query, and voting"""
        initial_stats = crowd_db.get_crowd_stats()
        initial_count = initial_stats["total_reports"]

        # Add a new report
        new_id = crowd_db.add_report(
            city="Delhi",
            location_name="Test Sector 12",
            hazard_type="Garbage/Plastic Fire",
            severity="Severe",
            description="Test automated burning incident for verification",
            symptoms="Eye irritation",
            lat=28.62,
            lon=77.21,
            grok_ai_assessment="Grok AI: Test verification assessment",
            estimated_aqi_impact="+30 AQI"
        )
        self.assertIsNotNone(new_id)

        # Upvote
        new_votes = crowd_db.upvote_report(new_id)
        self.assertGreaterEqual(new_votes, 2)

        # Check retrieval
        reports = crowd_db.get_reports("Delhi", limit=10)
        found = any(r["id"] == new_id for r in reports)
        self.assertTrue(found)
        print(f"[PASS] CrowdDB: Successfully inserted report #{new_id}, upvotes={new_votes}")

    def test_05_grok_ai_service(self):
        """Test Grok health advisory and citizen report assessment"""
        adv = grok_service.generate_health_advisory("Delhi", 280, "Poor", {"PM2.5": 140, "PM10": 240})
        self.assertIn("outdoor_activity_rating", adv)
        self.assertIn("vulnerable_groups", adv)

        assess = grok_service.assess_crowd_report("Delhi", "Outer Ring Road", "Stubble Burning", "Heavy smoke", "Cough")
        self.assertIn("estimated_local_aqi_increase", assess)
        self.assertIn("urgency", assess)
        print(f"[PASS] Grok Service: Activity Rating={adv['outdoor_activity_rating']}, Impact={assess['estimated_local_aqi_increase']}")

    def test_06_flask_api_endpoints(self):
        """Test all core REST endpoints"""
        # Home page
        r0 = self.client.get("/")
        self.assertEqual(r0.status_code, 200)

        # Cities list
        r1 = self.client.get("/api/cities")
        self.assertEqual(r1.status_code, 200)
        d1 = r1.get_json()
        self.assertGreaterEqual(d1["total"], 26)

        # Current city status
        r2 = self.client.get("/api/city/Delhi/current")
        self.assertEqual(r2.status_code, 200)
        d2 = r2.get_json()
        self.assertEqual(d2["city"], "Delhi")
        self.assertIn("aqi", d2)

        # Forecast
        r3 = self.client.get("/api/city/Delhi/forecast?days=7")
        self.assertEqual(r3.status_code, 200)
        d3 = r3.get_json()
        self.assertEqual(len(d3["forecast_days"]), 7)

        # Advisory
        r4 = self.client.get("/api/city/Delhi/advisory")
        self.assertEqual(r4.status_code, 200)

        # Crowd reports
        r5 = self.client.get("/api/crowd/reports")
        self.assertEqual(r5.status_code, 200)

        # Post chat
        r6 = self.client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "What mask should I wear today?"}],
            "context": {"city": "Delhi", "aqi": 250, "bucket": "Poor"}
        })
        self.assertEqual(r6.status_code, 200)
        d6 = r6.get_json()
        self.assertIn("reply", d6)

        print("[PASS] All Flask REST API endpoints verified successfully!")

if __name__ == "__main__":
    unittest.main()
