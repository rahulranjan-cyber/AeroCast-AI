"""
City-Wide AQI Forecasting Model Training
Dataset: city_day.csv (Indian Cities Air Quality 2015-2020)
Trains:
  1. HistGradientBoostingRegressor to estimate CPCB AQI from pollutant levels
     (PM2.5, PM10, NO2, CO, SO2, O3, NH3) matching OpenWeather Air Pollution metrics.
  2. City-specific time-series baseline profiles, seasonal harmonics, and diurnal variations.
Saves:
  - models/aqi_model.pkl
  - models/city_profiles.json
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Coordinates for major cities in the dataset
CITY_COORDINATES = {
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714, "state": "Gujarat"},
    "Aizawl": {"lat": 23.7271, "lon": 92.7176, "state": "Mizoram"},
    "Amaravati": {"lat": 16.5417, "lon": 80.5150, "state": "Andhra Pradesh"},
    "Amritsar": {"lat": 31.6340, "lon": 74.8723, "state": "Punjab"},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka"},
    "Bhopal": {"lat": 23.2599, "lon": 77.4126, "state": "Madhya Pradesh"},
    "Brajrajnagar": {"lat": 21.8260, "lon": 83.9189, "state": "Odisha"},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794, "state": "Chandigarh"},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu"},
    "Coimbatore": {"lat": 11.0168, "lon": 76.9558, "state": "Tamil Nadu"},
    "Delhi": {"lat": 28.6139, "lon": 77.2090, "state": "Delhi"},
    "Ernakulam": {"lat": 9.9816, "lon": 76.2999, "state": "Kerala"},
    "Gurugram": {"lat": 28.4595, "lon": 77.0266, "state": "Haryana"},
    "Guwahati": {"lat": 26.1445, "lon": 91.7362, "state": "Assam"},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867, "state": "Telangana"},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873, "state": "Rajasthan"},
    "Jorapokhar": {"lat": 23.7056, "lon": 86.4132, "state": "Jharkhand"},
    "Kochi": {"lat": 9.9312, "lon": 76.2673, "state": "Kerala"},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "state": "West Bengal"},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462, "state": "Uttar Pradesh"},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "state": "Maharashtra"},
    "Patna": {"lat": 25.5941, "lon": 85.1376, "state": "Bihar"},
    "Shillong": {"lat": 25.5788, "lon": 91.8933, "state": "Meghalaya"},
    "Talcher": {"lat": 20.9509, "lon": 85.2166, "state": "Odisha"},
    "Thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366, "state": "Kerala"},
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185, "state": "Andhra Pradesh"}
}

def get_cpcb_bucket(aqi):
    """Classify AQI according to Indian Central Pollution Control Board (CPCB) standards"""
    if aqi <= 50:
        return "Good", "Minimal impact", "#10b981"
    elif aqi <= 100:
        return "Satisfactory", "Minor breathing discomfort to sensitive people", "#84cc16"
    elif aqi <= 200:
        return "Moderate", "Breathing discomfort to the people with lungs, asthma and heart diseases", "#f59e0b"
    elif aqi <= 300:
        return "Poor", "Breathing discomfort to most people on prolonged exposure", "#f97316"
    elif aqi <= 400:
        return "Very Poor", "Respiratory illness on prolonged exposure", "#ef4444"
    else:
        return "Severe", "Affects healthy people and seriously impacts those with existing diseases", "#881337"

def train():
    os.makedirs("models", exist_ok=True)
    csv_path = "city_day.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found!")

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows. Columns: {df.columns.tolist()}")

    # Parse date and temporal features
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.month
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['DayOfYear'] = df['Date'].dt.dayofyear

    # Features matching OpenWeather Air Pollution components
    core_features = ['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'NH3']
    
    # Filter dataset for rows with valid AQI and PM2.5
    valid_df = df.dropna(subset=['AQI', 'PM2.5']).copy()
    print(f"Rows with valid AQI & PM2.5: {len(valid_df)}")

    # Impute missing pollutant features with column medians
    median_imputes = {}
    for col in core_features:
        med = float(valid_df[col].median() if col in valid_df and valid_df[col].notnull().sum() > 0 else 20.0)
        median_imputes[col] = med
        valid_df[col] = valid_df[col].fillna(med)

    X = valid_df[core_features]
    y = valid_df['AQI']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    print(f"Training HistGradientBoostingRegressor on {len(X_train)} samples...")
    model = HistGradientBoostingRegressor(
        max_iter=250,
        learning_rate=0.08,
        max_depth=8,
        min_samples_leaf=20,
        l2_regularization=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = float(r2_score(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    print(f"Model Evaluation Metrics:")
    print(f"  R2 Score : {r2:.4f}")
    print(f"  MAE      : {mae:.2f}")
    print(f"  RMSE     : {rmse:.2f}")

    # Save model artifact
    model_artifact = {
        "model": model,
        "features": core_features,
        "median_imputes": median_imputes,
        "metrics": {"r2": r2, "mae": mae, "rmse": rmse}
    }
    model_path = os.path.join("models", "aqi_model.pkl")
    joblib.dump(model_artifact, model_path)
    print(f"Saved model pipeline to {model_path}")

    # Build comprehensive City Profiles
    print("Generating city-specific statistical profiles and seasonal baselines...")
    city_profiles = {}
    all_cities = sorted(df['City'].unique().tolist())

    for city in all_cities:
        cdf = df[df['City'] == city].copy()
        if len(cdf) == 0:
            continue

        valid_aqi = cdf['AQI'].dropna()
        mean_aqi = float(valid_aqi.mean()) if len(valid_aqi) > 0 else 120.0
        median_aqi = float(valid_aqi.median()) if len(valid_aqi) > 0 else 110.0
        min_aqi = float(valid_aqi.min()) if len(valid_aqi) > 0 else 30.0
        max_aqi = float(valid_aqi.max()) if len(valid_aqi) > 0 else 400.0

        # Monthly AQI seasonal profile (1 to 12)
        monthly_stats = {}
        for m in range(1, 13):
            m_data = cdf[cdf['Month'] == m]['AQI'].dropna()
            monthly_stats[str(m)] = float(m_data.mean()) if len(m_data) > 0 else mean_aqi

        # Average pollutant concentrations
        pollutant_means = {}
        for col in core_features + ['NO', 'NOx', 'Benzene', 'Toluene', 'Xylene']:
            if col in cdf and cdf[col].notnull().sum() > 0:
                pollutant_means[col] = round(float(cdf[col].mean()), 2)
            else:
                pollutant_means[col] = round(median_imputes.get(col, 15.0), 2)

        # Diurnal curve multipliers (standard urban 24h pattern: morning peak at 8-10am, evening peak at 7-10pm)
        diurnal_multipliers = [
            0.82, 0.78, 0.75, 0.72, 0.74, 0.85, 1.10, 1.25, 1.30, 1.20,
            1.05, 0.95, 0.90, 0.85, 0.84, 0.86, 0.94, 1.08, 1.22, 1.32,
            1.28, 1.18, 1.05, 0.92
        ]

        coords = CITY_COORDINATES.get(city, {"lat": 20.5937, "lon": 78.9629, "state": "India"})

        bucket_name, health_desc, badge_color = get_cpcb_bucket(median_aqi)

        city_profiles[city] = {
            "city": city,
            "state": coords.get("state", "India"),
            "lat": coords["lat"],
            "lon": coords["lon"],
            "records_count": len(cdf),
            "stats": {
                "mean_aqi": round(mean_aqi, 1),
                "median_aqi": round(median_aqi, 1),
                "min_aqi": round(min_aqi, 1),
                "max_aqi": round(max_aqi, 1),
                "typical_bucket": bucket_name,
                "badge_color": badge_color
            },
            "monthly_seasonality": monthly_stats,
            "typical_pollutants": pollutant_means,
            "diurnal_multipliers": diurnal_multipliers
        }

    profiles_path = os.path.join("models", "city_profiles.json")
    with open(profiles_path, "w", encoding="utf-8") as f:
        json.dump(city_profiles, f, indent=2)
    print(f"Saved {len(city_profiles)} city profiles to {profiles_path}")

    # Summary table
    print("\nTraining complete! Top cities overview:")
    for city in ["Delhi", "Bengaluru", "Mumbai", "Kolkata", "Chennai", "Hyderabad"]:
        if city in city_profiles:
            cp = city_profiles[city]
            print(f"  {city:12} | Avg AQI: {cp['stats']['mean_aqi']} | Typical: {cp['stats']['typical_bucket']} | PM2.5: {cp['typical_pollutants']['PM2.5']} ug/m3")

if __name__ == "__main__":
    train()
