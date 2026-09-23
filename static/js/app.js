/**
 * AeroCast AI — Client-Side Application Logic
 * Integrates Chart.js, Leaflet Map, CrowdDB Incident Feed, and Grok AI Copilot
 */

// Application State
const state = {
  currentCity: "Delhi",
  cities: [],
  currentData: null,
  forecastData: null,
  crowdReports: [],
  crowdFilter: "all",
  charts: {
    forecast: null,
    pollutants: null,
    diurnal: null,
    history: null
  },
  map: null,
  mapCityMarkers: [],
  mapHazardMarkers: []
};

// CPCB 24-Hour Limits (µg/m³, except CO in mg/m³)
const CPCB_LIMITS = {
  "PM2.5": 60,
  "PM10": 100,
  "NO2": 80,
  "SO2": 80,
  "CO": 2.0,
  "O3": 100,
  "NH3": 400
};

// Initialize Application on DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  initTheme();
  initTabs();
  initModals();
  initChat();
  initLeafletMap();
  
  await loadCities();
  await refreshCityData(state.currentCity);
  await loadCrowdReports();
  await checkApiSettings();

  // Periodic polling for crowd reports & subtle time update
  setInterval(loadCrowdReports, 30000);
});

/* ==========================================================================
   Theme Management
   ========================================================================== */
function initTheme() {
  const savedTheme = localStorage.getItem("aerocast_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);

  document.getElementById("btnThemeToggle").addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("aerocast_theme", next);
    updateThemeIcon(next);
    
    // Re-render charts with theme-appropriate colors
    if (state.currentData) {
      renderForecastChart(state.forecastData?.forecast_days || []);
      renderPollutantsChart(state.currentData.pollutants);
      renderDiurnalChart(state.forecastData?.diurnal_curve || []);
    }
  });
}

function updateThemeIcon(theme) {
  const icon = document.querySelector("#btnThemeToggle i");
  if (icon) {
    icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
  }
}

/* ==========================================================================
   Tab Navigation
   ========================================================================== */
function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      
      tabButtons.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      
      btn.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");

      // Invalidate Leaflet map size when switching to map tab
      if (targetId === "tabCrowd" && state.map) {
        setTimeout(() => state.map.invalidateSize(), 150);
      }

      // Lazy load historical data if tab chosen
      if (targetId === "tabHistory" && !state.charts.history) {
        loadHistoricalTrends(state.currentCity);
      }
    });
  });
}

/* ==========================================================================
   Data Fetching & City Loading
   ========================================================================== */
async function loadCities() {
  try {
    const res = await fetch("/api/cities");
    const data = await res.json();
    state.cities = data.cities || [];

    const select = document.getElementById("citySelect");
    const reportSelect = document.getElementById("reportCity");
    select.innerHTML = "";
    reportSelect.innerHTML = "";

    state.cities.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.city;
      opt.textContent = `${c.city} (${c.state})`;
      if (c.city === state.currentCity) opt.selected = true;
      select.appendChild(opt);

      const rOpt = document.createElement("option");
      rOpt.value = c.city;
      rOpt.textContent = c.city;
      if (c.city === state.currentCity) rOpt.selected = true;
      reportSelect.appendChild(rOpt);
    });

    select.addEventListener("change", (e) => {
      state.currentCity = e.target.value;
      refreshCityData(state.currentCity);
      filterCrowdReports();
    });

    // Geolocate closest city button
    document.getElementById("btnGeolocate").addEventListener("click", findClosestCity);

  } catch (err) {
    console.error("Error loading cities:", err);
    showToast("Error loading city catalog", "error");
  }
}

