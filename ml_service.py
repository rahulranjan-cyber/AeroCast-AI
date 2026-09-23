"""
ML Service for AQI Prediction, Forecasting & Analytics
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "aqi_model.pkl")
PROFILES_PATH = os.path.join(os.path.dirname(__file__), "models", "city_profiles.json")
CSV_PATH = os.path.join(os.path.dirname(__file__), "city_day.csv")

class MLService:
    def __init__(self):
        self.model_data = None
        self.city_profiles = {}
        self.df_history = None
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            self.model_data = joblib.load(MODEL_PATH)
            print("Loaded trained AQI model pipeline.")
        else:
            print("Warning: aqi_model.pkl not found. Run train_model.py first.")

        if os.path.exists(PROFILES_PATH):
            with open(PROFILES_PATH, "r", encoding="utf-8") as f:
                self.city_profiles = json.load(f)
            print(f"Loaded {len(self.city_profiles)} city profiles.")
        else:
            print("Warning: city_profiles.json not found.")

    def get_cpcb_bucket(self, aqi):
        aqi = round(float(aqi), 1)
        if aqi <= 50:
            return {
                "name": "Good",
                "range": "0 - 50",
                "color": "#10b981",
                "bg_color": "rgba(16, 185, 129, 0.15)",
                "description": "Minimal health impact. Air quality is considered satisfactory, and air pollution poses little or no risk.",
                "advisory": "Ideal air quality for outdoor activities, sports, and ventilation."
            }
        elif aqi <= 100:
            return {
                "name": "Satisfactory",
                "range": "51 - 100",
                "color": "#84cc16",
                "bg_color": "rgba(132, 204, 22, 0.15)",
                "description": "Minor breathing discomfort to sensitive people.",
                "advisory": "Acceptable air quality. Unusually sensitive individuals should consider reducing prolonged outdoor exertion."
            }
        elif aqi <= 200:
            return {
                "name": "Moderate",
                "range": "101 - 200",
                "color": "#f59e0b",
                "bg_color": "rgba(245, 158, 11, 0.15)",
                "description": "Breathing discomfort to people with lung disease, asthma, and heart conditions.",
                "advisory": "Children, the elderly, and people with respiratory conditions should limit prolonged outdoor exertion."
            }
        elif aqi <= 300:
            return {
                "name": "Poor",
                "range": "201 - 300",
                "color": "#f97316",
                "bg_color": "rgba(249, 115, 22, 0.15)",
                "description": "Breathing discomfort to most people on prolonged exposure.",
                "advisory": "Everyone should reduce outdoor activities. Wear N95 masks during commutes and keep windows closed."
            }
        elif aqi <= 400:
            return {
                "name": "Very Poor",
                "range": "301 - 400",
                "color": "#ef4444",
                "bg_color": "rgba(239, 68, 68, 0.15)",
                "description": "Respiratory illness on prolonged exposure. Significant risk of throat and eye irritation.",
                "advisory": "Avoid morning walks and outdoor workouts. Use HEPA air purifiers indoors. Vulnerable groups must stay inside."
            }
        else:
            return {
                "name": "Severe",
                "range": "401+",
                "color": "#881337",
                "bg_color": "rgba(136, 19, 55, 0.25)",
                "description": "Affects healthy people and seriously impacts those with existing medical conditions.",
                "advisory": "Health emergency! Stay indoors, seal room gaps, run air purifiers on high, avoid any physical exertion outdoors."
            }

    def predict_aqi(self, pollutants):
        """
        Predict AQI from dict of pollutants:
        {'PM2.5': x, 'PM10': x, 'NO2': x, 'CO': x, 'SO2': x, 'O3': x, 'NH3': x}
        """
        if not self.model_data:
            # Fallback estimation using standard CPCB PM2.5 / PM10 piecewise approximation
            pm25 = pollutants.get('PM2.5', 40.0)
            est_aqi = max(pm25 * 1.6, 25.0)
            bucket = self.get_cpcb_bucket(est_aqi)
            return {
                "aqi": round(est_aqi),
                "bucket": bucket["name"],
                "color": bucket["color"],
                "description": bucket["description"],
                "advisory": bucket["advisory"],
                "primary_pollutant": "PM2.5"
            }

        features = self.model_data["features"]
        median_imputes = self.model_data["median_imputes"]
        row = []
        for feat in features:
            val = pollutants.get(feat, pollutants.get(feat.lower(), None))
            if val is None or np.isnan(val):
                val = median_imputes.get(feat, 20.0)
            row.append(float(val))

        X = pd.DataFrame([row], columns=features)
        pred = float(self.model_data["model"].predict(X)[0])
        pred = max(10.0, round(pred, 1))

        bucket = self.get_cpcb_bucket(pred)

        # Identify primary dominant pollutant relative to safety limits
        # CPCB 24h limits: PM2.5: 60, PM10: 100, NO2: 80, SO2: 80, CO: 2 (mg/m3) or 2000 ug, O3: 100, NH3: 400
        limits = {"PM2.5": 60.0, "PM10": 100.0, "NO2": 80.0, "SO2": 80.0, "CO": 2.0, "O3": 100.0, "NH3": 400.0}
        ratios = {}
        for feat in features:
            val = pollutants.get(feat, median_imputes.get(feat, 20.0))
            if feat in limits:
                ratios[feat] = val / limits[feat]
        primary = max(ratios, key=ratios.get) if ratios else "PM2.5"

        return {
            "aqi": int(round(pred)),
            "bucket": bucket["name"],
            "color": bucket["color"],
            "bg_color": bucket["bg_color"],
            "description": bucket["description"],
            "advisory": bucket["advisory"],
            "primary_pollutant": primary,
            "pollutant_ratios": {k: round(v, 2) for k, v in ratios.items()}
        }

    def forecast_city(self, city_name, days=7, live_pollutants=None):
        """
        Generate multi-day AQI forecast (1 to 7 days) using seasonal baseline + current reading
        """
        profile = self.city_profiles.get(city_name)
        now = datetime.now()
        current_month = str(now.month)

        if live_pollutants:
            current_pred = self.predict_aqi(live_pollutants)
            base_aqi = current_pred["aqi"]
        elif profile:
            base_aqi = profile["stats"]["mean_aqi"]
        else:
            base_aqi = 120.0

        seasonal_month_aqi = profile["monthly_seasonality"].get(current_month, base_aqi) if profile else base_aqi

        forecast = []
        for i in range(days):
            target_date = now + timedelta(days=i)
            day_name = target_date.strftime("%a")
            date_str = target_date.strftime("%b %d")

            # Day of week variation (weekend effect: slight dip on Sundays)
            dow = target_date.weekday()
            dow_factor = 0.94 if dow == 6 else (0.97 if dow == 5 else 1.02)

            # Auto-regressive smoothing toward seasonal mean
            weight_current = max(0.2, 0.85 ** i)
            projected = (weight_current * base_aqi) + ((1 - weight_current) * seasonal_month_aqi)
            projected *= dow_factor

            # Realistic micro-variance
            noise = np.sin(i * 1.3) * 6.0 + np.cos(i * 0.7) * 4.0
            val = max(15, round(projected + noise))

            margin = round(8 + (i * 3.5))
            bucket = self.get_cpcb_bucket(val)

            forecast.append({
                "day": day_name,
                "date": date_str,
                "is_today": i == 0,
                "predicted_aqi": val,
                "min_aqi": max(10, val - margin),
                "max_aqi": val + margin,
                "bucket": bucket["name"],
                "color": bucket["color"],
                "bg_color": bucket["bg_color"],
                "summary": bucket["description"]
            })

        return forecast

    def get_city_diurnal(self, city_name, current_aqi=None):
        """
        Generate 24-hour diurnal pollution curve showing hourly shifts
        """
        profile = self.city_profiles.get(city_name)
        if current_aqi is None:
            current_aqi = profile["stats"]["median_aqi"] if profile else 115.0

        multipliers = profile.get("diurnal_multipliers") if profile else [
            0.82, 0.78, 0.75, 0.72, 0.74, 0.85, 1.10, 1.25, 1.30, 1.20,
            1.05, 0.95, 0.90, 0.85, 0.84, 0.86, 0.94, 1.08, 1.22, 1.32,
            1.28, 1.18, 1.05, 0.92
        ]

        now = datetime.now()
        current_hour = now.hour

        hourly_points = []
        for h in range(24):
            time_label = f"{h:02d}:00"
            hour_mult = multipliers[h]
            hour_aqi = max(15, round(current_aqi * hour_mult))
            bucket = self.get_cpcb_bucket(hour_aqi)

            # Recommend outdoor activity window
            if h in [5, 6, 14, 15, 16] and hour_aqi < 150:
                activity_rating = "Favorable for outdoor workout"
            elif h in [8, 9, 10, 19, 20, 21]:
                activity_rating = "Peak traffic pollution - stay indoors"
            else:
                activity_rating = "Moderate caution"

            hourly_points.append({
                "hour": h,
                "label": time_label,
                "is_current": h == current_hour,
                "aqi": hour_aqi,
                "bucket": bucket["name"],
                "color": bucket["color"],
                "activity_rating": activity_rating
            })

        return hourly_points

    def get_city_history(self, city_name, limit=60):
        """
        Load historical records for city from city_day.csv
        """
        if not os.path.exists(CSV_PATH):
            return []

        try:
            if self.df_history is None:
                self.df_history = pd.read_csv(CSV_PATH)
                self.df_history['Date'] = pd.to_datetime(self.df_history['Date'])

            cdf = self.df_history[self.df_history['City'].str.lower() == city_name.lower()].dropna(subset=['AQI'])
            cdf = cdf.sort_values(by='Date', ascending=False).head(limit).iloc[::-1]

            results = []
            for _, r in cdf.iterrows():
                results.append({
                    "date": r['Date'].strftime("%Y-%m-%d"),
                    "aqi": round(float(r['AQI']), 1),
                    "pm25": round(float(r['PM2.5']), 1) if pd.notnull(r['PM2.5']) else None,
                    "pm10": round(float(r['PM10']), 1) if pd.notnull(r['PM10']) else None,
                    "no2": round(float(r['NO2']), 1) if pd.notnull(r['NO2']) else None,
                    "so2": round(float(r['SO2']), 1) if pd.notnull(r['SO2']) else None,
                    "co": round(float(r['CO']), 2) if pd.notnull(r['CO']) else None,
                    "o3": round(float(r['O3']), 1) if pd.notnull(r['O3']) else None,
                    "bucket": r['AQI_Bucket'] if pd.notnull(r['AQI_Bucket']) else self.get_cpcb_bucket(r['AQI'])["name"]
                })
            return results
        except Exception as e:
            print(f"Error reading history for {city_name}: {e}")
            return []

    def get_all_cities_list(self):
        """
        Returns list of all cities with metadata and default stats
        """
        output = []
        for city, data in self.city_profiles.items():
            output.append({
                "city": city,
                "state": data.get("state", "India"),
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "mean_aqi": data["stats"]["mean_aqi"],
                "median_aqi": data["stats"]["median_aqi"],
                "typical_bucket": data["stats"]["typical_bucket"],
                "badge_color": data["stats"]["badge_color"]
            })
        # Sort alphabetically
        output.sort(key=lambda x: x["city"])
        return output

# Singleton instance
ml_service = MLService()
