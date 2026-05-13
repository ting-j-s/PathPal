/**
 * PathPal 路线规划页面 JS
 * 使用 map-layers API 绘制完整内部道路图 + 路线覆盖
 */
(function () {
    "use strict";

    var API = window.PathPalAPI;
    var MapMod = window.PathPalMap;
    if (!API || !MapMod) return;

    var mapState = null;
    var nodesMap = {}; // nodeId -> {id, name, latitude, longitude, ...}
    var currentMapMeta = null;
    var currentEdges = [];
    var currentFacilities = [];

    // ---- 工具函数 ----

    function getSelectVal(id) {
        var el = document.getElementById(id);
        return el ? el.value : "";
    }

    function setSelectOptions(id, options, valueKey, labelKey) {
        var el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '<option value="">— 请选择 —</option>';
        options.forEach(function (opt) {
            var val = typeof opt === "object" ? opt[valueKey] : opt;
            var label = typeof opt === "object" ? opt[labelKey] : opt;
            el.innerHTML +=
                '<option value="' +
                API.escapeHtml(val) +
                '">' +
                API.escapeHtml(String(label)) +
                "</option>";
        });
    }

    // ---- 地图 ----

    function initMap() {
        mapState = MapMod.createMap("route-map", [39.96, 116.35], 15, { showTile: false });
        updateTileNote(null);
    }

    function updateMapForMeta(meta) {
        if (!mapState || !meta) return;
        if (meta.center && meta.center[0] !== 0 && meta.center[1] !== 0) {
            mapState.map.setView(meta.center, meta.default_zoom || 16);
        }
        if (mapState.setTileVisible) {
            mapState.setTileVisible(meta.show_tile === true);
        }
        updateTileNote(meta);
    }

    function updateTileNote(meta) {
        var el = document.getElementById("map-source-note");
        if (!el) return;
        if (!meta) {
            el.innerHTML = '<span class="tag tag-info">请选择目的地</span>';
            return;
        }
        if (meta.show_tile) {
            el.innerHTML =
                '<span class="tag tag-campus">真实 OSM 内部道路图</span> ' +
                API.escapeHtml(meta.tile_note || "");
        } else {
            el.innerHTML =
                '<span class="tag tag-warning">抽象内部地图模板</span> ' +
                API.escapeHtml(meta.tile_note || "该目的地复用抽象内部地图模板，不叠加真实地图瓦片。");
        }
    }

    function drawRouteOnMap(data) {
        if (!mapState) return;
        // 只清除路线层和标记层，保留基础路网
        MapMod.clearRouteLayers(mapState);
        MapMod.clearMarkerLayers(mapState);

        // 优先使用 route_geometry 绘制路线
        if (data.route_geometry && data.route_geometry.length > 0) {
            MapMod.drawRoute(mapState, data.route_geometry, { color: "#e74c3c", weight: 5, opacity: 0.85 });
        } else if (data.coordinates && data.coordinates.length > 0) {
            MapMod.drawRoute(mapState, data.coordinates, { color: "#e74c3c", weight: 5, opacity: 0.85 });
        } else if (data.path && nodesMap) {
            var coords = [];
            data.path.forEach(function (nid) {
                var n = nodesMap[nid];
                if (n && Math.abs(n.latitude) > 0.001 && Math.abs(n.longitude) > 0.001) {
                    coords.push([n.latitude, n.longitude]);
                }
            });
            if (coords.length > 0) {
                MapMod.drawRoute(mapState, coords, { color: "#e74c3c", weight: 5, opacity: 0.85 });
            }
        }

        // 起点/终点标记
        var markers = [];
        if (data.path && data.path.length > 0) {
            var startN = nodesMap[data.path[0]];
            var endN = nodesMap[data.path[data.path.length - 1]];
            if (startN) {
                markers.push({ lat: startN.latitude, lng: startN.longitude, label: "起点: " + (startN.name || startN.id), type: "start" });
            }
            if (endN) {
                markers.push({ lat: endN.latitude, lng: endN.longitude, label: "终点: " + (endN.name || endN.id), type: "end" });
            }
        }

        if (data.visit_order) {
            data.visit_order.forEach(function (nid, i) {
                var n = nodesMap[nid];
                if (n) {
                    markers.push({ lat: n.latitude, lng: n.longitude, label: "途经" + (i + 1) + ": " + (n.name || n.id), type: "waypoint" });
                }
            });
        }

        MapMod.drawMarkers(mapState, markers);

        // 分段路线（使用 routeLayer）
        if (data.segments) {
            var graphCoords = {};
            if (nodesMap) {
                Object.keys(nodesMap).forEach(function (nid) {
                    var n = nodesMap[nid];
                    if (Math.abs(n.latitude) > 0.001 && Math.abs(n.longitude) > 0.001) {
                        graphCoords[nid] = [n.latitude, n.longitude];
                    }
                });
            }
            MapMod.drawRouteWithSegments(mapState, data.segments, graphCoords);
        }
    }

    // ---- 渲染 ----

    function renderRouteResult(data) {
        var el = document.getElementById("route-result");
        if (!el) return;

        var html = "";

        html += '<table style="margin-bottom:12px;">';
        var rows = [
            ["目的地", API.escapeHtml(data.destination_name || "")],
            ["类型", data.destination_type === "campus" ? '<span class="tag tag-campus">校园</span>' : '<span class="tag tag-attraction">景区</span>'],
            ["内部地图 ID", '<code>' + API.escapeHtml(data.internal_map_id || "") + "</code>"],
            ["策略", '<span class="tag tag-algorithm">' + API.escapeHtml(data.strategy || "") + "</span>"],
            ["算法", API.escapeHtml(data.algorithm || "")],
            ["是否可达", data.reachable ? '<span class="tag tag-campus">可达</span>' : '<span class="tag tag-warning">不可达</span>'],
            ["总距离", API.formatDistance(data.total_distance)],
            ["总时间", API.formatTime(data.total_time)],
        ];
        if (data.formula) {
            rows.push(["计算公式", '<code>' + API.escapeHtml(data.formula) + "</code>"]);
        }
        if (data.note) {
            rows.push(["备注", '<span class="tag tag-warning">' + API.escapeHtml(data.note) + "</span>"]);
        }

        if (data.visit_order) {
            rows.push(["访问顺序", data.visit_order.map(API.escapeHtml).join(" → ")]);
            rows.push(["TSP 近似", '<span class="tag tag-info">' + API.escapeHtml(data.tsp_approximation || "") + "</span>"]);
            rows.push(["返回起点", data.returns_to_start ? "是" : "否"]);
        }

        rows.forEach(function (r) {
            html += "<tr><td style='width:120px;font-weight:600;'>" + r[0] + "</td><td>" + r[1] + "</td></tr>";
        });
        html += "</table>";

        if (data.path && data.path.length > 0) {
            html +=
                '<p style="font-size:0.85em; color:#777; margin-top:8px;">路径: ' +
                data.path.map(function (n) {
                    return "<code>" + API.escapeHtml(n) + "</code>";
                }).join(" → ") +
                "</p>";
        }

        el.innerHTML = html;
        renderSegmentsTable(data.segments);
    }

    function renderSegmentsTable(segments) {
        var card = document.getElementById("segments-card");
        var container = document.getElementById("segments-container");
        if (!card || !container) return;
        if (!segments || segments.length === 0) {
            card.style.display = "none";
            return;
        }

        card.style.display = "";
        var html = '<table class="segment-table"><thead><tr>';
        html += "<th>起点</th><th>终点</th><th>距离</th><th>交通</th><th>拥挤度</th><th>理想速度</th><th>真实速度</th><th>耗时</th>";
        html += "</tr></thead><tbody>";

        segments.forEach(function (seg) {
            html += "<tr>";
            html += "<td>" + API.escapeHtml(seg.from_name || seg.from) + "</td>";
            html += "<td>" + API.escapeHtml(seg.to_name || seg.to) + "</td>";
            html += "<td>" + API.formatDistance(seg.distance) + "</td>";
            html +=
                "<td>" +
                (seg.transport === "bike"
                    ? '<span class="tag tag-campus">bike</span>'
                    : seg.transport === "sightseeing_car"
                    ? '<span class="tag tag-attraction">sightseeing_car</span>'
                    : '<span class="tag tag-info">walk</span>') +
                "</td>";
            html += "<td>" + (seg.congestion !== undefined ? seg.congestion.toFixed(2) : "—") + "</td>";
            html += "<td>" + (seg.ideal_speed !== undefined ? seg.ideal_speed.toFixed(1) + " m/s" : "—") + "</td>";
            html += "<td>" + (seg.real_speed !== undefined ? seg.real_speed.toFixed(2) + " m/s" : "—") + "</td>";
            html += "<td>" + API.formatTime(seg.time) + "</td>";
            html += "</tr>";
        });

        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function clearResults() {
        var el = document.getElementById("route-result");
        if (el) el.innerHTML = '<p class="hint">请选择目的地、起点、终点后点击"规划路线"</p>';
        var card = document.getElementById("segments-card");
        if (card) card.style.display = "none";
    }

    // ---- 业务逻辑 ----

    function loadDestinations() {
        API.loadDestinations({ limit: 217 })
            .then(function (data) {
                var results = data.results || [];
                setSelectOptions("select-dest", results, "id", "name");
            })
            .catch(function (err) {
                API.showError("route-result", err);
            });
    }

    function onDestinationChange() {
        var destId = getSelectVal("select-dest");
        if (!destId) {
            setSelectOptions("select-start", [], "", "");
            setSelectOptions("select-end", [], "", "");
            updateTileNote(null);
            if (mapState) {
                MapMod.clearBaseLayers(mapState);
                MapMod.clearRouteLayers(mapState);
                MapMod.clearMarkerLayers(mapState);
            }
            return;
        }

        updateTransportHint(destId);
        clearResults();
        if (mapState) {
            MapMod.clearBaseLayers(mapState);
            MapMod.clearRouteLayers(mapState);
            MapMod.clearMarkerLayers(mapState);
        }

        // 使用新的 map-layers API
        API.getMapLayers(destId)
            .then(function (data) {
                var allNodes = data.nodes || [];
                currentEdges = data.edges || [];
                currentFacilities = data.facilities || [];

                // 所有节点（含 gate/building 等，即使坐标为 0 也过滤掉）
                var validNodes = allNodes.filter(function (n) {
                    return Math.abs(n.latitude) > 0.001 && Math.abs(n.longitude) > 0.001;
                });

                nodesMap = {};
                validNodes.forEach(function (n) {
                    nodesMap[n.id] = n;
                });

                // 设置下拉选项（优先语义节点，如果节点太多则限制）
                var selectableNodes = validNodes.filter(function (n) {
                    return n.type === "gate" || n.type === "scenic_spot" || n.type === "building" || n.type === "intersection";
                });
                // 对于大型真实地图（>100个可选择节点），只显示 POI 节点 + 部分路口
                if (selectableNodes.length > 100) {
                    selectableNodes = selectableNodes.filter(function (n) {
                        return n.type === "gate" || n.type === "scenic_spot" || n.type === "building" ||
                            (n.id && (n.id.indexOf("POI_") === 0 || n.id.indexOf("NODE_BUP_") === 0 || n.id.indexOf("NODE_TSR_") === 0));
                    });
                }
                setSelectOptions("select-start", selectableNodes, "id", "name");
                setSelectOptions("select-end", selectableNodes, "id", "name");

                // 处理 internal_map metadata
                currentMapMeta = data.internal_map || null;
                updateMapForMeta(currentMapMeta);

                // 绘制完整内部道路网络
                MapMod.drawBaseNetwork(mapState, validNodes, currentEdges, currentFacilities);
            })
            .catch(function (err) {
                API.showError("route-result", err);
            });
    }

    function updateTransportHint(destId) {
        var hintEl = document.getElementById("transport-hint");
        if (!hintEl) return;

        API.loadDestinations({ limit: 217 })
            .then(function (data) {
                var results = data.results || [];
                var found = null;
                for (var i = 0; i < results.length; i++) {
                    if (results[i].id === destId) {
                        found = results[i];
                        break;
                    }
                }
                if (!found) return;

                if (found.type === "campus") {
                    hintEl.innerHTML =
                        '<span class="tag tag-campus">校园</span> 支持: walk / bike | <span class="tag tag-warning">不支持 sightseeing_car</span>';
                } else if (found.type === "attraction") {
                    hintEl.innerHTML =
                        '<span class="tag tag-attraction">景区</span> 支持: walk / sightseeing_car | <span class="tag tag-warning">不支持 bike</span>';
                } else {
                    hintEl.innerHTML =
                        '<span class="tag tag-info">混合</span> 支持: walk / bike / sightseeing_car';
                }
            })
            .catch(function () {
                hintEl.innerHTML = "";
            });
    }

    function planRoute() {
        var destId = getSelectVal("select-dest");
        var start = getSelectVal("select-start");
        var end = getSelectVal("select-end");
        var strategy = getSelectVal("select-strategy");
        var transport = getSelectVal("select-transport");

        if (!destId || !start || !end) {
            API.showError("route-result", new Error("请选择目的地、起点和终点"));
            return;
        }

        var params = { destination_id: destId, start: start, end: end };

        var endpoint;
        if (strategy === "shortest-distance") {
            endpoint = "/route/shortest-distance";
        } else if (strategy === "shortest-time") {
            endpoint = "/route/shortest-time";
            params.transport = transport;
        } else if (strategy === "transport-time") {
            endpoint = "/route/transport-time";
            params.transport = transport;
        } else if (strategy === "mixed-time") {
            endpoint = "/route/mixed-time";
        }

        API.showLoading("route-result", "正在规划路线...");
        document.getElementById("segments-card").style.display = "none";

        API.apiGet(endpoint, params)
            .then(function (data) {
                renderRouteResult(data);
                drawRouteOnMap(data);
            })
            .catch(function (err) {
                API.showError("route-result", err);
            });
    }

    function planMultiPoint() {
        var destId = getSelectVal("select-dest");
        var start = getSelectVal("select-start");
        var targetsRaw = document.getElementById("input-targets").value.trim();
        var strategy = getSelectVal("select-multi-strategy");

        if (!destId || !start || !targetsRaw) {
            API.showError("route-result", new Error("请选择目的地、起点并输入途经节点"));
            return;
        }

        var targets = targetsRaw
            .split(/[,，\s]+/)
            .filter(function (t) {
                return t.length > 0;
            });

        if (targets.length === 0) {
            API.showError("route-result", new Error("请输入至少一个途经节点"));
            return;
        }

        API.showLoading("route-result", "正在规划多目标路线...");
        document.getElementById("segments-card").style.display = "none";

        API.apiPost("/route/multi-point", {
            destination_id: destId,
            start: start,
            targets: targets,
            strategy: strategy,
        })
            .then(function (data) {
                renderRouteResult(data);
                drawRouteOnMap(data);
            })
            .catch(function (err) {
                API.showError("route-result", err);
            });
    }

    // ---- 初始化 ----

    function init() {
        initMap();
        loadDestinations();

        document.getElementById("select-dest").addEventListener("change", onDestinationChange);
        document.getElementById("btn-plan").addEventListener("click", planRoute);
        document.getElementById("btn-multi-plan").addEventListener("click", planMultiPoint);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