async function refreshCityData(cityName) {
  try {
    showLoadingState(true);

    // 1. Fetch Current AQI & Pollutants
    const curRes = await fetch(`/api/city/${encodeURIComponent(cityName)}/current`);
    const currentData = await curRes.json();
    state.currentData = currentData;
    updateHeroDisplay(currentData);

    // 2. Fetch 7-Day Forecast & Diurnal Curve
    const fcRes = await fetch(`/api/city/${encodeURIComponent(cityName)}/forecast`);
    const forecastData = await fcRes.json();
    state.forecastData = forecastData;

    renderForecastCards(forecastData.forecast_days || []);
    renderForecastChart(forecastData.forecast_days || []);
    renderDiurnalChart(forecastData.diurnal_curve || []);

    // 3. Render Pollutant Bars & Breakdown
    renderPollutantBars(currentData.pollutants);
    renderPollutantsChart(currentData.pollutants);

    // 4. Fetch Grok AI Health Advisory & Root-Cause Diagnosis
    fetchGrokAdvisory(cityName);

    // 5. Update Map Center
    if (state.map && currentData.coordinates) {
      state.map.setView([currentData.coordinates.lat, currentData.coordinates.lon], 9, { animate: true });
    }

    showLoadingState(false);
  } catch (err) {
    console.error("Error refreshing city data:", err);
    showToast(`Failed to load data for ${cityName}`, "error");
    showLoadingState(false);
  }
}

/* ==========================================================================
   Hero Display & Visual Gauge Updates
   ========================================================================== */
function updateHeroDisplay(data) {
  document.getElementById("displayLocation").textContent = `${data.city}, ${data.state}`;
  document.getElementById("displayTimestamp").textContent = `Updated: ${data.timestamp}`;
  document.getElementById("sourceLabel").textContent = data.source;

  const aqiEl = document.getElementById("displayAqi");
  animateNumber(aqiEl, parseInt(aqiEl.textContent) || 0, data.aqi, 800);

  const bucketBadge = document.getElementById("displayBucketBadge");
  bucketBadge.textContent = data.bucket;
  bucketBadge.style.backgroundColor = data.bg_color;
  bucketBadge.style.color = data.color;

  const ring = document.getElementById("aqiRadialRing");
  ring.style.borderColor = data.color;
  ring.style.boxShadow = `0 0 30px ${data.color}40`;

  document.getElementById("displayAqiDesc").textContent = data.description;
  document.getElementById("displayDominantPollutant").textContent = data.primary_pollutant;

  // Scale pin positioning (0 to 500 range -> 0% to 100%)
  const pin = document.getElementById("scaleIndicatorPin");
  const pct = Math.min(100, Math.max(0, (data.aqi / 500) * 100));
  pin.style.left = `${pct}%`;
}

function animateNumber(element, start, end, duration) {
  if (isNaN(start)) start = 0;
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const current = Math.floor(progress * (end - start) + start);
    element.textContent = current;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      element.textContent = end;
    }
  };
  window.requestAnimationFrame(step);
}

/* ==========================================================================
   Forecast Cards & Chart.js Rendering
   ========================================================================== */
function renderForecastCards(days) {
  const container = document.getElementById("forecastCardsRow");
  container.innerHTML = "";

  days.forEach(d => {
    const card = document.createElement("div");
    card.className = `f-card ${d.is_today ? 'today' : ''}`;
    card.innerHTML = `
      <div class="f-day">${d.is_today ? 'Today' : d.day}</div>
      <div class="f-date">${d.date}</div>
      <div class="f-aqi" style="color: ${d.color};">${d.predicted_aqi}</div>
      <div class="f-badge" style="background: ${d.bg_color}; color: ${d.color};">${d.bucket}</div>
      <div class="f-range">${d.min_aqi} - ${d.max_aqi}</div>
    `;
    container.appendChild(card);
  });
}

