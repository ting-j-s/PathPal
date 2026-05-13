/**
 * PathPal 场所查询页面 JS
 * 使用 map-layers API 绘制完整内部道路图 + 附近设施查询结果
 */
(function () {
    "use strict";

    var API = window.PathPalAPI;
    var MapMod = window.PathPalMap;
    if (!API || !MapMod) return;

    var mapState = null;
    var nodesMap = {};
    var currentOriginNode = null;
    var currentMapMeta = null;
    var currentEdges = [];
    var currentFacilities = [];

    function getVal(id) {
        var el = document.getElementById(id);
        return el ? el.value : "";
    }

    function setOptions(id, items, valKey, labelKey) {
        var el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '<option value="">— 请选择 —</option>';
        items.forEach(function (item) {
            var v = typeof item === "object" ? item[valKey] : item;
            var l = typeof item === "object" ? item[labelKey] : item;
            el.innerHTML +=
                '<option value="' + API.escapeHtml(v) + '">' + API.escapeHtml(String(l)) + "</option>";
        });
    }

    function setCategoryOptions(id, categories) {
        var el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '<option value="">全部类别</option>';
        categories.forEach(function (cat) {
            el.innerHTML += '<option value="' + API.escapeHtml(cat) + '">' + API.escapeHtml(cat) + "</option>";
        });
    }

    // ---- 地图 ----

    function initMap() {
        mapState = MapMod.createMap("nearby-map", [39.96, 116.35], 15, { showTile: false });
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

    function drawNearbyOnMap(data) {
        if (!mapState) return;
        // 只清除标记层和路线层，保留基础路网
        MapMod.clearRouteLayers(mapState);
        MapMod.clearMarkerLayers(mapState);

        // 原节点标记
        if (currentOriginNode) {
            MapMod.drawMarkers(mapState, [
                {
                    lat: currentOriginNode.latitude,
                    lng: currentOriginNode.longitude,
                    label: "当前位置: " + (currentOriginNode.name || currentOriginNode.id),
                    type: "start",
                },
            ]);
        }

        // 设施标记
        var facilities = data.facilities || [];
        MapMod.drawFacilityMarkers(mapState, facilities);
    }

    function drawFacilityRoute(facility) {
        if (!mapState || !facility) return;
        MapMod.clearRouteLayers(mapState);
        MapMod.clearMarkerLayers(mapState);

        if (currentOriginNode && facility.linked_node_id) {
            MapMod.drawMarkers(mapState, [
                {
                    lat: currentOriginNode.latitude,
                    lng: currentOriginNode.longitude,
                    label: "当前位置",
                    type: "start",
                },
                {
                    lat: facility.latitude,
                    lng: facility.longitude,
                    label: facility.name,
                    type: "end",
                },
            ]);

            // 优先使用 route_geometry
            if (facility.route_geometry && facility.route_geometry.length > 0) {
                MapMod.drawRoute(mapState, facility.route_geometry, { color: "#e74c3c", weight: 4, opacity: 0.8 });
            } else if (facility.path && nodesMap) {
                var coords = [];
                facility.path.forEach(function (nid) {
                    var n = nodesMap[nid];
                    if (n && Math.abs(n.latitude) > 0.001) {
                        coords.push([n.latitude, n.longitude]);
                    }
                });
                if (coords.length > 0) {
                    MapMod.drawRoute(mapState, coords, { color: "#e74c3c", weight: 4, opacity: 0.8 });
                }
            }
        }
    }

    // ---- 渲染 ----

    function renderFacilities(data) {
        var el = document.getElementById("nearby-result");
        if (!el) return;

        var facilities = data.facilities || [];

        var html = "";

        html +=
            '<p style="margin-bottom:10px;">' +
            '<span class="tag tag-algorithm">算法: ' +
            API.escapeHtml(data.algorithm || "") +
            "</span> " +
            '<span class="tag tag-info">数据结构: ' +
            API.escapeHtml(data.data_structure || "") +
            "</span> " +
            '<span class="tag tag-info">结果数: ' +
            (data.count !== undefined ? data.count : facilities.length) +
            "</span>" +
            "</p>";

        if (data.note) {
            html +=
                '<p style="margin-bottom:8px;"><span class="tag tag-warning">' +
                API.escapeHtml(data.note) +
                "</span></p>";
        }

        if (facilities.length === 0) {
            html += '<p class="hint">未找到附近设施</p>';
            el.innerHTML = html;
            return;
        }

        html += '<table><thead><tr>';
        html += "<th>名称</th><th>类别</th><th>道路距离</th><th>关联节点</th><th>描述</th><th>操作</th>";
        html += "</tr></thead><tbody>";

        facilities.forEach(function (f, idx) {
            html += "<tr>";
            html += "<td><strong>" + API.escapeHtml(f.name || "") + "</strong></td>";
            html += "<td>" + API.escapeHtml(f.category || "") + "</td>";
            html += "<td><strong>" + API.formatDistance(f.road_distance) + "</strong></td>";
            html += "<td><code>" + API.escapeHtml(f.linked_node_id || "") + "</code></td>";
            html += "<td style='font-size:0.85em;'>" + API.escapeHtml(f.description || "") + "</td>";
            html +=
                '<td><button class="secondary" data-facility-idx="' +
                idx +
                '" style="font-size:0.8em;padding:4px 8px;">查看路径</button></td>';
            html += "</tr>";
        });

        html += "</tbody></table>";
        el.innerHTML = html;

        el.querySelectorAll("button[data-facility-idx]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var idx = parseInt(this.getAttribute("data-facility-idx"));
                if (facilities[idx]) {
                    drawFacilityRoute(facilities[idx]);
                }
            });
        });
    }

    // ---- 业务 ----

    function loadDestinations() {
        API.loadDestinations({ limit: 217 })
            .then(function (data) {
                var results = data.results || [];
                setOptions("select-dest", results, "id", "name");
            })
            .catch(function (err) {
                API.showError("nearby-result", err);
            });
    }

    function onDestinationChange() {
        var destId = getVal("select-dest");
        if (!destId) {
            setOptions("select-node", [], "", "");
            setCategoryOptions("select-category", []);
            updateTileNote(null);
            if (mapState) {
                MapMod.clearBaseLayers(mapState);
                MapMod.clearRouteLayers(mapState);
                MapMod.clearMarkerLayers(mapState);
            }
            return;
        }

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

                var validNodes = allNodes.filter(function (n) {
                    return Math.abs(n.latitude) > 0.001 && Math.abs(n.longitude) > 0.001;
                });

                nodesMap = {};
                validNodes.forEach(function (n) {
                    nodesMap[n.id] = n;
                });

                var selectableNodes = validNodes.filter(function (n) {
                    return n.type === "gate" || n.type === "scenic_spot" || n.type === "building" || n.type === "intersection";
                });
                // 对于大型真实地图（>100个可选择节点），只显示 POI 节点
                if (selectableNodes.length > 100) {
                    selectableNodes = selectableNodes.filter(function (n) {
                        return n.type === "gate" || n.type === "scenic_spot" || n.type === "building" ||
                            (n.id && (n.id.indexOf("POI_") === 0 || n.id.indexOf("NODE_BUP_") === 0 || n.id.indexOf("NODE_TSR_") === 0));
                    });
                }
                setOptions("select-node", selectableNodes, "id", "name");

                currentMapMeta = data.internal_map || null;
                updateMapForMeta(currentMapMeta);

                // 绘制完整内部道路网络
                MapMod.drawBaseNetwork(mapState, validNodes, currentEdges, currentFacilities);
            })
            .catch(function (err) {
                API.showError("nearby-result", err);
            });

        // 加载类别
        API.apiGet("/nearby/categories", { destination_id: destId })
            .then(function (data) {
                setCategoryOptions("select-category", data.categories || []);
            })
            .catch(function () {});
    }

    function findNearby() {
        var destId = getVal("select-dest");
        var nodeId = getVal("select-node");
        var radius = getVal("input-radius");

        if (!destId || !nodeId) {
            API.showError("nearby-result", new Error("请选择目的地和当前节点"));
            return;
        }

        currentOriginNode = nodesMap[nodeId] || null;

        var params = { destination_id: destId, node_id: nodeId };
        if (radius) params.radius = parseFloat(radius);

        API.showLoading("nearby-result", "正在查询附近设施...");

        API.apiGet("/nearby", params)
            .then(function (data) {
                renderFacilities(data);
                drawNearbyOnMap(data);
            })
            .catch(function (err) {
                API.showError("nearby-result", err);
            });
    }

    function findByCategory() {
        var destId = getVal("select-dest");
        var nodeId = getVal("select-node");
        var category = getVal("select-category");
        var radius = getVal("input-radius");

        if (!destId || !nodeId || !category) {
            API.showError("nearby-result", new Error("请选择目的地、节点和类别"));
            return;
        }

        currentOriginNode = nodesMap[nodeId] || null;

        var params = { destination_id: destId, node_id: nodeId, category: category };
        if (radius) params.radius = parseFloat(radius);

        API.showLoading("nearby-result", "正在按类别查询...");

        API.apiGet("/nearby/category", params)
            .then(function (data) {
                renderFacilities(data);
                drawNearbyOnMap(data);
            })
            .catch(function (err) {
                API.showError("nearby-result", err);
            });
    }

    function searchNearby() {
        var destId = getVal("select-dest");
        var nodeId = getVal("select-node");
        var keyword = getVal("input-keyword");
        var radius = getVal("input-radius");

        if (!destId || !nodeId || !keyword) {
            API.showError("nearby-result", new Error("请选择目的地、节点并输入关键词"));
            return;
        }

        currentOriginNode = nodesMap[nodeId] || null;

        var params = { destination_id: destId, node_id: nodeId, keyword: keyword };
        if (radius) params.radius = parseFloat(radius);

        API.showLoading("nearby-result", "正在搜索...");

        API.apiGet("/nearby/search", params)
            .then(function (data) {
                renderFacilities(data);
                drawNearbyOnMap(data);
            })
            .catch(function (err) {
                API.showError("nearby-result", err);
            });
    }

    // ---- 初始化 ----

    function init() {
        initMap();
        loadDestinations();

        document.getElementById("select-dest").addEventListener("change", onDestinationChange);
        document.getElementById("btn-nearby").addEventListener("click", findNearby);
        document.getElementById("btn-category").addEventListener("click", findByCategory);
        document.getElementById("btn-search").addEventListener("click", searchNearby);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
