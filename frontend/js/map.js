/**
 * PathPal Leaflet 地图交互模块
 * 支持分层管理：baseLayers（内部道路网络）+ routeLayers（规划路线）+ markerLayers（标记点）
 * 挂载到 window.PathPalMap
 */
(function () {
    "use strict";

    // 节点类型图标配置
    var NODE_STYLE = {
        gate: { radius: 7, color: "#27ae60", fillColor: "#27ae60", fillOpacity: 0.8, weight: 2 },
        scenic_spot: { radius: 6, color: "#8e44ad", fillColor: "#8e44ad", fillOpacity: 0.7, weight: 2 },
        building: { radius: 6, color: "#2c3e50", fillColor: "#2c3e50", fillOpacity: 0.7, weight: 2 },
        intersection: { radius: 2.5, color: "#95a5a6", fillColor: "#95a5a6", fillOpacity: 0.5, weight: 1 },
        junction: { radius: 2.5, color: "#95a5a6", fillColor: "#95a5a6", fillOpacity: 0.5, weight: 1 },
        crossroad: { radius: 3.5, color: "#bdc3c7", fillColor: "#bdc3c7", fillOpacity: 0.6, weight: 1.5 },
        default: { radius: 3, color: "#7f8c8d", fillColor: "#7f8c8d", fillOpacity: 0.5, weight: 1 },
    };

    var EDGE_STYLE = {
        main_road: { color: "#bdc3c7", weight: 2.5, opacity: 0.6, dashArray: null },
        secondary_road: { color: "#d5dbdb", weight: 1.8, opacity: 0.5, dashArray: null },
        path: { color: "#d5dbdb", weight: 1.5, opacity: 0.4, dashArray: "4,6" },
        bike_lane: { color: "#2ecc71", weight: 2.0, opacity: 0.5, dashArray: "6,4" },
        sightseeing_route: { color: "#e67e22", weight: 2.0, opacity: 0.5, dashArray: "6,4" },
        default: { color: "#ccd1d1", weight: 1.5, opacity: 0.4, dashArray: null },
    };

    var FACILITY_ICON_MAP = {
        toilet: "#3498db",
        cafe: "#8b4513",
        shop: "#e67e22",
        supermarket: "#f39c12",
        canteen: "#e74c3c",
        restaurant: "#e74c3c",
        service_desk: "#27ae60",
        ticket: "#2ecc71",
        medical: "#e74c3c",
        atm: "#2c3e50",
        default: "#7f8c8d",
    };

    /**
     * 创建 Leaflet 地图实例，返回分层管理的 mapState。
     */
    function createMap(containerId, center, zoom, options) {
        var c = center || [39.9042, 116.4074];
        var z = zoom || 15;
        var opts = options || {};
        var tileLayer = null;

        var oldContainer = document.getElementById(containerId);
        if (oldContainer && oldContainer._leaflet_id) {
            oldContainer._leaflet_id = null;
        }

        var map = L.map(containerId).setView(c, z);

        if (opts.showTile !== false) {
            tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                maxZoom: 19,
            }).addTo(map);
        }

        // 三个独立图层组
        var baseLayer = L.layerGroup().addTo(map);
        var routeLayer = L.layerGroup().addTo(map);
        var markerLayer = L.layerGroup().addTo(map);

        function setTileVisible(show) {
            if (show && !tileLayer) {
                tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                    maxZoom: 19,
                }).addTo(map);
            } else if (!show && tileLayer) {
                map.removeLayer(tileLayer);
                tileLayer = null;
            }
        }

        setTimeout(function () {
            map.invalidateSize();
        }, 100);

        return {
            map: map,
            baseLayer: baseLayer,
            routeLayer: routeLayer,
            markerLayer: markerLayer,
            setTileVisible: setTileVisible,
            // 兼容旧 API
            layerGroup: baseLayer,
        };
    }

    // ==================== 分层清空 ====================

    function clearBaseLayers(mapState) {
        if (mapState && mapState.baseLayer) {
            mapState.baseLayer.clearLayers();
        }
    }

    function clearRouteLayers(mapState) {
        if (mapState && mapState.routeLayer) {
            mapState.routeLayer.clearLayers();
        }
    }

    function clearMarkerLayers(mapState) {
        if (mapState && mapState.markerLayer) {
            mapState.markerLayer.clearLayers();
        }
    }

    function clearAllLayers(mapState) {
        clearBaseLayers(mapState);
        clearRouteLayers(mapState);
        clearMarkerLayers(mapState);
    }

    // ==================== 绘制基础网络 ====================

    function drawBaseNetwork(mapState, nodes, edges, facilities) {
        if (!mapState) return;
        clearBaseLayers(mapState);

        // 建立 nodeId -> node 映射
        var nodesById = {};
        if (nodes) {
            nodes.forEach(function (n) {
                nodesById[n.id] = n;
            });
        }

        if (edges && edges.length > 0) {
            drawEdges(mapState.baseLayer, nodesById, edges);
        }
        if (nodes && nodes.length > 0) {
            drawNodes(mapState.baseLayer, nodes);
        }
        if (facilities && facilities.length > 0) {
            drawFacilities(mapState.baseLayer, facilities);
        }
    }

    function drawEdges(layerGroup, nodesById, edges) {
        edges.forEach(function (e) {
            // 优先使用 edge.geometry
            var coords = null;
            if (e.geometry && Array.isArray(e.geometry) && e.geometry.length >= 2) {
                coords = e.geometry;
            } else {
                var fromNode = nodesById[e.from];
                var toNode = nodesById[e.to];
                if (!fromNode || !toNode) return;
                var lat1 = fromNode.latitude;
                var lng1 = fromNode.longitude;
                var lat2 = toNode.latitude;
                var lng2 = toNode.longitude;
                if (Math.abs(lat1) < 0.001 && Math.abs(lng1) < 0.001) return;
                if (Math.abs(lat2) < 0.001 && Math.abs(lng2) < 0.001) return;
                coords = [[lat1, lng1], [lat2, lng2]];
            }

            // 过滤无效坐标
            coords = coords.filter(function (c) {
                return Math.abs(c[0]) > 0.001 && Math.abs(c[1]) > 0.001;
            });
            if (coords.length < 2) return;

            // 根据道路类型 + allowed_transport 选择样式
            var style = null;
            var transport = e.allowed_transport || [];

            if (transport.indexOf("bike") >= 0 && transport.indexOf("sightseeing_car") < 0) {
                var st = EDGE_STYLE[e.road_type] || EDGE_STYLE.default;
                style = { color: "#2ecc71", weight: st.weight, opacity: 0.45, dashArray: "6,4" };
            } else if (transport.indexOf("sightseeing_car") >= 0) {
                style = { color: "#e67e22", weight: 2.0, opacity: 0.45, dashArray: "6,4" };
            } else {
                style = EDGE_STYLE[e.road_type] || EDGE_STYLE.default;
            }

            var line = L.polyline(coords, {
                color: style.color,
                weight: style.weight || 1.5,
                opacity: style.opacity || 0.4,
                dashArray: style.dashArray || null,
                interactive: false,
            });
            layerGroup.addLayer(line);
        });
    }

    function drawNodes(layerGroup, nodes) {
        nodes.forEach(function (n) {
            var lat = n.latitude;
            var lng = n.longitude;
            if (Math.abs(lat) < 0.001 && Math.abs(lng) < 0.001) return;

            var typeStyle = NODE_STYLE[n.type] || NODE_STYLE.default;
            var subtypeStyle = NODE_STYLE[n.subtype] || null;
            var s = subtypeStyle || typeStyle;

            var circle = L.circleMarker([lat, lng], {
                radius: s.radius,
                color: s.color,
                fillColor: s.fillColor,
                fillOpacity: s.fillOpacity,
                weight: s.weight,
            });
            circle.bindTooltip(n.name || n.id, { direction: "top", offset: [0, -s.radius] });
            layerGroup.addLayer(circle);
        });
    }

    function drawFacilities(layerGroup, facilities) {
        facilities.forEach(function (f) {
            var lat = f.latitude;
            var lng = f.longitude;
            if (lat === undefined || lng === undefined) return;
            if (Math.abs(lat) < 0.001 && Math.abs(lng) < 0.001) return;

            var color = FACILITY_ICON_MAP[f.category] || FACILITY_ICON_MAP.default;

            // 小圆点标记
            var circle = L.circleMarker([lat, lng], {
                radius: 4.5,
                color: color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 1.5,
            });

            var label = f.category ? (f.category + ": " + f.name) : f.name;
            circle.bindPopup("<b>" + (window.PathPalAPI ? PathPalAPI.escapeHtml(f.name) : f.name) +
                "</b><br>类别: " + (f.category || "未知"));

            layerGroup.addLayer(circle);
        });
    }

    // ==================== 绘制路线 ====================

    function drawRoute(mapState, coordinates, options) {
        if (!mapState || !coordinates || coordinates.length === 0) return;
        var opts = Object.assign({ color: "#e74c3c", weight: 5, opacity: 0.85 }, options || {});
        var line = L.polyline(coordinates, opts);
        mapState.routeLayer.addLayer(line);
        mapState.map.fitBounds(line.getBounds().pad(0.15));
    }

    function drawRouteWithSegments(mapState, segments, graphCoords) {
        if (!mapState || !segments) return;

        var transportColors = {
            walk: "#3498db",
            bike: "#27ae60",
            sightseeing_car: "#e67e22",
        };

        var allCoords = [];

        segments.forEach(function (seg) {
            var segCoords = null;

            // 优先使用 segment.geometry
            if (seg.geometry && Array.isArray(seg.geometry) && seg.geometry.length >= 2) {
                segCoords = seg.geometry;
            } else if (graphCoords) {
                // Fallback: 用 graphCoords 查找 from/to 坐标
                var fromCoord = graphCoords[seg.from];
                var toCoord = graphCoords[seg.to];
                if (fromCoord && toCoord) {
                    segCoords = [fromCoord, toCoord];
                }
            }

            if (!segCoords || segCoords.length < 2) return;

            var color = transportColors[seg.transport] || "#95a5a6";
            var line = L.polyline(segCoords, {
                color: color,
                weight: 4,
                opacity: 0.8,
            });
            mapState.routeLayer.addLayer(line);
            segCoords.forEach(function (c) { allCoords.push(c); });
        });

        if (allCoords.length > 0) {
            var bounds = L.latLngBounds(allCoords);
            mapState.map.fitBounds(bounds.pad(0.15));
        }
    }

    // ==================== 绘制标记 ====================

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
            mapState.markerLayer.addLayer(marker);
        });
    }

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
            mapState.markerLayer.addLayer(marker);
        });
    }

    // ---- 挂载到 window ----
    window.PathPalMap = {
        createMap: createMap,
        clearMapLayers: clearAllLayers,
        clearBaseLayers: clearBaseLayers,
        clearRouteLayers: clearRouteLayers,
        clearMarkerLayers: clearMarkerLayers,
        drawBaseNetwork: drawBaseNetwork,
        drawEdges: drawEdges,
        drawNodes: drawNodes,
        drawFacilities: drawFacilities,
        drawRoute: drawRoute,
        drawRouteWithSegments: drawRouteWithSegments,
        drawMarkers: drawMarkers,
        drawFacilityMarkers: drawFacilityMarkers,
    };
})();