function renderForecastChart(days) {
  const ctx = document.getElementById("forecastChart")?.getContext("2d");
  if (!ctx) return;

  if (state.charts.forecast) {
    state.charts.forecast.destroy();
  }

  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const gridColor = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
  const textColor = isDark ? "#9ca3af" : "#475569";

  const labels = days.map(d => d.is_today ? `Today (${d.day})` : `${d.day} (${d.date})`);
  const values = days.map(d => d.predicted_aqi);
  const minVals = days.map(d => d.min_aqi);
  const maxVals = days.map(d => d.max_aqi);

  state.charts.forecast = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Predicted AQI",
          data: values,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.15)",
          fill: true,
          tension: 0.35,
          borderWidth: 3,
          pointBackgroundColor: days.map(d => d.color),
          pointBorderColor: "#ffffff",
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        },
        {
          label: "Uncertainty Upper",
          data: maxVals,
          borderColor: "rgba(99, 102, 241, 0.35)",
          borderDash: [5, 5],
          borderWidth: 1.5,
          fill: false,
          pointRadius: 0
        },
        {
          label: "Uncertainty Lower",
          data: minVals,
          borderColor: "rgba(99, 102, 241, 0.35)",
          borderDash: [5, 5],
          borderWidth: 1.5,
          fill: "-1",
          backgroundColor: "rgba(99, 102, 241, 0.08)",
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(17, 24, 39, 0.95)",
          titleColor: "#f3f4f6",
          bodyColor: "#f3f4f6",
          borderColor: "rgba(255, 255, 255, 0.15)",
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (context) => {
              const d = days[context.dataIndex];
              if (context.datasetIndex === 0) {
                return `AQI: ${context.parsed.y} (${d.bucket})`;
              }
              return `${context.dataset.label}: ${context.parsed.y}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: "Inter", size: 11 } }
        },
        y: {
          min: 0,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: "Inter", size: 11 } }
        }
      }
    }
  });
}

/* ==========================================================================
   Diurnal Hourly Curve Chart
   ========================================================================== */
function renderDiurnalChart(curve) {
  const ctx = document.getElementById("diurnalChart")?.getContext("2d");
  if (!ctx) return;

  if (state.charts.diurnal) {
    state.charts.diurnal.destroy();
  }

  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const gridColor = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
  const textColor = isDark ? "#9ca3af" : "#475569";

  const labels = curve.map(c => c.label);
  const values = curve.map(c => c.aqi);
  const pointColors = curve.map(c => c.color);

  // Find lowest AQI daytime window for badge
  const daytimeHours = curve.filter(c => c.hour >= 11 && c.hour <= 17);
  if (daytimeHours.length > 0) {
    const bestHour = daytimeHours.reduce((min, cur) => cur.aqi < min.aqi ? cur : min, daytimeHours[0]);
    document.getElementById("bestWindowPill").innerHTML = `
      <i class="fa-solid fa-person-walking"></i> Optimal Outdoor Window: ${bestHour.label} (AQI ~${bestHour.aqi})
    `;
  }

  state.charts.diurnal = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Hourly AQI",
        data: values,
        backgroundColor: pointColors.map(c => c + "90"),
        borderColor: pointColors,
        borderWidth: 1.5,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(17, 24, 39, 0.95)",
          padding: 12,
          callbacks: {
            afterLabel: (ctx) => {
              const pt = curve[ctx.dataIndex];
              return `Category: ${pt.bucket}\nGuidance: ${pt.activity_rating}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textColor, font: { family: "Inter", size: 10 } }
        },
        y: {
          min: 0,
          grid: { color: gridColor },
          ticks: { color: textColor, font: { family: "Inter", size: 11 } }
        }
      }
    }
  });
}

/* ==========================================================================
   Pollutant Chemistry List & Ratio Radar Chart
   ========================================================================== */
