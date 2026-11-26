// Automatically detect API host: works locally (file:// or port 5500) and in cloud deployment (Render)
const API_BASE = (window.location.protocol === "file:" || window.location.port === "5500")
    ? "http://127.0.0.1:8000"
    : window.location.origin;

const form = document.getElementById("predictionForm");
const resultBox = document.getElementById("result");
const cropSelect = document.getElementById("crop");
const yearInput = document.getElementById("year");
const areaInput = document.getElementById("area");
const submitBtn = document.getElementById("submitBtn");
const cancelEditBtn = document.getElementById("cancelEditBtn");
const historyBody = document.getElementById("historyBody");
const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

// Tracks record ID when editing an existing row (null = Create mode)
let editingId = null;

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

function exitEditMode() {
    editingId = null;
    submitBtn.innerText = "Predict Yield";
    if (cancelEditBtn) cancelEditBtn.classList.add("hidden");
}

function startEdit(item) {
    editingId = item.id;
    cropSelect.value = item.crop;
    yearInput.value = item.year;
    areaInput.value = item.crop_area_harvested;
    submitBtn.innerText = `Update Prediction #${item.id}`;
    if (cancelEditBtn) cancelEditBtn.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// CREATE or UPDATE prediction
form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const crop = cropSelect.value;
    const year = parseInt(yearInput.value, 10);
    const area = parseFloat(areaInput.value);

    if (!crop || !year || !area || area <= 0) {
        showResult("Please enter valid details.", "error");
        return;
    }

    const payload = {
        year: year,
        crop: crop,
        crop_area_harvested: area
    };

    const isUpdating = editingId !== null;
    const url = isUpdating ? `${API_BASE}/history/${editingId}` : `${API_BASE}/predict`;
    const method = isUpdating ? "PUT" : "POST";

    submitBtn.disabled = true;
    submitBtn.innerText = isUpdating ? "Updating..." : "Predicting...";
    showResult(isUpdating ? "Updating prediction..." : "Predicting yield... please wait.", "info");

    try {
        const response = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Request failed");
        }

        const totalTonnes = data.estimated_total_production_tonnes
            ? `${Number(data.estimated_total_production_tonnes).toLocaleString()} tonnes`
            : `${((data.predicted_yield * data.crop_area_harvested) / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} tonnes`;

        const actionLabel = isUpdating ? "Updated in PostgreSQL Database" : "Saved to PostgreSQL Database";

        showResult(`
            <div class="result-title">${isUpdating ? "Updated Prediction Result" : "Prediction Result"}</div>
            <div class="result-details">
                <div><strong>Crop:</strong> ${data.crop}</div>
                <div><strong>Year:</strong> ${data.year}</div>
                <div><strong>Area:</strong> ${Number(data.crop_area_harvested).toLocaleString()} ha</div>
                <div class="predicted-value">🌾 Predicted Yield: <span>${Number(data.predicted_yield).toFixed(2)} kg/ha</span></div>
                <div style="margin-top: 6px;">📦 <strong>Estimated Total Production:</strong> ${totalTonnes}</div>
            </div>
            ${data.id ? `<div class="db-saved-notice">✓ ${actionLabel} (ID: ${data.id})</div>` : ""}
        `, "success");

        exitEditMode();
        loadHistory();
    } catch (error) {
        console.error(error);
        showResult(
            `Unable to connect to the prediction backend (${error.message}). Please ensure the service is running.`,
            "error"
        );
    } finally {
        submitBtn.disabled = false;
        if (editingId === null) {
            submitBtn.innerText = "Predict Yield";
        }
    }
});

// READ prediction history from PostgreSQL
async function loadHistory() {
    if (!historyBody) return;
    try {
        const response = await fetch(`${API_BASE}/history?limit=15`);
        if (!response.ok) throw new Error("Failed to load history");
        const data = await response.json();
        const items = data.history || [];

        if (items.length === 0) {
            historyBody.innerHTML = `<tr><td colspan="6" class="empty-state">No predictions recorded yet.</td></tr>`;
            return;
        }

        historyBody.innerHTML = "";
        items.forEach(item => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${item.timestamp || "-"}</td>
                <td><strong>${item.crop}</strong></td>
                <td>${item.year}</td>
                <td>${Number(item.crop_area_harvested).toLocaleString()}</td>
                <td class="yield-badge">${Number(item.predicted_yield).toFixed(2)}</td>
                <td class="row-actions">
                    <button type="button" class="action-btn edit-btn">✏️ Edit</button>
                    <button type="button" class="action-btn delete-btn">🗑️ Delete</button>
                </td>
            `;
            tr.querySelector(".edit-btn").addEventListener("click", () => startEdit(item));
            tr.querySelector(".delete-btn").addEventListener("click", () => deleteRecord(item.id));
            historyBody.appendChild(tr);
        });
    } catch (err) {
        console.warn("Could not load history:", err);
        historyBody.innerHTML = `<tr><td colspan="6" class="empty-state">Unable to load database history.</td></tr>`;
    }
}

// DELETE a single record
async function deleteRecord(id) {
    try {
        const response = await fetch(`${API_BASE}/history/${id}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Delete failed");
        if (editingId === id) exitEditMode();
        loadHistory();
    } catch (err) {
        console.error(err);
        showResult(`Failed to delete record #${id}.`, "error");
    }
}

// DELETE all records
async function clearAllHistory() {
    if (!confirm("Delete all stored predictions from the database?")) return;
    try {
        const response = await fetch(`${API_BASE}/history`, { method: "DELETE" });
        if (!response.ok) throw new Error("Clear failed");
        exitEditMode();
        loadHistory();
    } catch (err) {
        console.error(err);
        showResult("Failed to clear database history.", "error");
    }
}

function showResult(html, type) {
    resultBox.className = `result-box ${type}`;
    resultBox.innerHTML = html;
    resultBox.classList.remove("hidden");
}

if (cancelEditBtn) cancelEditBtn.addEventListener("click", exitEditMode);
if (refreshHistoryBtn) refreshHistoryBtn.addEventListener("click", loadHistory);
if (clearHistoryBtn) clearHistoryBtn.addEventListener("click", clearAllHistory);

// Initialize on page load
loadCrops();
loadHistory();
