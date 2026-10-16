document.addEventListener("DOMContentLoaded", () => {
    // API Configuration
    const API_BASE = "/api";

    // Chart instances
    let factorChartInstance = null;
    let yieldTrendChartInstance = null;
    let rainfallTrendChartInstance = null;
    let topStatesChartInstance = null;
    let scenarioChartInstance = null;

    // DOM Elements
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    const cropSelect = document.getElementById("crop-select");
    const stateSelect = document.getElementById("state-select");
    const seasonSelect = document.getElementById("season-select");
    const yearSelect = document.getElementById("year-select");
    const landAreaInput = document.getElementById("land-area");
    const fertLevelSelect = document.getElementById("fert-level");
    const pestLevelSelect = document.getElementById("pest-level");
    const predictionForm = document.getElementById("prediction-form");

    const metricYield = document.getElementById("metric-yield");
    const metricTotal = document.getElementById("metric-total");
    const riskBadge = document.getElementById("risk-badge");
    const seasonalTemp = document.getElementById("seasonal-temp");
    const advisoryText = document.getElementById("advisory-text");
    const headerRegion = document.getElementById("header-region");

    const analyticsCrop = document.getElementById("analytics-crop");
    const analyticsState = document.getElementById("analytics-state");
    const btnLoadAnalytics = document.getElementById("btn-load-analytics");

    const scCropA = document.getElementById("sc-crop-a");
    const scCropB = document.getElementById("sc-crop-b");
    const btnRunScenario = document.getElementById("btn-run-scenario");

    // ------------------------------------
    // Tab Navigation
    // ------------------------------------
    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            navButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");

            // Update titles
            switch (targetTab) {
                case "predictor":
                    pageTitle.innerText = "Yield Prediction & Climate Risk";
                    pageSubtitle.innerText = "Real-time machine learning yield estimation based on weather and soil inputs.";
                    break;
                case "analytics":
                    pageTitle.innerText = "Historical Yield & Climate Analytics";
                    pageSubtitle.innerText = "Explore historical trends and regional production insights across India.";
                    loadAnalytics();
                    break;
                case "scenario":
                    pageTitle.innerText = "Scenario Simulator & What-If Comparator";
                    pageSubtitle.innerText = "Evaluate yield variance between baseline vs optimized farming strategies.";
                    break;
                case "agronomy":
                    pageTitle.innerText = "Agronomic Advisory & Resilience Guide";
                    pageSubtitle.innerText = "Best practices for soil health, pest management, and climate adaptation.";
                    break;
            }
        });
    });

    // ------------------------------------
    // Load Initial Metadata Options
    // ------------------------------------
    async function loadOptions() {
        try {
            const response = await fetch(`${API_BASE}/options`);
            if (!response.ok) throw new Error("API not reachable");
            const data = await response.json();
            populateDropdowns(data);
        } catch (error) {
            console.warn("Using offline dataset fallback for options:", error);
            // Local Fallback Options
            const fallbackData = {
                crops: ["Rice", "Wheat", "Maize", "Cotton(lint)", "Sugarcane", "Potato", "Jute", "Onion", "Arhar/Tur"],
                states: ["Assam", "Punjab", "Uttar Pradesh", "Haryana", "Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "West Bengal"],
                seasons: ["Kharif", "Rabi", "Summer", "Whole Year"],
                years: Array.from({ length: 25 }, (_, i) => 1997 + i)
            };
            populateDropdowns(fallbackData);
        }
    }

    function populateDropdowns(data) {
        populateSelect(cropSelect, data.crops, "Rice");
        populateSelect(stateSelect, data.states, "Punjab");
        populateSelect(seasonSelect, data.seasons, "Kharif");

        // Year Select
        yearSelect.innerHTML = "";
        const years = data.years && data.years.length > 0 ? data.years : Array.from({ length: 20 }, (_, i) => 2000 + i);
        years.forEach(yr => {
            const opt = document.createElement("option");
            opt.value = yr;
            opt.textContent = yr;
            if (yr === Math.max(...years)) opt.selected = true;
            yearSelect.appendChild(opt);
        });

        // Scenario & Analytics Dropdowns
        populateSelect(analyticsCrop, data.crops, "Rice");
        populateSelect(scCropA, data.crops, "Rice");
        populateSelect(scCropB, data.crops, "Wheat");

        if (data.states) {
            data.states.forEach(st => {
                const opt = document.createElement("option");
                opt.value = st;
                opt.textContent = st;
                analyticsState.appendChild(opt);
            });
        }

        // Trigger initial calculation
        runPrediction();
    }

    function populateSelect(selectEl, items, defaultValue) {
        selectEl.innerHTML = "";
        items.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item;
            opt.textContent = item;
            if (item === defaultValue) opt.selected = true;
            selectEl.appendChild(opt);
        });
    }

    stateSelect.addEventListener("change", () => {
        headerRegion.textContent = stateSelect.value || "National Data";
    });

    // ------------------------------------
    // Prediction Form Handler
    // ------------------------------------
    predictionForm.addEventListener("submit", (e) => {
        e.preventDefault();
        runPrediction();
    });

    async function runPrediction() {
        const crop = cropSelect.value;
        const state = stateSelect.value;
        const season = seasonSelect.value;
        const year = parseInt(yearSelect.value) || 2017;
        const area = parseFloat(landAreaInput.value) || 2.5;

        const rfRadio = document.querySelector('input[name="rainfall_level"]:checked');
        const rainfall_level = rfRadio ? rfRadio.value : "Normal";
        const fertilizer_level = fertLevelSelect.value;
        const pesticide_level = pestLevelSelect.value;

        const payload = {
            crop, state, season, year, area,
            rainfall_level, fertilizer_level, pesticide_level
        };

        const btnPredict = document.getElementById("btn-predict");
        const statusBadge = document.getElementById("model-source-badge");
        const modelSubtext = document.getElementById("model-subtext");
        const latencyTag = document.getElementById("inference-latency-tag");
        const pulseDot = document.getElementById("status-pulse-dot");

        if (btnPredict) {
            btnPredict.disabled = true;
            btnPredict.classList.add("computing");
            btnPredict.innerHTML = `<span>🔄 Computing ML Model in Background...</span>`;
        }

        if (latencyTag) {
            latencyTag.textContent = "⚡ Running Inference...";
        }

        const clientStart = performance.now();

        try {
            const response = await fetch(`${API_BASE}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("API Predict Error");
            const result = await response.json();
            const clientLatency = Math.round(performance.now() - clientStart);

            updatePredictionUI(result);

            if (statusBadge) statusBadge.textContent = result.engine || "ML Engine: RandomForest Pipeline";
            if (modelSubtext) modelSubtext.textContent = `Inference #${result.inference_id || 1} computed in background at ${new Date().toLocaleTimeString()}`;
            if (latencyTag) latencyTag.textContent = `⚡ ${result.latency_ms || clientLatency} ms`;
            if (pulseDot) pulseDot.style.backgroundColor = "#10b981";

            // Update sidebar stats
            checkModelStatus();
        } catch (error) {
            console.warn("Using offline prediction engine:", error);
            const offlineResult = generateOfflinePrediction(payload);
            updatePredictionUI(offlineResult);

            if (statusBadge) statusBadge.textContent = "Offline Fallback Engine";
            if (modelSubtext) modelSubtext.textContent = "Backend offline — computed locally via quantile mapping";
            if (latencyTag) latencyTag.textContent = "⚠️ Offline";
            if (pulseDot) pulseDot.style.backgroundColor = "#f59e0b";
        } finally {
            if (btnPredict) {
                btnPredict.disabled = false;
                btnPredict.classList.remove("computing");
                btnPredict.innerHTML = `<span>✨ Calculate Predicted Yield</span>`;
            }
        }
    }

    function generateOfflinePrediction(p) {
        // Quantile mapping simulation
        const rainMap = { Low: 650, Normal: 1450, High: 2300 };
        const fertMap = { Low: 600000, Medium: 2500000, High: 9000000 };
        const pestMap = { Low: 1200, Medium: 12000, High: 45000 };

        const rainVal = rainMap[p.rainfall_level] || 1450;
        const fertVal = fertMap[p.fertilizer_level] || 2500000;
        const pestVal = pestMap[p.pesticide_level] || 12000;

        let tempVal = 26.8;
        if (p.season.toLowerCase().includes("summer")) tempVal = 31.4;
        if (p.season.toLowerCase().includes("rabi") || p.season.toLowerCase().includes("winter")) tempVal = 22.1;

        let yieldVal = (fertVal / 1e7) * 1.8 + (rainVal / 1000) * 0.7 + 1.1;
        if (p.crop === "Sugarcane" || p.crop === "Coconut") yieldVal *= 15.0;

        const totalHarvest = yieldVal * p.area;

        let risk_tier = "Low";
        let risk_label = "Low Climate Risk";
        let recommendation = "Climate parameters align well with regional historical averages. Maintain balanced fertilization.";

        if (p.rainfall_level === "High" || tempVal > 30) {
            risk_tier = "Medium";
            risk_label = "Moderate Risk";
            recommendation = "Elevated humidity & temperature detected. Monitor field drainage to prevent root rot.";
        }
        if (p.rainfall_level === "Low" && tempVal > 31) {
            risk_tier = "High";
            risk_label = "High Anomaly Risk";
            recommendation = "Severe drought risk detected! Deploy drip irrigation and protective organic mulching immediately.";
        }

        return {
            predicted_yield: yieldVal.toFixed(3),
            total_harvest: totalHarvest.toFixed(2),
            seasonal_temperature: tempVal,
            risk_tier: risk_tier,
            risk_label: risk_label,
            recommendation: recommendation,
            inputs: {
                rainfall_mm: rainVal,
                fertilizer_kg: fertVal,
                pesticide_kg: pestVal
            }
        };
    }

    function updatePredictionUI(res) {
        metricYield.textContent = res.predicted_yield;
        metricTotal.textContent = Number(res.total_harvest).toLocaleString();

        seasonalTemp.textContent = `${res.seasonal_temperature} °C`;
        advisoryText.textContent = res.recommendation;

        riskBadge.textContent = res.risk_label;
        riskBadge.className = `risk-badge badge-${res.risk_tier.toLowerCase()}`;

        // Render Factor Chart
        renderFactorChart(res.inputs);
    }

    function renderFactorChart(inputs) {
        const ctx = document.getElementById("factorChart").getContext("2d");

        if (factorChartInstance) factorChartInstance.destroy();

        factorChartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Rainfall (mm)", "Fertilizer (x100 kg)", "Pesticide (kg)"],
                datasets: [{
                    label: "Input Factors",
                    data: [
                        inputs.rainfall_mm,
                        inputs.fertilizer_kg / 100,
                        inputs.pesticide_kg
                    ],
                    backgroundColor: [
                        "rgba(52, 211, 153, 0.7)",
                        "rgba(59, 130, 246, 0.7)",
                        "rgba(251, 191, 36, 0.7)"
                    ],
                    borderColor: ["#34d399", "#3b82f6", "#fbbf24"],
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        grid: { color: "rgba(255, 255, 255, 0.08)" },
                        ticks: { color: "#94a3b8" }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: "#cbd5e1" }
                    }
                }
            }
        });
    }

    // ------------------------------------
    // Analytics Dashboard
    // ------------------------------------
    btnLoadAnalytics.addEventListener("click", loadAnalytics);

    async function loadAnalytics() {
        const crop = analyticsCrop.value || "Rice";
        const state = analyticsState.value || "All";

        try {
            const res = await fetch(`${API_BASE}/analytics?crop=${encodeURIComponent(crop)}&state=${encodeURIComponent(state)}`);
            if (!res.ok) throw new Error();
            const data = await res.json();
            renderAnalyticsCharts(data);
        } catch (e) {
            // Offline analytics mockup
            const years = Array.from({ length: 15 }, (_, i) => 2002 + i);
            const yields = years.map((_, i) => (1.8 + i * 0.08 + Math.random() * 0.4).toFixed(2));
            const rainfall = years.map(() => Math.floor(1100 + Math.random() * 600));
            renderAnalyticsCharts({
                years: years,
                yields: yields,
                rainfall: rainfall,
                top_states: {
                    states: ["Punjab", "Haryana", "UP", "West Bengal", "Tamil Nadu", "Assam"],
                    yields: [3.4, 3.1, 2.8, 2.6, 2.4, 2.1]
                }
            });
        }
    }

    function renderAnalyticsCharts(data) {
        // Yield Trend Chart
        const ctxYield = document.getElementById("yieldTrendChart").getContext("2d");
        if (yieldTrendChartInstance) yieldTrendChartInstance.destroy();
        yieldTrendChartInstance = new Chart(ctxYield, {
            type: "line",
            data: {
                labels: data.years,
                datasets: [{
                    label: "Avg Yield (T/ha)",
                    data: data.yields,
                    borderColor: "#34d399",
                    backgroundColor: "rgba(52, 211, 153, 0.15)",
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: "rgba(255,255,255,0.08)" }, ticks: { color: "#94a3b8" } },
                    x: { grid: { display: false }, ticks: { color: "#94a3b8" } }
                }
            }
        });

        // Rainfall Trend Chart
        const ctxRain = document.getElementById("rainfallTrendChart").getContext("2d");
        if (rainfallTrendChartInstance) rainfallTrendChartInstance.destroy();
        rainfallTrendChartInstance = new Chart(ctxRain, {
            type: "line",
            data: {
                labels: data.years,
                datasets: [{
                    label: "Rainfall (mm)",
                    data: data.rainfall,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.15)",
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: "rgba(255,255,255,0.08)" }, ticks: { color: "#94a3b8" } },
                    x: { grid: { display: false }, ticks: { color: "#94a3b8" } }
                }
            }
        });

        // Top States Chart
        const ctxStates = document.getElementById("topStatesChart").getContext("2d");
        if (topStatesChartInstance) topStatesChartInstance.destroy();
        topStatesChartInstance = new Chart(ctxStates, {
            type: "bar",
            data: {
                labels: data.top_states.states,
                datasets: [{
                    label: "Yield (T/ha)",
                    data: data.top_states.yields,
                    backgroundColor: "rgba(16, 185, 129, 0.75)",
                    borderColor: "#10b981",
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { color: "rgba(255,255,255,0.08)" }, ticks: { color: "#94a3b8" } },
                    y: { grid: { display: false }, ticks: { color: "#94a3b8" } }
                }
            }
        });
    }

    // ------------------------------------
    // Scenario Simulator
    // ------------------------------------
    btnRunScenario.addEventListener("click", async () => {
        const cropA = scCropA.value;
        const rainA = document.getElementById("sc-rain-a").value;
        const fertA = document.getElementById("sc-fert-a").value;

        const cropB = scCropB.value;
        const rainB = document.getElementById("sc-rain-b").value;
        const fertB = document.getElementById("sc-fert-b").value;

        const state = stateSelect.value || "Assam";

        const pA = { crop: cropA, state, season: "Kharif", year: 2017, area: 1.0, rainfall_level: rainA, fertilizer_level: fertA, pesticide_level: "Medium" };
        const pB = { crop: cropB, state, season: "Kharif", year: 2017, area: 1.0, rainfall_level: rainB, fertilizer_level: fertB, pesticide_level: "Medium" };

        let resA, resB;

        try {
            const [rA, rB] = await Promise.all([
                fetch(`${API_BASE}/predict`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(pA) }).then(r => r.json()),
                fetch(`${API_BASE}/predict`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(pB) }).then(r => r.json())
            ]);
            resA = rA; resB = rB;
        } catch (e) {
            resA = generateOfflinePrediction(pA);
            resB = generateOfflinePrediction(pB);
        }

        const yA = parseFloat(resA.predicted_yield);
        const yB = parseFloat(resB.predicted_yield);
        const diffPct = (((yB - yA) / yA) * 100).toFixed(1);

        document.getElementById("comp-yield-a").textContent = `${yA} T/ha`;
        document.getElementById("comp-yield-b").textContent = `${yB} T/ha`;
        document.getElementById("comp-diff").textContent = `${diffPct > 0 ? '+' : ''}${diffPct}%`;

        // Render Scenario Chart
        const ctxSc = document.getElementById("scenarioChart").getContext("2d");
        if (scenarioChartInstance) scenarioChartInstance.destroy();
        scenarioChartInstance = new Chart(ctxSc, {
            type: "bar",
            data: {
                labels: [`Option A (${cropA})`, `Option B (${cropB})`],
                datasets: [{
                    label: "Yield (Tonnes / Ha)",
                    data: [yA, yB],
                    backgroundColor: ["rgba(96, 165, 250, 0.75)", "rgba(52, 211, 153, 0.75)"],
                    borderColor: ["#60a5fa", "#34d399"],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: "rgba(255,255,255,0.08)" }, ticks: { color: "#94a3b8" } },
                    x: { grid: { display: false }, ticks: { color: "#cbd5e1" } }
                }
            }
        });
    });

    // Check background model status
    async function checkModelStatus() {
        try {
            const res = await fetch(`${API_BASE}/model-status`);
            if (res.ok) {
                const data = await res.json();
                const statusLabel = document.querySelector(".sidebar-footer .status-indicator span:last-child");
                if (statusLabel) {
                    statusLabel.textContent = `ML Pipeline Active (${data.total_inferences_served} served)`;
                }
                const modelBadge = document.getElementById("model-source-badge");
                if (modelBadge && modelBadge.textContent.includes("RandomForest")) {
                    modelBadge.textContent = `ML Engine: ${data.algorithm}`;
                }
            }
        } catch (e) {
            console.warn("Model health endpoint check:", e);
        }
    }

    // Initialize
    loadOptions();
    checkModelStatus();
});