function renderPollutantBars(pollutants) {
  const container = document.getElementById("pollutantsList");
  container.innerHTML = "";

  const pollutantNames = [
    { key: "PM2.5", full: "Fine Particulate Matter (< 2.5 µm)", unit: "µg/m³" },
    { key: "PM10", full: "Inhalable Coarse Particles (< 10 µm)", unit: "µg/m³" },
    { key: "NO2", full: "Nitrogen Dioxide (Vehicular/Thermal)", unit: "µg/m³" },
    { key: "SO2", full: "Sulfur Dioxide (Industrial Smelting)", unit: "µg/m³" },
    { key: "CO", full: "Carbon Monoxide (Combustion)", unit: "mg/m³" },
    { key: "O3", full: "Surface Ozone (Photochemical Smog)", unit: "µg/m³" },
    { key: "NH3", full: "Ammonia (Agricultural/Livestock)", unit: "µg/m³" }
  ];

  pollutantNames.forEach(p => {
    const val = pollutants[p.key] !== undefined ? pollutants[p.key] : 0;
    const limit = CPCB_LIMITS[p.key] || 100;
    const ratio = val / limit;
    const pct = Math.min(100, Math.round((val / (limit * 2)) * 100));

    let barColor = "#10b981";
    if (ratio > 2.0) barColor = "#881337";
    else if (ratio > 1.5) barColor = "#ef4444";
    else if (ratio > 1.0) barColor = "#f97316";
    else if (ratio > 0.75) barColor = "#f59e0b";

    const row = document.createElement("div");
    row.className = "pollutant-row";
    row.innerHTML = `
      <div class="p-meta">
        <div class="p-name">${p.key}</div>
        <div class="p-full">${p.full}</div>
      </div>
      <div class="p-bar-container">
        <div class="p-bar-track">
          <div class="p-bar-fill" style="width: ${pct}%; background-color: ${barColor};"></div>
        </div>
        <div class="p-limit-label">CPCB 24h Limit: ${limit} ${p.unit} ${ratio > 1 ? `<strong style="color: #ef4444">(${ratio.toFixed(1)}x limit)</strong>` : ''}</div>
      </div>
      <div class="p-val-box">
        <div class="p-val" style="color: ${barColor};">${val}</div>
        <div class="p-unit">${p.unit}</div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderPollutantsChart(pollutants) {
  const ctx = document.getElementById("pollutantsChart")?.getContext("2d");
  if (!ctx) return;

  if (state.charts.pollutants) {
    state.charts.pollutants.destroy();
  }

  const isDark = document.documentElement.getAttribute("data-theme") !== "light";
  const textColor = isDark ? "#9ca3af" : "#475569";
  const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)";

  const keys = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "NH3"];
  const ratios = keys.map(k => {
    const val = pollutants[k] || 0;
    const limit = CPCB_LIMITS[k] || 100;
    return parseFloat((val / limit).toFixed(2));
  });

  state.charts.pollutants = new Chart(ctx, {
    type: "radar",
    data: {
      labels: keys,
      datasets: [
        {
          label: "Current Ratio to CPCB Limit",
          data: ratios,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.25)",
          borderWidth: 2.5,
          pointBackgroundColor: "#06b6d4",
          pointBorderColor: "#ffffff",
          pointRadius: 4
        },
        {
          label: "Safe Threshold (1.0x)",
          data: [1, 1, 1, 1, 1, 1, 1],
          borderColor: "#ef4444",
          borderDash: [4, 4],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "bottom",
          labels: { color: textColor, font: { family: "Inter", size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.r}x safe limit`
          }
        }
      },
      scales: {
        r: {
          angleLines: { color: gridColor },
          grid: { color: gridColor },
          pointLabels: { color: textColor, font: { family: "Outfit", size: 11, weight: 600 } },
          ticks: { backdropColor: "transparent", color: textColor, stepSize: 0.5 }
        }
      }
    }
  });
}

/* ==========================================================================
   Historical Dataset Explorer
   ========================================================================== */
async function loadHistoricalTrends(cityName) {
  try {
    const res = await fetch(`/api/city/${encodeURIComponent(cityName)}/history?limit=90`);
    const data = await res.json();
    const records = data.records || [];

    if (records.length === 0) return;

    const ctx = document.getElementById("historyChart")?.getContext("2d");
    if (!ctx) return;

    if (state.charts.history) {
      state.charts.history.destroy();
    }

    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.06)" : "rgba(0, 0, 0, 0.06)";
    const textColor = isDark ? "#9ca3af" : "#475569";

    const labels = records.map(r => r.date);
    const aqiVals = records.map(r => r.aqi);
    const pm25Vals = records.map(r => r.pm25);

    state.charts.history = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Historical AQI",
            data: aqiVals,
            borderColor: "#f59e0b",
            backgroundColor: "rgba(245, 158, 11, 0.1)",
            fill: true,
            tension: 0.2,
            borderWidth: 2,
            pointRadius: 2
          },
          {
            label: "PM2.5 Concentration (µg/m³)",
            data: pm25Vals,
            borderColor: "#6366f1",
            borderWidth: 1.5,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: "top",
            labels: { color: textColor }
          }
        },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: textColor, maxTicksLimit: 12 } },
          y: { grid: { color: gridColor }, ticks: { color: textColor } }
        }
      }
    });

    document.getElementById("historySummary").innerHTML = `
      <span class="legend-chip"><i class="fa-solid fa-database"></i> ${records.length} Recorded Days</span>
    `;

  } catch (err) {
    console.error("Error loading historical trends:", err);
  }
}

/* ==========================================================================
   Leaflet Interactive Map & CrowdDB Hazard Visuals
   ========================================================================== */
