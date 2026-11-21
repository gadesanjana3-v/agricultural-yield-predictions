// Automatically detect API host: works locally (file:// or port 5500) and in cloud deployment (Render)
const API_BASE = (window.location.protocol === "file:" || window.location.port === "5500")
    ? "http://127.0.0.1:8000"
    : window.location.origin;

const form = document.getElementById("predictionForm");
const resultBox = document.getElementById("result");
const cropSelect = document.getElementById("crop");
const submitBtn = document.getElementById("submitBtn");

// Load crops from backend or use fallback
async function loadCrops() {
    try {
        const response = await fetch(`${API_BASE}/crops`);
        if (!response.ok) throw new Error("Failed to fetch crops");
        const data = await response.json();
        const crops = data.crops || [];

        cropSelect.innerHTML = '<option value="">Choose a crop</option>';

        // Default priority crops to pin at the top
        const priorityCrops = ["Rice", "Wheat", "Maize (corn)"];
        const remainingCrops = crops.filter(c => !priorityCrops.includes(c)).sort();

        priorityCrops.forEach(crop => {
            if (crops.includes(crop)) {
                const opt = document.createElement("option");
                opt.value = crop;
                opt.textContent = `★ ${crop}`;
                cropSelect.appendChild(opt);
            }
        });

        if (remainingCrops.length > 0) {
            const separator = document.createElement("option");
            separator.disabled = true;
            separator.textContent = "────────── All Crops ──────────";
            cropSelect.appendChild(separator);

            remainingCrops.forEach(crop => {
                const opt = document.createElement("option");
                opt.value = crop;
                opt.textContent = crop;
                cropSelect.appendChild(opt);
            });
        }

        // Set default selection
        cropSelect.value = "Rice";

    } catch (err) {
        console.warn("Could not load crops dynamically from backend, using default list:", err);
        cropSelect.innerHTML = `
            <option value="">Choose a crop</option>
            <option value="Rice" selected>Rice</option>
            <option value="Wheat">Wheat</option>
            <option value="Maize (corn)">Maize (corn)</option>
        `;
    }
}

// Handle prediction submission
form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const crop = cropSelect.value;
    const year = parseInt(document.getElementById("year").value, 10);
    const area = parseFloat(document.getElementById("area").value);

    if (!crop || !year || !area || area <= 0) {
        showResult("Please enter valid details.", "error");
        return;
    }

    const payload = {
        year: year,
        crop: crop,
        crop_area_harvested: area
    };

    submitBtn.disabled = true;
    submitBtn.innerText = "Predicting...";
    showResult("Predicting yield... please wait.", "info");

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Prediction request failed");
        }

        const totalTonnes = data.estimated_total_production_tonnes
            ? `${Number(data.estimated_total_production_tonnes).toLocaleString()} tonnes`
            : `${((data.predicted_yield * data.crop_area_harvested) / 1000).toLocaleString(undefined, {maximumFractionDigits: 2})} tonnes`;

        showResult(`
            <div class="result-title">Prediction Result</div>
            <div class="result-details">
                <div><strong>Crop:</strong> ${data.crop}</div>
                <div><strong>Year:</strong> ${data.year}</div>
                <div><strong>Area:</strong> ${Number(data.crop_area_harvested).toLocaleString()} ha</div>
                <div class="predicted-value">🌾 Predicted Yield: <span>${data.predicted_yield.toFixed(2)} kg/ha</span></div>
                <div style="margin-top: 6px;">📦 <strong>Estimated Total Production:</strong> ${totalTonnes}</div>
            </div>
        `, "success");

    } catch (error) {
        console.error(error);
        showResult(
            `Unable to connect to the prediction backend (${error.message}). Please ensure the service is running.`,
            "error"
        );
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Predict Yield";
    }
});

function showResult(html, type) {
    resultBox.className = `result-box ${type}`;
    resultBox.innerHTML = html;
    resultBox.classList.remove("hidden");
}

// Initialize on page load
loadCrops();
