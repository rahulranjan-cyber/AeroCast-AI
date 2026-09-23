# AeroCast AI — City-Wide AQI Forecasting & CrowdDB Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.8-orange.svg)](https://scikit-learn.org/)
[![OpenWeather](https://img.shields.io/badge/OpenWeather-Air_Pollution_API-yellow.svg)](https://openweathermap.org/api/air-pollution)
[![xAI](https://img.shields.io/badge/Grok-xAI_API-red.svg)](https://x.ai/)
[![Database](https://img.shields.io/badge/SQLite-CrowdDB-lightgrey.svg)](https://sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent, full-stack Air Quality Index (AQI) forecasting and environmental intelligence platform. AeroCast AI combines **machine learning trained on 6 years of Indian city air quality data**, live **OpenWeather Air Pollution API telemetry**, **Grok (xAI) health & source attribution AI**, and a citizen-driven **CrowdDB incident reporting database** with interactive maps and charts.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Directory Structure](#directory-structure)
- [Dataset & Model Performance](#dataset--model-performance)
- [Installation & Setup](#installation--setup)
- [Configuration & API Keys](#configuration--api-keys)
- [Training & Re-training](#training--re-training)
- [Running the Application](#running-the-application)
- [REST API Reference](#rest-api-reference)
- [CrowdDB (Citizen Hazard Database)](#crowddb-citizen-hazard-database)
- [Grok AI Integration](#grok-ai-integration)
- [CPCB AQI Standard Reference](#cpcb-aqi-standard-reference)
- [Automated Testing](#automated-testing)
- [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## Overview

Urban air pollution is a critical public health challenge characterized by rapid shifts, extreme seasonal smog spikes, and hyper-local combustion hazards (such as agricultural burning, industrial flaring, and garbage fires).

**AeroCast AI** solves this with a multi-layered approach:
1. **Predictive Analytics**: A trained gradient boosted regression pipeline predicting official CPCB AQI from multi-pollutant concentrations with an **$R^2$ of ~0.88**.
2. **7-Day Forecasting**: Time-series seasonal projections with diurnal hourly curves identifying the safest daytime exercise windows.
3. **Real-Time Telemetry**: OpenWeather API integration for live particulate and gas measurements across monitored cities.
4. **AI-Powered Diagnostics**: Grok (xAI) analyzes chemical stoichiometry ($\text{PM}_{2.5}/\text{PM}_{10}$ ratios, $\text{NO}_2$, $\text{SO}_2$) to determine emission sources and generate personalized health advisories.
5. **Crowd-Sourced Intelligence (CrowdDB)**: Citizen science portal to log local hazard events, plot them on a live map, and obtain instant Grok AI hazard severity scores.

---

## System Architecture

```text
                               +------------------------------------------+
                               |              Web Browser UI              |
                               |  - Glassmorphic Responsive Dashboard     |
                               |  - Chart.js (Forecast, Diurnal, Radar)   |
                               |  - Leaflet Map (Stations & Hazards)      |
                               |  - Grok AI Environmental Copilot Chat    |
                               |  - CrowdDB Incident Report Modal         |
                               +--------------------+---------------------+
                                                    | REST API / JSON
                                                    v
                               +------------------------------------------+
                               |           Flask Backend Server           |
                               |            (app.py / :5000)              |
                               +----------+---------+---------+-----------+
                                          |         |         |
                   +----------------------+         |         +-----------------------+
                   v                                v                                 v
          +------------------+             +------------------+             +--------------------+
          |  Trained ML Model|             |  OpenWeather API |             |   Grok (xAI) API   |
          | - HistGradBoost  |             | - Geocoding      |             | - Health Advisory  |
          | - CPCB Scale     |             | - Live Pollutants|             | - Cause Diagnosis  |
          | - 7-Day Forecast |             | - 5-Day Forecast |             | - Report AI Score  |
          | - 26 City Baseln |             +------------------+             | - Live Copilot     |
          +------------------+                                              +--------------------+
                   ^                                                                  |
                   |                                                                  v
                   |                       +------------------+                       |
                   +-----------------------|  CrowdDB (SQLite)|<----------------------+
                                           | - Citizen Reports|  (AI-verified hazard
                                           | - Map Hotspots   |   and impact score)
                                           | - Upvotes/Verify |
                                           +------------------+
```

---

## Key Features

- **Trained ML AQI Prediction**: Calculates exact CPCB Indian AQI from $\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, $\text{SO}_2$, $\text{CO}$, $\text{O}_3$, and $\text{NH}_3$.
- **7-Day Multi-Step Forecast**: Daily projections with confidence intervals based on seasonal harmonics and live atmospheric vectors.
- **24-Hour Diurnal Curve**: Hourly pollution trajectories highlighting morning rush spikes and optimal outdoor activity windows.
- **OpenWeather Telemetry**: Live sensor ingestion with automatic unit conversion ($\text{CO}$ from $\mu\text{g/m}^3$ to $\text{mg/m}^3$) and fallback calibration.
- **Grok AI Environmental Engine**:
  - Epidemiological health advisories for sensitive cohorts (Asthma, Children, Elderly, Athletes, Commuters).
  - Atmospheric root-cause diagnosis (vehicular exhaust vs. resuspended crustal dust vs. industrial plumes).
  - Citizen incident credibility and local AQI impact evaluation ($+20$ to $+75$ AQI).
  - Conversational AI Copilot with prompt suggestions.
- **CrowdDB & Interactive Hazard Map**:
  - SQLite-backed community incident logging.
  - Interactive Leaflet.js map with city station circles and hazard markers.
  - Community upvoting to validate active incidents.
- **High-Aesthetic UI**:
  - Glassmorphic dark and light modes.
  - Radial animated AQI gauge and CPCB scale spectrum pin.
  - Dynamic radar and line charts via Chart.js.
  - Geolocation detection for nearest monitored city.

---

## Directory Structure

```text
c:\MiniP\
├── app.py                 # Main Flask server and REST API routes
├── train_model.py         # Model training script on city_day.csv
├── ml_service.py          # ML inference, forecasting, and city profile engine
├── weather_service.py     # OpenWeather Air Pollution API & geocoding service
├── grok_service.py        # Grok (xAI) API health advisory & copilot engine
├── crowd_db.py            # SQLite CrowdDB module and seed manager
├── test_system.py         # Unit tests and end-to-end API verification suite
├── city_day.csv           # 2015–2020 Indian Cities Air Quality Dataset
├── requirements.txt       # Python package dependencies
├── .env                   # Environment variables (API keys)
├── .env.example           # Example configuration template
├── data/
│   └── crowd_reports.db   # SQLite database for citizen incident reports
├── models/
│   ├── aqi_model.pkl      # Serialized trained HistGradientBoosting model
│   └── city_profiles.json # Statistical & seasonal baseline profiles for 26 cities
├── templates/
│   └── index.html         # Modern Single Page Application (SPA) dashboard
└── static/
    ├── css/
    │   └── style.css      # Custom design system with glassmorphism & CPCB styles
    └── js/
        └── app.js         # Chart.js, Leaflet map, CrowdDB, and Grok chat logic
```

---

## Dataset & Model Performance

The model is trained on [`city_day.csv`](file:///c:/MiniP/city_day.csv), containing daily air quality readings across **26 Indian cities** from **2015 to 2020** (29,531 records).

### Features Used:
- $\text{PM}_{2.5}$ (Fine particulate matter $<2.5\,\mu\text{m}$)
- $\text{PM}_{10}$ (Inhalable coarse particulate $<10\,\mu\text{m}$)
- $\text{NO}_2$ (Nitrogen dioxide)
- $\text{CO}$ (Carbon monoxide)
- $\text{SO}_2$ (Sulfur dioxide)
- $\text{O}_3$ (Surface ozone)
- $\text{NH}_3$ (Ammonia)

### Model Architecture:
- Algorithm: `HistGradientBoostingRegressor` (Scikit-Learn)
- Target: CPCB Air Quality Index (`AQI`) & Category (`AQI_Bucket`)
- Regularization: L2 regularization ($0.1$), early stopping, depth $= 8$

### Validation Metrics:
| Metric | Value | Meaning |
| :--- | :--- | :--- |
| **$R^2$ Score** | **0.8795** | 88% of AQI variance explained by chemical components |
| **MAE** | **22.36** | Average error of only ~22 points across a 0–500 scale |
| **RMSE** | **45.84** | Robustness against extreme outlier spikes |

---

## Installation & Setup

### Prerequisites
- Python **3.10** or higher
- `pip` package manager

### 1. Clone or Open Project Directory
```powershell
cd c:\MiniP
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## Configuration & API Keys

Create or edit your `.env` file in the project root:

```ini
# OpenWeather API Key (from https://openweathermap.org/api)
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Grok (xAI) API Key (from https://console.x.ai/)
GROK_API_KEY=your_grok_xai_api_key_here

# Optional: Flask Secret Key and Port
SECRET_KEY=your_custom_secret_key
PORT=5000
```

> [!TIP]
> **In-App Key Management**: You can also configure your keys directly inside the web UI by clicking the **Sliders icon (Settings)** in the top-right header! Keys entered in the UI are applied immediately and automatically saved to `.env`.

> [!NOTE]
> **Offline / Fallback Resilience**: If API keys are not yet configured or rate limits are reached, the system automatically runs in **Calibrated Simulation Mode** using the trained dataset baselines and rule-based AI reasoning, ensuring the UI remains 100% operational.

---

## Training & Re-training

To re-train the machine learning model on [`city_day.csv`](file:///c:/MiniP/city_day.csv):

```powershell
python train_model.py
```

This will:
1. Clean and impute missing pollutant data.
2. Train the `HistGradientBoostingRegressor`.
3. Output $R^2$, MAE, and RMSE metrics.
4. Save the pipeline to `models/aqi_model.pkl`.
5. Extract seasonal harmonics and diurnal curves into `models/city_profiles.json`.

---

## Running the Application

To start the Flask development server:

```powershell
python app.py
```

Once running, navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the main SPA Dashboard |
| `GET` | `/api/cities` | Returns all 26 cities with coordinates, average AQI, and color badges |
| `GET` | `/api/city/<name>/current` | Current AQI, CPCB bucket, dominant pollutant, and chemical concentrations |
| `GET` | `/api/city/<name>/forecast?days=7` | 7-day predicted AQI trend with uncertainty intervals and 24h diurnal curve |
| `GET` | `/api/city/<name>/history?limit=60` | Historical daily records from 2015–2020 for the selected city |
| `GET` | `/api/city/<name>/advisory` | Grok AI health guidance for sensitive cohorts and atmospheric source diagnosis |
| `POST` | `/api/chat` | Grok AI Copilot conversational endpoint |
| `GET` | `/api/crowd/reports?city=<name>` | Retrieves citizen hazard incident reports (filterable by city) |
| `POST` | `/api/crowd/report` | Submits a new citizen report; automatically triggers Grok AI threat evaluation |
| `POST` | `/api/crowd/vote` | Upvotes / confirms an active hazard report |
| `GET` | `/api/crowd/stats` | Aggregated statistics on report types, cities, and severity counts |
| `GET` | `/api/settings` | Returns connection status of OpenWeather and Grok API keys |
| `POST` | `/api/settings` | Saves new OpenWeather and Grok keys and updates `.env` |

---

## CrowdDB (Citizen Hazard Database)

CrowdDB empowers citizens to report localized pollution sources that official fixed monitoring stations might miss.

### Supported Hazard Categories:
- 🔥 **Garbage / Plastic Burning**: Burning of synthetic municipal solid waste.
- 🌾 **Stubble / Crop Residue Burning**: Agricultural open burning.
- 🚗 **Heavy Traffic Gridlock**: Prolonged vehicular idling in dense corridors.
- 🏭 **Industrial Emissions**: Low-efficiency smokestack or foundry flaring.
- 🏗️ **Construction Dust**: Uncovered aggregate hauling or dry concrete mixing.
- ⚠️ **Chemical / Pungent Odor**: Volatile organic compound leaks or toxic fumes.

### Database Schema (`data/crowd_reports.db`):
```sql
CREATE TABLE crowd_reports (
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
);
```

---

## Grok AI Integration

AeroCast AI integrates with the **xAI Grok API** (`grok-2-latest` / `grok-beta`) for four key capabilities:

1. **Epidemiological Health Advisories**:
   Contextual guidance for:
   - Asthmatics & Respiratory patients (bronchodilator readiness)
   - Children & Elderly (outdoor restriction timings)
   - Athletes (workout window recommendations)
   - Commuters (mask grade recommendations: N95 vs. surgical)
2. **Pollution Source Attribution**:
   Analyzes chemical ratios (e.g., $\text{PM}_{2.5}/\text{PM}_{10} > 0.65$ indicates combustion soot; high $\text{NO}_2$ indicates vehicular traffic; high $\text{SO}_2$ indicates industrial coal burning).
3. **Citizen Incident Assessment**:
   Evaluates each CrowdDB submission in real time, assigns credibility, and estimates localized AQI surges (e.g. $+35$ to $+60$ AQI).
4. **Interactive Environmental Copilot**:
   An embedded chat drawer where users can ask questions regarding air purifiers, mask types, ventilation, or green mitigation.

---

## CPCB AQI Standard Reference

AeroCast AI adheres to the official **Central Pollution Control Board (CPCB)** National Air Quality Index standards:

| AQI Band | Category | Color | Health Implications |
| :---: | :---: | :---: | :--- |
| **0 – 50** | **Good** | `#10b981` (Green) | Minimal health impact; ideal for all outdoor activities. |
| **51 – 100** | **Satisfactory** | `#84cc16` (Lime) | Minor breathing discomfort to sensitive individuals. |
| **101 – 200** | **Moderate** | `#f59e0b` (Amber) | Breathing discomfort to people with lung, asthma, and heart diseases. |
| **201 – 300** | **Poor** | `#f97316` (Orange) | Breathing discomfort to most people on prolonged exposure; N95 recommended. |
| **301 – 400** | **Very Poor** | `#ef4444` (Crimson) | Respiratory illness on prolonged exposure; avoid morning outdoor workouts. |
| **401 – 500+** | **Severe** | `#881337` (Maroon) | Health emergency; affects healthy people and severely impacts vulnerable groups. |

---

## Automated Testing

A comprehensive test suite verifies ML predictions, forecasting, WeatherService, CrowdDB, Grok AI logic, and Flask endpoints:

```powershell
python test_system.py
```

### Expected Output:
```text
......
----------------------------------------------------------------------
Ran 6 tests in 1.9s

OK
[PASS] ML Prediction: AQI=208, Bucket=Poor, Primary=PM10
[PASS] 7-Day Forecast: Day 1=269 AQI, Day 7=204 AQI
[PASS] WeatherService: Source=Calibrated ML Historical Sensor Engine, PM2.5=37.5
[PASS] CrowdDB: Successfully inserted report #10, upvotes=2
[PASS] Grok Service: Activity Rating=Hazardous, Impact=+40 to +75 AQI
[PASS] All Flask REST API endpoints verified successfully!
```

---

## Troubleshooting & FAQs

### Q: Why does the app show "Calibrated ML Sensor" instead of OpenWeather?
**A:** This indicates that your `OPENWEATHER_API_KEY` is not yet set in `.env` or has reached its rate limit. The app smoothly falls back to calibrated simulation so you can explore all features. Open the **Settings modal (Sliders icon)** in the UI to input your key.

### Q: How do I save my `.env` file if I edited it in an IDE?
**A:** Ensure you press **`Ctrl + S`** in your editor to flush the buffer to disk.

### Q: Can I run this on a different port or host?
**A:** Yes! Pass the port in `.env` or set it in your environment:
```powershell
$env:PORT = "8080"; python app.py
```

### Q: How do I reset or clear the CrowdDB database?
**A:** Simply delete `data/crowd_reports.db`. The application will automatically recreate and re-seed the initial reports upon startup.

---

## License

This project is licensed under the MIT License — feel free to use and extend for academic, personal, or commercial environmental applications.