function initLeafletMap() {
  const mapElement = document.getElementById("interactiveMap");
  if (!mapElement) return;

  // Initialize Map centered on India
  state.map = L.map("interactiveMap", {
    center: [20.5937, 78.9629],
    zoom: 5,
    zoomControl: true
  });

  // Dark CartoDB Map Tiles
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://carto.com/">CartoDB</a>',
    maxZoom: 18
  }).addTo(state.map);

  document.getElementById("btnRecenterMap")?.addEventListener("click", () => {
    if (state.currentData?.coordinates) {
      state.map.setView([state.currentData.coordinates.lat, state.currentData.coordinates.lon], 9);
    } else {
      state.map.setView([20.5937, 78.9629], 5);
    }
  });
}

function updateMapCityStations() {
  if (!state.map) return;

  // Clear existing station markers
  state.mapCityMarkers.forEach(m => state.map.removeLayer(m));
  state.mapCityMarkers = [];

  state.cities.forEach(city => {
    const marker = L.circleMarker([city.lat, city.lon], {
      radius: 9,
      fillColor: city.badge_color || "#06b6d4",
      color: "#ffffff",
      weight: 2,
      opacity: 0.9,
      fillOpacity: 0.85
    }).addTo(state.map);

    marker.bindPopup(`
      <div style="font-family: 'Inter', sans-serif; padding: 4px;">
        <h4 style="margin: 0 0 4px 0; font-family: 'Outfit'; font-size: 1.1rem;">${city.city}</h4>
        <p style="margin: 0 0 6px 0; font-size: 0.8rem; color: #9ca3af;">Typical AQI: <strong>${city.mean_aqi}</strong> (${city.typical_bucket})</p>
        <button onclick="selectCityFromMap('${city.city}')" style="background: #06b6d4; color: #fff; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: 600;">
          Focus City Data
        </button>
      </div>
    `);

    state.mapCityMarkers.push(marker);
  });
}

// Global hook for map popup click
window.selectCityFromMap = (cityName) => {
  const select = document.getElementById("citySelect");
  if (select) {
    select.value = cityName;
    state.currentCity = cityName;
    refreshCityData(cityName);
    filterCrowdReports();
    // Switch to overview tab
    document.querySelector('.tab-btn[data-tab="tabForecast"]')?.click();
  }
};

/* ==========================================================================
   CrowdDB Reports Management
   ========================================================================== */
async function loadCrowdReports() {
  try {
    const res = await fetch("/api/crowd/reports");
    const data = await res.json();
    state.crowdReports = data.reports || [];

    // Update active city crowd counter in hero
    const activeCityReports = state.crowdReports.filter(r => r.city.toLowerCase() === state.currentCity.toLowerCase());
    document.getElementById("displayCrowdCount").textContent = `${activeCityReports.length} reported`;
    document.getElementById("tabCrowdBadge").textContent = state.crowdReports.length;

    renderCrowdFeed();
    updateMapHazardPins();
    updateMapCityStations();
  } catch (err) {
    console.error("Error loading crowd reports:", err);
  }
}

function filterCrowdReports() {
  renderCrowdFeed();
}

