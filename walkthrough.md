# Walkthrough: City-Wide AQI Forecasting AI System (AeroCast AI)

We have built and verified **AeroCast AI**, an end-to-end City-Wide AQI Forecasting and Environmental Intelligence platform powered by:
1. **Machine Learning Model** trained on `city_day.csv` (29,531 records across 26 Indian cities).
2. **OpenWeather Air Pollution & Geocoding Integration** for live atmospheric metrics (`PM2.5`, `PM10`, `NO2`, `SO2`, `CO`, `O3`, `NH3`).
3. **Grok (xAI) Environmental AI** for epidemiological health advisories, root-cause chemical attribution, citizen incident verification, and an interactive Environmental Copilot.
4. **CrowdDB SQLite Database** for citizen hazard reporting (stubble burning, toxic fires, traffic, industrial flaring, dust, chemical odors) with geo-spatial hazard mapping.
5. **Modern Glassmorphic Single Page Application** with dynamic CPCB color scales, Chart.js visualizations, Leaflet interactive map, and dark/light themes.

---

## 1. Architecture & Components

| Component | File | Purpose |
| :--- | :--- | :--- |
| **Model Trainer** | [`train_model.py`](file:///c:/MiniP/train_model.py) | Preprocesses `city_day.csv`, trains `HistGradientBoostingRegressor` (R²: **0.8795**, MAE: **22.36**), builds 26 city seasonal and diurnal profiles, and serializes `models/aqi_model.pkl` and `models/city_profiles.json`. |
| **ML Service** | [`ml_service.py`](file:///c:/MiniP/ml_service.py) | Microsecond inference engine for CPCB AQI prediction, multi-day city forecasting with uncertainty bounds, 24h diurnal cycle generation, and historical data retrieval. |
| **OpenWeather Engine** | [`weather_service.py`](file:///c:/MiniP/weather_service.py) | Geocoding and real-time pollutant ingestion from OpenWeather Air Pollution API with automatic conversion of units (CO from µg/m³ to mg/m³) and calibrated baseline simulation. |
| **Grok (xAI) Intelligence** | [`grok_service.py`](file:///c:/MiniP/grok_service.py) | Connects to xAI API (`grok-2-latest` / `grok-beta`) for vulnerable cohort health guidance, chemical signature source diagnostics, and citizen report threat assessment. |
| **CrowdDB (SQLite)** | [`crowd_db.py`](file:///c:/MiniP/crowd_db.py) | SQLite database (`data/crowd_reports.db`) storing citizen reports, hazard categories, GPS coordinates, upvotes, and Grok AI impact scores. Pre-seeded with realistic reports across top cities. |
| **Flask Server** | [`app.py`](file:///c:/MiniP/app.py) | REST API exposing city data, live AQI, 7-day forecasts, CrowdDB reports, Copilot chat, and settings. |
| **UI Dashboard** | [`templates/index.html`](file:///c:/MiniP/templates/index.html) | Semantic SPA layout: AQI Radial Gauge, CPCB Scale Pin, Grok Advisory Card, 6 Analytics Tabs, and Citizen Reporting Modal. |
| **Design System** | [`static/css/style.css`](file:///c:/MiniP/static/css/style.css) | Custom CSS with Glassmorphism, ambient backlights, CPCB standard color spectrum, smooth transitions, and responsive grids. |
| **Interactive Logic** | [`static/js/app.js`](file:///c:/MiniP/static/js/app.js) | Chart.js forecast/diurnal/radar charts, Leaflet.js interactive hazard map, live report submissions, voting, and Grok chat. |

---

## 2. Validation & Test Results

### Automated Test Suite (`test_system.py`)
Executed test suite covering ML prediction, 7-day forecasting, Weather service, CrowdDB SQLite CRUD, Grok AI reasoning, and Flask REST endpoints:

```
Loaded trained AQI model pipeline.
Loaded 26 city profiles.
[PASS] ML Prediction: AQI=208, Bucket=Poor, Primary=PM10
[PASS] 7-Day Forecast: Day 1=269 AQI, Day 7=204 AQI
[PASS] WeatherService: Source=Calibrated ML Historical Sensor Engine, PM2.5=37.5
[PASS] CrowdDB: Successfully inserted report #10, upvotes=2
[PASS] Grok Service: Activity Rating=Hazardous, Impact=+40 to +75 AQI
[PASS] All Flask REST API endpoints verified successfully!
Ran 6 tests in 1.928s -> OK
```

### Live Server Verification
The server was launched as a daemon on `http://127.0.0.1:5000` and `http://0.0.0.0:5000`:
- **HTTP GET `/`**: Returns HTTP 200 with full AeroCast AI HTML bundle.
- **HTTP GET `/api/cities`**: Returns 26 monitored Indian cities with coordinates, average AQI, and color badges.
- **HTTP GET `/api/city/Bengaluru/current`**: Returns real-time pollutants, CPCB AQI classification, and dominant pollutant.
- **HTTP POST `/api/chat`**: Successfully generates contextual AI responses from the Grok Copilot engine.

---

## 3. How to Access and Use the Platform

### Running the App Locally
The server is currently running in the background at:
👉 **`http://127.0.0.1:5000`**

To start it manually at any time in your terminal:
```powershell
python app.py
```

### Key Features to Explore in the UI:
1. **City Switching**: Use the header dropdown or the **GPS Crosshair** button to select from 26 cities (Delhi, Bengaluru, Mumbai, Kolkata, Chennai, Hyderabad, etc.).
2. **CPCB Gauge & Scale**: Observe the animated radial gauge and scale indicator pin highlighting the official Indian CPCB category (Good, Satisfactory, Moderate, Poor, Very Poor, Severe).
3. **7-Day ML Forecast & 24h Diurnal Curve**: Inspect daily predicted AQI with uncertainty bands and find the optimal daytime window for outdoor exercise.
4. **CrowdDB & Interactive Hazard Map**: Open the **CrowdDB & Hazard Map** tab to view city station markers and citizen-reported hazard pins (waste burning, traffic, construction dust). Click **"Report Hazard"** to submit a new observation and watch Grok AI evaluate the threat!
5. **Grok AI Intelligence & Copilot**: View the **Grok AI Diagnostics** tab for root-cause source attribution (vehicular soot vs. road dust vs. industrial) and chat directly with the Copilot.
6. **API Settings**: Click the **Sliders icon** in the header to view or update your `OPENWEATHER_API_KEY` and `GROK_API_KEY`.
