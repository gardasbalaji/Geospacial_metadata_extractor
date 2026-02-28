/**
 * map_controller.js
 * Handles all Leaflet map interactions, polylines, and marker placements.
 */

class MapController {
    constructor(containerId) {
        // Init map centered on a global view
        this.map = L.map(containerId, {
            zoomControl: false // Custom placement later if needed
        }).setView([20, 0], 2);

        // Add dark-themed CartoDB Positron for a clean tech look
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(this.map);

        L.control.zoom({
            position: 'bottomright'
        }).addTo(this.map);

        this.markers = [];
        this.polyline = null;
    }

    clearMap() {
        this.markers.forEach(m => this.map.removeLayer(m));
        this.markers = [];

        if (this.polyline) {
            this.map.removeLayer(this.polyline);
            this.polyline = null;
        }
    }

    createCustomIcon(isFlagged) {
        const color = isFlagged ? '#ff9f0a' : '#ea4335';
        const pulseClass = isFlagged ? 'marker-pulse' : '';
        const svgHTML = `
            <svg class="${pulseClass}" viewBox="0 0 24 36" width="24" height="36" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 0C5.373 0 0 5.373 0 12c0 8.4 12 24 12 24s12-15.6 12-24c0-6.627-5.373-12-12-12zm0 17c-2.761 0-5-2.239-5-5s2.239-5 5-5 5 2.239 5 5-2.239 5-5 5z" fill="${color}" stroke="#fff" stroke-width="1.5"/>
            </svg>
        `;
        return L.divIcon({
            className: 'custom-marker-svg',
            html: svgHTML,
            iconSize: [24, 36],
            iconAnchor: [12, 36],
            popupAnchor: [0, -36]
        });
    }

    generateCurvePoints(p1, p2, numPoints = 50) {
        // Calculates a quadratic Bezier curve to simulate a parabola
        const latMid = (p1[0] + p2[0]) / 2;
        const lngMid = (p1[1] + p2[1]) / 2;

        const dLat = p2[0] - p1[0];
        const dLng = p2[1] - p1[1];

        // Offset for the control point perpendicular to the line
        const offset = 0.2;
        const ctrlLat = latMid - dLng * offset;
        const ctrlLng = lngMid + dLat * offset;

        const curve = [];
        for (let t = 0; t <= 1; t += 1 / numPoints) {
            const lat = (1 - t) * (1 - t) * p1[0] + 2 * (1 - t) * t * ctrlLat + t * t * p2[0];
            const lng = (1 - t) * (1 - t) * p1[1] + 2 * (1 - t) * t * ctrlLng + t * t * p2[1];
            curve.push([lat, lng]);
        }
        return curve;
    }

    /**
     * Renders a timeline array to the map
     * @param {Array} timeline Array of analysis objects
     */
    renderTimeline(timeline) {
        this.clearMap();

        const latLngs = [];

        timeline.forEach((item, index) => {
            const pt = item.point;
            const flagged = item.flagged;
            const markerCoord = [pt.latitude, pt.longitude];

            latLngs.push(markerCoord);

            // Create popup content
            const timestamp = new Date(pt.datetime).toLocaleString();
            let popupContent = `
                <div class="popup-content">
                    <img src="${pt.url}" alt="Location image">
                    <h4>${pt.landmark_name || "Extracted Coordinate"}</h4>
                    <p><i data-feather="clock" style="width:12px; height:12px"></i> ${timestamp}</p>
                    <p><i data-feather="database" style="width:12px; height:12px"></i> Source: ${pt.source}</p>
            `;

            if (flagged) {
                popupContent += `
                    <div class="warning-box">
                        <i data-feather="alert-triangle" style="width:14px; height:14px"></i>
                        <span>${item.reason}</span>
                    </div>
                `;
            }
            popupContent += `</div>`;

            // Place marker
            const marker = L.marker(markerCoord, {
                icon: this.createCustomIcon(flagged)
            }).bindPopup(popupContent);

            marker.addTo(this.map);
            this.markers.push(marker);
        });

        // Draw Polyline path
        if (latLngs.length > 1) {
            let curveLatLngs = [];
            for (let i = 0; i < latLngs.length - 1; i++) {
                const curvedSegment = this.generateCurvePoints(latLngs[i], latLngs[i + 1]);
                curveLatLngs.push(...curvedSegment);
            }
            this.polyline = L.polyline(curveLatLngs, {
                color: 'var(--accent)',
                weight: 3,
                opacity: 0.8,
                dashArray: '8, 8', // Dotted line to simulate chronological path
                lineJoin: 'round'
            }).addTo(this.map);
        }

        // Auto-fit bounds
        if (this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }

        // Re-init feather icons inside popups
        this.map.on('popupopen', () => feather.replace());
    }
}