function renderCrowdFeed() {
  const container = document.getElementById("crowdReportsList");
  if (!container) return;
  container.innerHTML = "";

  let filtered = state.crowdReports;
  if (state.crowdFilter === "current") {
    filtered = filtered.filter(r => r.city.toLowerCase() === state.currentCity.toLowerCase());
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-dim);">
        <i class="fa-solid fa-shield-cat" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
        <p>No incidents reported for this view yet.<br>Be the first citizen to log a local hazard!</p>
      </div>
    `;
    return;
  }

  filtered.forEach(report => {
    let sevClass = "hazard-moderate";
    if (report.severity === "Severe") sevClass = "hazard-severe";
    if (report.severity === "Hazardous") sevClass = "hazard-hazardous";

    let hazardIcon = "fa-triangle-exclamation";
    if (report.hazard_type.includes("Fire") || report.hazard_type.includes("Burning")) hazardIcon = "fa-fire";
    else if (report.hazard_type.includes("Traffic")) hazardIcon = "fa-car";
    else if (report.hazard_type.includes("Industrial")) hazardIcon = "fa-industry";
    else if (report.hazard_type.includes("Dust")) hazardIcon = "fa-trowel-bricks";
    else if (report.hazard_type.includes("Odor")) hazardIcon = "fa-mask-ventilator";

    const item = document.createElement("div");
    item.className = "report-item";
    item.innerHTML = `
      <div class="report-item-header">
        <span class="hazard-tag ${sevClass}">
          <i class="fa-solid ${hazardIcon}"></i> ${report.hazard_type}
        </span>
        <span style="font-size: 0.72rem; color: var(--text-dim);">${report.created_at.split(' ')[0]}</span>
      </div>
      <div class="report-location">
        <i class="fa-solid fa-location-dot"></i> ${report.city} &bull; ${report.location_name}
      </div>
      <div class="report-desc">${report.description}</div>
      ${report.symptoms ? `<div style="font-size: 0.75rem; color: var(--text-dim); margin-bottom: 0.4rem;"><strong>Symptoms:</strong> ${report.symptoms}</div>` : ''}
      ${report.grok_ai_assessment ? `
        <div class="report-ai-box">
          <i class="fa-solid fa-sparkles"></i>
          <div>${report.grok_ai_assessment} <span style="font-weight: 700; color: #f59e0b;">(Local AQI Impact: ${report.estimated_aqi_impact})</span></div>
        </div>
      ` : ''}
      <div class="report-footer">
        <span>Status: <strong style="color: #38bdf8;">${report.status}</strong></span>
        <button class="btn-vote" onclick="voteReport(${report.id})">
          <i class="fa-solid fa-thumbs-up"></i> Confirm Hazard (<span id="voteCount-${report.id}">${report.upvotes}</span>)
        </button>
      </div>
    `;
    container.appendChild(item);
  });
}

function updateMapHazardPins() {
  if (!state.map) return;

  state.mapHazardMarkers.forEach(m => state.map.removeLayer(m));
  state.mapHazardMarkers = [];

  state.crowdReports.forEach(r => {
    if (!r.latitude || !r.longitude) return;

    let markerColor = "#f59e0b";
    if (r.severity === "Severe") markerColor = "#ef4444";
    if (r.severity === "Hazardous") markerColor = "#881337";

    const hazardMarker = L.circleMarker([r.latitude, r.longitude], {
      radius: 12,
      fillColor: markerColor,
      color: "#ffffff",
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(state.map);

    hazardMarker.bindPopup(`
      <div style="font-family: 'Inter', sans-serif; padding: 4px; max-width: 240px;">
        <div style="font-size: 0.75rem; color: ${markerColor}; font-weight: 700; text-transform: uppercase;">Hazard: ${r.hazard_type}</div>
        <h4 style="margin: 2px 0 6px 0; font-size: 0.95rem;">${r.location_name}</h4>
        <p style="margin: 0 0 6px 0; font-size: 0.8rem; color: #d1d5db;">${r.description}</p>
        <div style="font-size: 0.75rem; color: #38bdf8; margin-bottom: 6px;">Impact: ${r.estimated_aqi_impact}</div>
        <button onclick="voteReport(${r.id})" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 0.72rem;">
          Confirm (${r.upvotes} confirmed)
        </button>
      </div>
    `);

    state.mapHazardMarkers.push(hazardMarker);
  });
}

window.voteReport = async (reportId) => {
  try {
    const res = await fetch("/api/crowd/vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report_id: reportId })
    });
    const data = await res.json();
    if (data.success) {
      const el = document.getElementById(`voteCount-${reportId}`);
      if (el) el.textContent = data.upvotes;
      showToast("Report confirmed! Thank you for validating crowd data.", "success");
    }
  } catch (err) {
    console.error("Error voting on report:", err);
  }
};

/* ==========================================================================
   Grok AI Health Advisory & Atmospheric Diagnostics
   ========================================================================== */
async function fetchGrokAdvisory(cityName) {
  try {
    const res = await fetch(`/api/city/${encodeURIComponent(cityName)}/advisory`);
    const data = await res.json();

    const advisory = data.advisory || {};
    const diagnosis = data.diagnosis || {};

    // 1. Health Advisory Elements
    document.getElementById("activityRating").textContent = `Outdoor Exertion: ${advisory.outdoor_activity_rating || 'Caution'}`;
    document.getElementById("activitySummary").textContent = advisory.summary || 'Elevated particulate levels require prudent precautions.';

    if (advisory.vulnerable_groups) {
      document.getElementById("vAsthma").textContent = advisory.vulnerable_groups.asthma || "Keep inhaler ready.";
      document.getElementById("vChildren").textContent = advisory.vulnerable_groups.children || "Restrict strenuous sports.";
    }
    document.getElementById("vMask").textContent = advisory.mask_recommendation || "Certified N95 during rush hours.";
    document.getElementById("vIndoor").textContent = advisory.indoor_precautions || "Operate HEPA filtration.";

    // 2. Atmospheric Root-Cause Diagnostics
    document.getElementById("diagPrimary").textContent = diagnosis.primary_driver || "Particulate Combustion & Inversion Stagnation";
    document.getElementById("diagMeteo").textContent = diagnosis.meteorological_context || "Atmospheric boundary layer compression reducing pollutant dispersion.";
    document.getElementById("diagAction").textContent = diagnosis.actionable_mitigation || "Deploy localized misting and enforce dust suppression.";

    // Source bars breakdown
    const sourceBarsContainer = document.getElementById("diagSourceBars");
    sourceBarsContainer.innerHTML = "";
    if (diagnosis.source_breakdown) {
      Object.entries(diagnosis.source_breakdown).forEach(([sourceName, pctStr]) => {
        const row = document.createElement("div");
        row.className = "source-bar-item";
        row.innerHTML = `
          <div class="s-label">${sourceName}</div>
          <div class="s-track">
            <div class="s-fill" style="width: ${pctStr};"></div>
          </div>
          <div class="s-pct">${pctStr}</div>
        `;
        sourceBarsContainer.appendChild(row);
      });
    }

  } catch (err) {
    console.error("Error fetching Grok advisory:", err);
  }
}

/* ==========================================================================
   Grok Environmental Copilot Chat
   ========================================================================== */
function initChat() {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const messagesContainer = document.getElementById("chatMessages");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    appendChatMessage("user", text);
    input.value = "";

    // Show AI thinking indicator
    const thinkingBubble = appendChatMessage("ai", "Analyzing atmospheric telemetry with Grok AI...");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: text }],
          context: {
            city: state.currentCity,
            aqi: state.currentData?.aqi || 150,
            bucket: state.currentData?.bucket || "Moderate",
            pollutants: state.currentData?.pollutants || {}
          }
        })
      });
      const data = await res.json();
      thinkingBubble.querySelector(".bubble-text").innerHTML = formatMarkdown(data.reply);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (err) {
      thinkingBubble.querySelector(".bubble-text").textContent = "Grok AI connection momentarily interrupted. Please check API settings.";
    }
  });

  // Prompt chips
  document.querySelectorAll(".chip-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      input.value = btn.getAttribute("data-prompt");
      form.dispatchEvent(new Event("submit"));
    });
  });
}

function appendChatMessage(sender, text) {
  const container = document.getElementById("chatMessages");
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble chat-bubble-${sender}`;
  bubble.innerHTML = `
    <div class="bubble-avatar"><i class="fa-solid ${sender === 'ai' ? 'fa-brain' : 'fa-user'}"></i></div>
    <div class="bubble-text">${formatMarkdown(text)}</div>
  `;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
}

