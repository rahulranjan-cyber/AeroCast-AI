"""
City-Wide AQI Forecasting & Monitoring Platform
Flask Backend Server
Integrates:
  - Trained ML Model (city_day.csv / HistGradientBoosting)
  - OpenWeather Air Pollution & Forecast API
  - Grok (xAI) Environmental Intelligence & Health Advisory
  - CrowdDB SQLite Citizen Incident Reporting
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from ml_service import ml_service
from weather_service import weather_service
from grok_service import grok_service
from crowd_db import crowd_db

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "aqi-ai-super-secret-key-2026")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/cities", methods=["GET"])
def get_cities():
    cities = ml_service.get_all_cities_list()
    return jsonify({"cities": cities, "total": len(cities)})

@app.route("/api/city/<city_name>/current", methods=["GET"])
def get_city_current(city_name):
    # Lookup city profile from ML service
    profile = ml_service.city_profiles.get(city_name)
    if not profile:
        # Match case-insensitively
        for k, v in ml_service.city_profiles.items():
            if k.lower() == city_name.lower():
                profile = v
                city_name = k
                break

    # Fetch live or calibrated sensor pollutants from WeatherService
    weather_data = weather_service.get_live_pollution(city_name, profile)
    pollutants = weather_data["pollutants"]

    # Compute CPCB AQI using our trained HistGradientBoosting model
    ml_prediction = ml_service.predict_aqi(pollutants)

    # Coordinates
    lat = profile["lat"] if profile else weather_data["coordinates"]["lat"]
    lon = profile["lon"] if profile else weather_data["coordinates"]["lon"]
    state = profile.get("state", "India") if profile else "India"

    response = {
        "city": city_name,
        "state": state,
        "coordinates": {"lat": lat, "lon": lon},
        "timestamp": weather_data["timestamp"],
        "source": weather_data["source"],
        "is_live_api": weather_data["status"] == "live",
        "aqi": ml_prediction["aqi"],
        "bucket": ml_prediction["bucket"],
        "color": ml_prediction["color"],
        "bg_color": ml_prediction["bg_color"],
        "description": ml_prediction["description"],
        "advisory": ml_prediction["advisory"],
        "primary_pollutant": ml_prediction["primary_pollutant"],
        "pollutant_ratios": ml_prediction["pollutant_ratios"],
        "pollutants": pollutants
    }
    return jsonify(response)

@app.route("/api/city/<city_name>/forecast", methods=["GET"])
def get_city_forecast(city_name):
    days = int(request.args.get("days", 7))
    profile = ml_service.city_profiles.get(city_name)

    # Get live pollutants to anchor the forecast
    weather_data = weather_service.get_live_pollution(city_name, profile)
    pollutants = weather_data.get("pollutants")

    # Generate 7-day forecast
    forecast_days = ml_service.forecast_city(city_name, days=days, live_pollutants=pollutants)

    # Generate 24-hour diurnal curve
    current_pred = ml_service.predict_aqi(pollutants)
    diurnal_curve = ml_service.get_city_diurnal(city_name, current_pred["aqi"])

    return jsonify({
        "city": city_name,
        "forecast_days": forecast_days,
        "diurnal_curve": diurnal_curve
    })

@app.route("/api/city/<city_name>/history", methods=["GET"])
def get_city_history(city_name):
    limit = int(request.args.get("limit", 60))
    history = ml_service.get_city_history(city_name, limit=limit)
    return jsonify({
        "city": city_name,
        "records": history,
        "total": len(history)
    })

@app.route("/api/city/<city_name>/advisory", methods=["GET"])
def get_city_advisory(city_name):
    profile = ml_service.city_profiles.get(city_name)
    weather_data = weather_service.get_live_pollution(city_name, profile)
    pollutants = weather_data.get("pollutants", {})
    ml_prediction = ml_service.predict_aqi(pollutants)

    # Get recent crowd reports for this city to provide ground context
    recent_crowd = crowd_db.get_reports(city=city_name, limit=3)
    crowd_summaries = [f"{r['hazard_type']} at {r['location_name']}: {r['description'][:60]}" for r in recent_crowd]

    # Grok health advisory
    advisory = grok_service.generate_health_advisory(
        city_name, ml_prediction["aqi"], ml_prediction["bucket"], pollutants
    )

    # Grok pollution source diagnosis
    diagnosis = grok_service.diagnose_pollution_source(
        city_name, ml_prediction["aqi"], pollutants, crowd_summaries
    )

    return jsonify({
        "city": city_name,
        "aqi": ml_prediction["aqi"],
        "bucket": ml_prediction["bucket"],
        "advisory": advisory,
        "diagnosis": diagnosis,
        "grok_active": grok_service.has_api_key()
    })

@app.route("/api/crowd/reports", methods=["GET"])
def get_crowd_reports():
    city = request.args.get("city")
    limit = int(request.args.get("limit", 50))
    reports = crowd_db.get_reports(city=city, limit=limit)
    return jsonify({"reports": reports, "count": len(reports)})

@app.route("/api/crowd/report", methods=["POST"])
def submit_crowd_report():
    data = request.get_json() or {}
    city = data.get("city", "Delhi")
    location = data.get("location_name", "Local Neighborhood")
    hazard_type = data.get("hazard_type", "Garbage/Plastic Fire")
    severity = data.get("severity", "Moderate")
    description = data.get("description", "")
    symptoms = data.get("symptoms", "")
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not description:
        return jsonify({"error": "Description is required"}), 400

    # Auto-resolve coordinates if missing
    if lat is None or lon is None:
        profile = ml_service.city_profiles.get(city)
        if profile:
            lat = profile["lat"]
            lon = profile["lon"]

    # Run Grok AI Incident Assessment
    ai_assessment_result = grok_service.assess_crowd_report(
        city=city,
        location=location,
        hazard_type=hazard_type,
        description=description,
        symptoms=symptoms
    )
    ai_summary = ai_assessment_result.get("ai_summary", "")
    estimated_impact = ai_assessment_result.get("estimated_local_aqi_increase", "+25 AQI")

    # Save to SQLite database
    report_id = crowd_db.add_report(
        city=city,
        location_name=location,
        hazard_type=hazard_type,
        severity=severity,
        description=description,
        symptoms=symptoms,
        lat=lat,
        lon=lon,
        grok_ai_assessment=ai_summary,
        estimated_aqi_impact=estimated_impact
    )

    return jsonify({
        "success": True,
        "id": report_id,
        "grok_assessment": ai_assessment_result,
        "message": "Incident report logged and evaluated by Grok AI!"
    })

@app.route("/api/crowd/vote", methods=["POST"])
def vote_crowd_report():
    data = request.get_json() or {}
    report_id = data.get("report_id")
    if not report_id:
        return jsonify({"error": "report_id is required"}), 400

    new_votes = crowd_db.upvote_report(report_id)
    return jsonify({"success": True, "upvotes": new_votes})

@app.route("/api/crowd/stats", methods=["GET"])
def get_crowd_stats():
    stats = crowd_db.get_crowd_stats()
    return jsonify(stats)

@app.route("/api/chat", methods=["POST"])
def chat_copilot():
    data = request.get_json() or {}
    messages = data.get("messages", [])
    context = data.get("context", {})

    reply = grok_service.chat_copilot(messages, context)
    return jsonify({
        "reply": reply,
        "grok_active": grok_service.has_api_key()
    })

@app.route("/api/settings", methods=["GET", "POST"])
def handle_settings():
    if request.method == "POST":
        data = request.get_json() or {}
        ow_key = data.get("openweather_key", "").strip()
        grok_key = data.get("grok_key", "").strip()

        # Update in-memory service keys
        if ow_key:
            weather_service.set_api_key(ow_key)
        if grok_key:
            grok_service.set_api_key(grok_key)

        # Write or update .env file
        try:
            env_lines = []
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            existing_vars = {}
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            k, v = line.strip().split("=", 1)
                            existing_vars[k.strip()] = v.strip()

            if ow_key:
                existing_vars["OPENWEATHER_API_KEY"] = ow_key
            if grok_key:
                existing_vars["GROK_API_KEY"] = grok_key

            with open(env_path, "w", encoding="utf-8") as f:
                for k, v in existing_vars.items():
                    f.write(f"{k}={v}\n")
        except Exception as e:
            print(f"Error persisting .env: {e}")

        return jsonify({
            "success": True,
            "openweather_configured": weather_service.has_api_key(),
            "grok_configured": grok_service.has_api_key()
        })

    # GET request
    return jsonify({
        "openweather_configured": weather_service.has_api_key(),
        "openweather_masked": weather_service.api_key[:4] + "..." + weather_service.api_key[-4:] if weather_service.has_api_key() else "",
        "grok_configured": grok_service.has_api_key(),
        "grok_masked": grok_service.api_key[:4] + "..." + grok_service.api_key[-4:] if grok_service.has_api_key() else ""
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting City-Wide AQI Forecasting Platform on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
