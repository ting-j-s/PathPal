/**
 * PathPal Leaflet 地图交互模块
 * 所有地图操作统一通过此模块，挂载到 window.PathPalMap
 */
(function () {
    "use strict";

    /**
     * 创建 Leaflet 地图实例。
     * @param {string} containerId - 容器 DOM ID
     * @param {Array}  center       - [lat, lng]
     * @param {number} zoom
     * @returns {object} { map, layerGroup }
     */
    function createMap(containerId, center, zoom) {
        var c = center || [39.9042, 116.4074];
        var z = zoom || 15;

        // 销毁同容器旧实例
        var oldContainer = document.getElementById(containerId);
        if (oldContainer && oldContainer._leaflet_id) {
            oldContainer._leaflet_id = null;
        }

        var map = L.map(containerId).setView(c, z);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19,
        }).addTo(map);

        var layerGroup = L.layerGroup().addTo(map);

        // 延迟 invalidateSize 解决容器初始化尺寸问题
        setTimeout(function () {
            map.invalidateSize();
        }, 100);

        return { map: map, layerGroup: layerGroup };
    }

    /**
     * 清空地图上所有自定义图层。
     */
    function clearMapLayers(mapState) {
        if (mapState && mapState.layerGroup) {
            mapState.layerGroup.clearLayers();
        }
    }

    /**
     * 绘制路线 polyline。
     * @param {object} mapState
     * @param {Array}  coordinates - [[lat,lng], [lat,lng], ...]
     * @param {object} options     - Leaflet polyline options
     */
    function drawRoute(mapState, coordinates, options) {
        if (!mapState || !coordinates || coordinates.length === 0) return;
        var opts = Object.assign({ color: "#e74c3c", weight: 5, opacity: 0.85 }, options || {});
        var line = L.polyline(coordinates, opts);
        mapState.layerGroup.addLayer(line);
        mapState.map.fitBounds(line.getBounds().pad(0.15));
    }

    /**
     * 在地图上绘制标记点。
     * @param {object} mapState
     * @param {Array}  points - [{lat, lng, label, type}]
     *   type: "start" → 绿色, "end" → 红色, "waypoint" → 蓝色, 其他 → 默认蓝色
     */
    function drawMarkers(mapState, points) {
        if (!mapState || !points) return;
        var colorMap = { start: "#27ae60", end: "#e74c3c", waypoint: "#2980b9" };

        points.forEach(function (p) {
            var color = colorMap[p.type] || "#2980b9";
            var icon = L.divIcon({
                className: "",
                html:
                    '<svg width="28" height="36" viewBox="0 0 28 36">' +
                    '<path d="M14 0C6.3 0 0 6.3 0 14c0 10.5 14 22 14 22s14-11.5 14-22C28 6.3 21.7 0 14 0z" fill="' +
                    color +
                    '"/>' +
                    '<circle cx="14" cy="14" r="5" fill="#fff"/>' +
                    "</svg>",
                iconSize: [28, 36],
                iconAnchor: [14, 36],
                popupAnchor: [0, -38],
            });
            var marker = L.marker([p.lat, p.lng], { icon: icon });
            if (p.label) {
                marker.bindPopup("<b>" + (window.PathPalAPI ? PathPalAPI.escapeHtml(p.label) : p.label) + "</b>");
            }
            mapState.layerGroup.addLayer(marker);
        });
    }

    /**
     * 在地图上绘制设施标记点（带 popup 显示名称、类别、道路距离）。
     * @param {object} mapState
     * @param {Array}  facilities - 来自 nearby API 响应的 facilities 数组
     */
    function drawFacilityMarkers(mapState, facilities) {
        if (!mapState || !facilities) return;
        facilities.forEach(function (f) {
            var lat = f.latitude;
            var lng = f.longitude;
            if (lat === undefined || lng === undefined) return;

            var icon = L.divIcon({
                className: "",
                html:
                    '<svg width="22" height="32" viewBox="0 0 22 32">' +
                    '<path d="M11 0C4.9 0 0 4.9 0 11c0 8.3 11 21 11 21s11-12.7 11-21C22 4.9 17.1 0 11 0z" fill="#27ae60"/>' +
                    '<circle cx="11" cy="11" r="4" fill="#fff"/>' +
                    "</svg>",
                iconSize: [22, 32],
                iconAnchor: [11, 32],
                popupAnchor: [0, -34],
            });

            var popupText =
                "<b>" +
                (PathPalAPI ? PathPalAPI.escapeHtml(f.name) : f.name) +
                "</b><br>类别: " +
                (PathPalAPI ? PathPalAPI.escapeHtml(f.category || "") : f.category || "") +
                "<br>道路距离: " +
                (PathPalAPI ? PathPalAPI.formatDistance(f.road_distance) : f.road_distance + " m");

            var marker = L.marker([lat, lng], { icon: icon }).bindPopup(popupText);
            mapState.layerGroup.addLayer(marker);
        });
    }

    /**
     * 按 segments 绘制分段路线（不同交通方式用不同颜色）。
     * @param {object} mapState
     * @param {Array}  segments
     * @param {object} graphCoords - { nodeId: [lat, lng], ... }
     */
    function drawRouteWithSegments(mapState, segments, graphCoords) {
        if (!mapState || !segments || !graphCoords) return;

        var transportColors = {
            walk: "#3498db",
            bike: "#27ae60",
            sightseeing_car: "#e67e22",
        };

        var allCoords = [];

        segments.forEach(function (seg) {
            var fromCoord = graphCoords[seg.from];
            var toCoord = graphCoords[seg.to];
            if (!fromCoord || !toCoord) return;

            var color = transportColors[seg.transport] || "#95a5a6";
            var line = L.polyline([fromCoord, toCoord], {
                color: color,
                weight: 4,
                opacity: 0.8,
            });
            mapState.layerGroup.addLayer(line);
            allCoords.push(fromCoord, toCoord);
        });

        if (allCoords.length > 0) {
            var bounds = L.latLngBounds(allCoords);
            mapState.map.fitBounds(bounds.pad(0.15));
        }
    }

    // ---- 挂载到 window ----
    window.PathPalMap = {
        createMap: createMap,
        clearMapLayers: clearMapLayers,
        drawRoute: drawRoute,
        drawMarkers: drawMarkers,
        drawFacilityMarkers: drawFacilityMarkers,
        drawRouteWithSegments: drawRouteWithSegments,
    };
})();