function formatMarkdown(str) {
  if (!str) return "";
  return str
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

/* ==========================================================================
   Modals & Citizen Incident Submission
   ========================================================================== */
function initModals() {
  const reportModal = document.getElementById("reportModal");
  const settingsModal = document.getElementById("settingsModal");

  // Open Report Modal
  document.getElementById("btnOpenReportModal")?.addEventListener("click", () => openModal(reportModal));
  document.getElementById("btnReportIncidentInline")?.addEventListener("click", () => openModal(reportModal));
  document.getElementById("btnCloseReportModal")?.addEventListener("click", () => closeModal(reportModal));
  document.getElementById("btnCancelReport")?.addEventListener("click", () => closeModal(reportModal));

  // Open Settings Modal
  document.getElementById("btnOpenSettings")?.addEventListener("click", () => openModal(settingsModal));
  document.getElementById("btnCloseSettingsModal")?.addEventListener("click", () => closeModal(settingsModal));
  document.getElementById("btnCancelSettings")?.addEventListener("click", () => closeModal(settingsModal));

  // Feed Filter Chips
  document.querySelectorAll(".feed-filter-bar .filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".feed-filter-bar .filter-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      state.crowdFilter = chip.getAttribute("data-filter");
      renderCrowdFeed();
    });
  });

  // Handle Citizen Report Submission
  const reportForm = document.getElementById("reportForm");
  reportForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById("btnSubmitReport");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting & Grok Verifying...`;

    const payload = {
      city: document.getElementById("reportCity").value,
      hazard_type: document.getElementById("reportHazardType").value,
      location_name: document.getElementById("reportLocation").value,
      severity: document.getElementById("reportSeverity").value,
      symptoms: document.getElementById("reportSymptoms").value,
      description: document.getElementById("reportDescription").value
    };

    try {
      const res = await fetch("/api/crowd/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast("Hazard logged! Grok AI evaluated environmental threat.", "success");
        closeModal(reportModal);
        reportForm.reset();
        await loadCrowdReports();
        // Switch to CrowdDB tab
        document.querySelector('.tab-btn[data-tab="tabCrowd"]')?.click();
      } else {
        showToast(data.error || "Failed to submit report", "error");
      }
    } catch (err) {
      console.error("Report submit error:", err);
      showToast("Error communicating with server", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>Submit to CrowdDB</span>`;
    }
  });

  // Handle Settings Form Submission
  const settingsForm = document.getElementById("settingsForm");
  settingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const owKey = document.getElementById("inputOwKey").value.trim();
    const grokKey = document.getElementById("inputGrokKey").value.trim();

    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ openweather_key: owKey, grok_key: grokKey })
      });
      const data = await res.json();
      if (data.success) {
        showToast("API Credentials saved successfully!", "success");
        closeModal(settingsModal);
        await checkApiSettings();
        refreshCityData(state.currentCity);
      }
    } catch (err) {
      showToast("Error updating settings", "error");
    }
  });
}

