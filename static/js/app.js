/**
 * app.js
 * Bridges DOM interactions and API logic
 */

document.addEventListener("DOMContentLoaded", () => {

    const mapCtrl = new MapController('map');

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const timelineContainer = document.getElementById('timeline');
    const resultsContainer = document.getElementById('results-container');
    const loadingOverlay = document.getElementById('loading');

    // Stats
    const statPoints = document.getElementById('stat-points');
    const statFlagsBox = document.getElementById('stat-flag-box');
    const statFlags = document.getElementById('stat-flags');

    let globalUploadedItems = []; // Keeps items in upload order
    let isAnalyzing = false;

    // --- Drag & Drop Handlers ---
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            analyzeFiles(Array.from(files));
        }
        fileInput.value = ''; // Reset to allow re-selection of the same file
    }

    // --- API Interaction ---
    async function analyzeFiles(filesToAnalyze) {
        if (isAnalyzing || filesToAnalyze.length === 0) return;
        isAnalyzing = true;
        loadingOverlay.classList.remove('hidden');

        const formData = new FormData();
        filesToAnalyze.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/api/analyze_batch', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.status === 'success') {
                // Append the newly returned raw points to our global list (preserves upload order)
                globalUploadedItems.push(...data.raw_points);
                renderDashboard();
            } else {
                alert("Error processing images.");
            }
        } catch (error) {
            console.error("API Error", error);
            alert("Connection error occurred.");
        } finally {
            loadingOverlay.classList.add('hidden');
            isAnalyzing = false;
        }
    }

    // --- API Interaction ---
    analyzeBtn.addEventListener('click', () => {
        // Kept for backward compatibility if needed or removed functionality since we auto-analyze
        if (globalUploadedItems.length > 0) {
            renderDashboard();
        }
    });

    function calculateVelocity(p1, p2) {
        if (p1.latitude == null || p1.longitude == null || p2.latitude == null || p2.longitude == null) return null;

        const R = 6371; // km
        const dLat = (p2.latitude - p1.latitude) * Math.PI / 180;
        const dLon = (p2.longitude - p1.longitude) * Math.PI / 180;
        const lat1 = p1.latitude * Math.PI / 180;
        const lat2 = p2.latitude * Math.PI / 180;

        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance_km = R * c;

        const t1 = new Date(p1.datetime).getTime();
        const t2 = new Date(p2.datetime).getTime();

        if (isNaN(t1) || isNaN(t2)) return null;

        const time_diff_hours = Math.abs(t2 - t1) / 3600000;

        if (time_diff_hours === 0) return { distance_km: distance_km.toFixed(2), speed_kmh: distance_km > 0 ? Infinity : 0 };

        const speed_kmh = distance_km / time_diff_hours;

        return {
            distance_km: parseFloat(distance_km.toFixed(2)),
            speed_kmh: parseFloat(speed_kmh.toFixed(2))
        };
    }

    function calculateDistance(p1, p2) {
        if (p1.latitude == null || p1.longitude == null || p2.latitude == null || p2.longitude == null) return 0;

        const R = 6371; // km
        const dLat = (p2.latitude - p1.latitude) * Math.PI / 180;
        const dLon = (p2.longitude - p1.longitude) * Math.PI / 180;
        const lat1 = p1.latitude * Math.PI / 180;
        const lat2 = p2.latitude * Math.PI / 180;

        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        // Return with 2 decimal precision to match backend rounding
        return parseFloat((R * c).toFixed(2));
    }

    // --- Dashboard Rendering ---
    function renderDashboard() {
        resultsContainer.style.display = 'flex';
        timelineContainer.innerHTML = '';

        let flagCount = 0;

        // Reset previous flags and metrics before recalculating
        globalUploadedItems.forEach(item => {
            item.flagged = false;
            item.reason = null;
            item.movement_metrics = null;
        });

        // Filter out items without coordinates to avoid map crash
        let chronoItems = [...globalUploadedItems]
            .filter(item => item.latitude != null && item.longitude != null)
            .sort((a, b) => {
                let tA = new Date(a.datetime).getTime();
                let tB = new Date(b.datetime).getTime();
                if (isNaN(tA)) tA = 0;
                if (isNaN(tB)) tB = 0;
                return tA - tB;
            });

        // Recalculate movement metrics for the chronological timeline
        let totalSumDistance = 0;
        let timelineData = [];
        for (let i = 0; i < chronoItems.length; i++) {
            let item = { ...chronoItems[i] }; // Clone to avoid mutating original for analysis
            let flagged = false;
            let reason = null;
            let metrics = null;

            // Apply minor jitter ONLY to the display copy if overlapping
            if (i > 0) {
                for (let j = 0; j < i; j++) {
                    let prevItem = chronoItems[j];
                    if (Math.abs(item.latitude - prevItem.latitude) < 0.0001 &&
                        Math.abs(item.longitude - prevItem.longitude) < 0.0001) {
                        item.latitude += 0.0001 * (i + 1);
                        item.longitude += 0.0001 * (i + 1);
                    }
                }
            }

            if (i > 0) {
                metrics = calculateVelocity(chronoItems[i - 1], chronoItems[i]); // Use original coords for distance
                if (metrics && metrics.distance_km) {
                    totalSumDistance += parseFloat(metrics.distance_km);
                }
                if (metrics && metrics.speed_kmh > 1000) {
                    flagged = true;
                    reason = `Impossible velocity detected: ${metrics.speed_kmh} km/h`;
                }
            }

            // Assign back to the object reference so the sidebar picks it up
            chronoItems[i].flagged = flagged;
            chronoItems[i].reason = reason;
            chronoItems[i].movement_metrics = metrics;

            timelineData.push({ point: item, flagged, reason, movement_metrics: metrics });
        }

        // Render Map Points in chronological order
        mapCtrl.renderTimeline(timelineData);

        // Render Timeline Sidebar in UPLOAD ORDER
        globalUploadedItems.forEach((pt, idx) => {
            if (pt.flagged) flagCount++;

            let dateStr = "Unknown Time";
            if (pt.datetime) {
                dateStr = new Date(pt.datetime).toLocaleString();
            }

            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item';

            let contentHTML = `
                <div class="timeline-dot ${pt.flagged ? 'alert' : ''}"></div>
                <div class="timeline-content">
                    <span class="time-label">${dateStr}</span>
                    <div class="loc-name">${pt.landmark_name || 'Lat: ' + pt.latitude.toFixed(4) + ', Lng: ' + pt.longitude.toFixed(4)}</div>
                    <span class="loc-source">${pt.source}</span>
            `;

            if (pt.movement_metrics) {
                contentHTML += `
                    <div class="flight-metrics">
                        <span><i data-feather="navigation" style="width:12px; height:12px"></i> ${pt.movement_metrics.distance_km} km</span>
                        <span><i data-feather="wind" style="width:12px; height:12px"></i> ${pt.movement_metrics.speed_kmh} km/h</span>
                    </div>
                `;
            }

            if (pt.flagged) {
                contentHTML += `
                    <div class="warning-box">
                        <i data-feather="alert-triangle" style="width:14px; height:14px"></i>
                        <span>${pt.reason}</span>
                    </div>
                `;
            }

            contentHTML += `</div>`;
            timelineItem.innerHTML = contentHTML;
            timelineContainer.appendChild(timelineItem);
        });

        // Render Timeline Summary
        const summaryContainer = document.getElementById('timeline-summary');
        if (summaryContainer) {
            summaryContainer.style.display = 'block';
            summaryContainer.innerHTML = `
                <h4>Route Summary</h4>
                <div class="summary-stats" style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px; font-size: 0.9em; color: var(--text-secondary);">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="display: flex; align-items: center; gap: 4px;"><i data-feather="map-pin" style="width:14px; height:14px"></i> Total Points:</span>
                        <strong style="color: var(--text-primary);">${globalUploadedItems.length}</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="display: flex; align-items: center; gap: 4px;"><i data-feather="navigation" style="width:14px; height:14px"></i> Total Distance:</span>
                        <strong style="color: var(--text-primary);">${(Number(totalSumDistance) || 0).toFixed(2)} km</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; color: ${flagCount > 0 ? 'var(--warning)' : 'inherit'}">
                        <span style="display: flex; align-items: center; gap: 4px;"><i data-feather="alert-triangle" style="width:14px; height:14px"></i> Anomalies:</span>
                        <strong style="color: ${flagCount > 0 ? 'var(--warning)' : 'var(--text-primary)'};">${flagCount}</strong>
                    </div>
                </div>
            `;
        }

        // Update Stats
        statPoints.textContent = globalUploadedItems.length;
        if (flagCount > 0) {
            statFlagsBox.style.display = 'flex';
            statFlags.textContent = flagCount;
        } else {
            statFlagsBox.style.display = 'none';
        }

        feather.replace();
    }
});