function openModal(modal) {
  modal.classList.add("active");
  modal.setAttribute("aria-hidden", "false");
}

function closeModal(modal) {
  modal.classList.remove("active");
  modal.setAttribute("aria-hidden", "true");
}

/* ==========================================================================
   API Settings Status Check
   ========================================================================== */
async function checkApiSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();

    const owBadge = document.getElementById("owStatusBadge");
    const grokBadge = document.getElementById("grokStatusBadge");
    const statusText = document.getElementById("apiStatusText");

    if (data.openweather_configured) {
      owBadge.textContent = "Connected";
      owBadge.style.color = "#10b981";
      document.getElementById("inputOwKey").placeholder = `Active: ${data.openweather_masked}`;
    } else {
      owBadge.textContent = "Calibrated Simulation";
      owBadge.style.color = "#f59e0b";
    }

    if (data.grok_configured) {
      grokBadge.textContent = "Active";
      grokBadge.style.color = "#10b981";
      document.getElementById("inputGrokKey").placeholder = `Active: ${data.grok_masked}`;
    } else {
      grokBadge.textContent = "AI Fallback Engine";
      grokBadge.style.color = "#f59e0b";
    }

    if (data.openweather_configured && data.grok_configured) {
      statusText.textContent = "Live APIs Active";
    } else {
      statusText.textContent = "Engine Ready";
    }

  } catch (err) {
    console.error("Settings check error:", err);
  }
}

/* ==========================================================================
   Utilities & Notifications
   ========================================================================== */
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function showLoadingState(isLoading) {
  const pin = document.getElementById("scaleIndicatorPin");
  if (isLoading && pin) {
    pin.style.transition = "none";
  } else if (pin) {
    pin.style.transition = "left 0.6s cubic-bezier(0.16, 1, 0.3, 1)";
  }
}

function findClosestCity() {
  if (!navigator.geolocation) {
    showToast("Geolocation not supported by browser", "error");
    return;
  }
  showToast("Detecting user geolocation...", "success");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const uLat = pos.coords.latitude;
      const uLon = pos.coords.longitude;
      let closest = state.cities[0];
      let minDistance = Infinity;

      state.cities.forEach(c => {
        const dist = Math.hypot(c.lat - uLat, c.lon - uLon);
        if (dist < minDistance) {
          minDistance = dist;
          closest = c;
        }
      });

      if (closest) {
        state.currentCity = closest.city;
        document.getElementById("citySelect").value = closest.city;
        refreshCityData(closest.city);
        showToast(`Located nearest monitored city: ${closest.city}!`, "success");
      }
    },
    (err) => {
      showToast("Geolocation access denied", "error");
    }
  );
}
