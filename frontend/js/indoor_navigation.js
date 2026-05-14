/**
 * PathPal 室内导航页面 JS
 * 支持 SVG 楼层拓扑图展示、Dijkstra 最短路径、跨层电梯/楼梯导航。
 */
(function () {
    "use strict";

    var API = window.PathPalAPI;
    if (!API) {
        console.error("[indoor_navigation] PathPalAPI not loaded — check api.js");
        return;
    }

    var state = {
        buildings: [],
        currentBuilding: null,
        currentNodes: [],
        routeResult: null,
    };

    var BUILDING_TYPE_LABELS = {
        campus_building: "校园建筑",
        scenic_exhibition: "景区展馆",
    };

    // ================================================================
    // 节点颜色映射
    // ================================================================
    var NODE_COLORS = {
        entrance: "#4a90d9",
        lobby: "#7eb8e0",
        elevator: "#4caf50",
        stairs: "#ff9800",
        corridor: "#bdbdbd",
        classroom: "#ffd54f",
        office: "#ab47bc",
        restroom: "#ef9a9a",
        service_point: "#009688",
        exhibition_hall: "#ff7043",
        exit: "#e53935",
    };

    function nodeColor(type) {
        return NODE_COLORS[type] || "#90a4ae";
    }

    // ================================================================
    // 初始化
    // ================================================================
    function init() {
        console.log("[indoor_nav] init() — DOM readyState:", document.readyState);
        try {
            var bldSel = document.getElementById("building-select");
            console.log("[indoor_nav] building-select found:", !!bldSel);
            if (bldSel) bldSel.addEventListener("change", onBuildingChange);
            var flrSel = document.getElementById("floor-filter");
            if (flrSel) flrSel.addEventListener("change", onFloorFilterChange);
            setBuildingStatus("加载中...");
            loadBuildings();
        } catch (e) {
            console.error("[indoor_navigation] init error:", e);
            setBuildingStatus("初始化失败: " + e.message, true);
        }
    }

    function setBuildingStatus(msg, isError) {
        var el = document.getElementById("building-status");
        if (el) {
            el.textContent = msg;
            el.style.color = isError ? "#e53935" : "#999";
        }
    }

    // ================================================================
    // 加载建筑列表
    // ================================================================
    function loadBuildings() {
        console.log("[indoor_nav] loadBuildings() — fetching /indoor/buildings...");
        API.apiGet("/indoor/buildings")
            .then(function (data) {
                console.log("[indoor_nav] /indoor/buildings response:", data);
                var buildings = data.buildings || [];
                state.buildings = buildings;
                console.log("[indoor_nav] buildings count:", buildings.length);
                var sel = document.getElementById("building-select");
                if (!sel) {
                    console.error("[indoor_nav] building-select element NOT FOUND in DOM");
                    setBuildingStatus("DOM元素丢失", true);
                    return;
                }
                buildings.forEach(function (b) {
                    var opt = document.createElement("option");
                    opt.value = b.building_id;
                    var typeLabel = BUILDING_TYPE_LABELS[b.building_type] || b.building_type || "";
                    opt.textContent = b.building_name + " (" + typeLabel + ", " + (b.floors || []).length + "层)";
                    sel.appendChild(opt);
                    console.log("[indoor_nav] added option:", opt.value, opt.textContent);
                });
                setBuildingStatus("已加载 " + buildings.length + " 栋建筑");
            })
            .catch(function (err) {
                console.error("[indoor_nav] loadBuildings FAILED:", err.message || err);
                setBuildingStatus("加载失败: " + (err.message || err), true);
                showIndoorError(err);
            });
    }

    // ================================================================
    // 建筑切换
    // ================================================================
    function onBuildingChange() {
        var buildingId = document.getElementById("building-select").value;
        console.log("[indoor_nav] onBuildingChange() — buildingId:", buildingId || "(empty)");
        clearResults();
        if (!buildingId) {
            resetNodeSelects();
            clearFloorGraphs();
            return;
        }

        // 加载建筑详情
        console.log("[indoor_nav] fetching /indoor/buildings/" + buildingId + "...");
        API.apiGet("/indoor/buildings/" + encodeURIComponent(buildingId))
            .then(function (building) {
                console.log("[indoor_nav] building detail loaded, nodes:", (building.nodes || []).length);
                state.currentBuilding = building;
                state.currentNodes = building.nodes || [];
                loadFloors(building);
                populateNodeSelects(building.nodes || []);
                renderFloorGraphs(building, null);
            })
            .catch(function (err) {
                console.error("[indoor_nav] onBuildingChange FAILED:", err.message || err);
                showIndoorError(err);
            });
    }

    function onFloorFilterChange() {
        if (!state.currentBuilding) return;
        var floorVal = document.getElementById("floor-filter").value;
        var nodes = state.currentBuilding.nodes || [];
        if (floorVal !== "") {
            nodes = nodes.filter(function (n) { return String(n.floor) === floorVal; });
        }
        populateNodeSelects(nodes);
    }

    function loadFloors(building) {
        var sel = document.getElementById("floor-filter");
        sel.innerHTML = '<option value="">全部楼层</option>';
        (building.floors || []).forEach(function (f) {
            var opt = document.createElement("option");
            opt.value = String(f);
            opt.textContent = f + "F";
            sel.appendChild(opt);
        });
    }

    function populateNodeSelects(nodes) {
        var startSel = document.getElementById("start-select");
        var endSel = document.getElementById("end-select");
        startSel.innerHTML = "";
        endSel.innerHTML = "";

        // 按楼层分组
        var byFloor = {};
        nodes.forEach(function (n) {
            var f = String(n.floor);
            if (!byFloor[f]) byFloor[f] = [];
            byFloor[f].push(n);
        });

        Object.keys(byFloor).sort(function (a, b) { return Number(a) - Number(b); }).forEach(function (f) {
            var groupLabel = f + "F";
            addOptGroup(startSel, groupLabel, byFloor[f]);
            addOptGroup(endSel, groupLabel, byFloor[f]);
        });
    }

    function addOptGroup(sel, label, nodes) {
        var grp = document.createElement("optgroup");
        grp.label = label;
        nodes.forEach(function (n) {
            var opt = document.createElement("option");
            opt.value = n.id;
            opt.textContent = n.name + " [" + n.type + "]";
            grp.appendChild(opt);
        });
        sel.appendChild(grp);
    }

    function resetNodeSelects() {
        var empty = '<option value="">— 请先选择建筑 —</option>';
        document.getElementById("start-select").innerHTML = empty;
        document.getElementById("end-select").innerHTML = empty;
    }

    // ================================================================
    // 路径规划
    // ================================================================
    function planIndoorRoute() {
        var buildingId = document.getElementById("building-select").value;
        var start = document.getElementById("start-select").value;
        var end = document.getElementById("end-select").value;
        console.log("[indoor_nav] planIndoorRoute() — building:", buildingId, "start:", start, "end:", end);

        if (!buildingId || !start || !end) {
            showIndoorError(new Error("请选择建筑、起点和终点"));
            return;
        }

        clearResults();
        API.showLoading("indoor-error", "");

        API.apiGet("/indoor/route", {
            building_id: buildingId,
            start: start,
            end: end,
        })
            .then(function (result) {
                state.routeResult = result;
                document.getElementById("indoor-error").innerHTML = "";
                renderIndoorRoute(result);
                renderSteps(result.steps || []);
                renderFloorGraphs(state.currentBuilding, result);
            })
            .catch(function (err) {
                showIndoorError(err);
            });
    }

    // ================================================================
    // 结果显示
    // ================================================================
    function renderIndoorRoute(result) {
        var panel = document.getElementById("route-result-panel");
        var summary = document.getElementById("route-summary");
        panel.style.display = "block";

        var reachableHtml = result.reachable
            ? '<span style="color:green;">&#10003; 可达</span>'
            : '<span style="color:red;">&#10007; 不可达</span>';

        var pathStr = (result.path || []).join(" → ");

        summary.innerHTML =
            '<p><strong>建筑：</strong>' + API.escapeHtml(result.building_name || "") +
            ' | <strong>类型：</strong>' + API.escapeHtml(result.building_type || "") + "</p>" +
            '<p><strong>策略：</strong>' + API.escapeHtml(result.strategy || "") +
            ' | <strong>算法：</strong>' + API.escapeHtml(result.algorithm || "") +
            ' | <strong>距离：</strong>' + API.formatDistance(result.distance) +
            ' | <strong>状态：</strong>' + reachableHtml + "</p>" +
            '<p><strong>路径：</strong><small>' + API.escapeHtml(pathStr) + "</small></p>";

        // 楼层路径
        if (result.floor_paths) {
            var fpHtml = "";
            Object.keys(result.floor_paths).sort(function (a, b) { return Number(a) - Number(b); }).forEach(function (f) {
                fpHtml += "<li>" + f + "F: " + result.floor_paths[f].join(" → ") + "</li>";
            });
            if (fpHtml) {
                summary.innerHTML += '<p><strong>楼层路径：</strong></p><ul>' + fpHtml + "</ul>";
            }
        }
    }

    function renderSteps(steps) {
        var panel = document.getElementById("steps-panel");
        var tbody = document.getElementById("steps-table").querySelector("tbody");
        panel.style.display = "block";
        tbody.innerHTML = "";

        steps.forEach(function (s) {
            var tr = document.createElement("tr");
            var typeLabels = { start: "起点", end: "终点", elevator: "电梯", stairs: "楼梯", corridor: "走廊", doorway: "门" };
            tr.innerHTML =
                "<td>" + s.step + "</td>" +
                "<td>" + API.escapeHtml(s.description) + "</td>" +
                "<td>" + API.escapeHtml(typeLabels[s.type] || s.type || "") + "</td>" +
                "<td>" + (s.distance != null ? s.distance : "") + "</td>";
            tbody.appendChild(tr);
        });
    }

    // ================================================================
    // SVG 楼层拓扑图
    // ================================================================
    function renderFloorGraphs(building, routeResult) {
        var container = document.getElementById("floor-graphs-container");
        var panel = document.getElementById("floor-graphs-panel");
        container.innerHTML = "";
        panel.style.display = "block";

        if (!building || !building.nodes) return;

        var nodes = building.nodes || [];
        var edges = building.edges || [];
        var floors = building.floors || [];
        var pathSet = new Set();
        var pathEdgeSet = new Set();

        if (routeResult && routeResult.reachable) {
            (routeResult.path || []).forEach(function (nid) { pathSet.add(nid); });
            (routeResult.edges || []).forEach(function (e) {
                pathEdgeSet.add(e.from + "|" + e.to);
                pathEdgeSet.add(e.to + "|" + e.from);
            });
        }

        floors.forEach(function (floor) {
            var floorNodes = nodes.filter(function (n) { return n.floor === floor; });
            if (floorNodes.length === 0) return;

            // 找出该层涉及的边（包括跨层边中属于该层节点的）
            var floorNodeIds = new Set(floorNodes.map(function (n) { return n.id; }));
            var floorEdges = edges.filter(function (e) {
                return floorNodeIds.has(e.from) && floorNodeIds.has(e.to);
            });

            // 计算 SVG viewBox
            var xs = floorNodes.map(function (n) { return n.x; });
            var ys = floorNodes.map(function (n) { return n.y; });
            var minX = Math.min.apply(null, xs) - 30;
            var maxX = Math.max.apply(null, xs) + 80;
            var minY = Math.min.apply(null, ys) - 20;
            var maxY = Math.max.apply(null, ys) + 20;
            var w = maxX - minX;
            var h = maxY - minY;

            var wrapper = document.createElement("div");
            wrapper.className = "svg-floor-panel";
            wrapper.innerHTML = "<h4>" + floor + "F</h4>";

            var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svg.setAttribute("width", Math.max(w, 200));
            svg.setAttribute("height", Math.max(h, 150));
            svg.setAttribute("viewBox", minX + " " + minY + " " + w + " " + h);

            // 边
            floorEdges.forEach(function (e) {
                var fn = floorNodes.find(function (n) { return n.id === e.from; });
                var tn = floorNodes.find(function (n) { return n.id === e.to; });
                if (!fn || !tn) return;

                var line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                line.setAttribute("x1", fn.x);
                line.setAttribute("y1", fn.y);
                line.setAttribute("x2", tn.x);
                line.setAttribute("y2", tn.y);
                line.setAttribute("class", "edge-line");

                var isPathEdge = pathEdgeSet.has(e.from + "|" + e.to);
                var etype = e.type || "";
                if (isPathEdge) {
                    line.classList.add("path-highlight");
                } else if (etype === "elevator") {
                    line.setAttribute("stroke-dasharray", "4,2");
                } else if (etype === "stairs") {
                    line.setAttribute("stroke-dasharray", "3,3");
                }

                svg.appendChild(line);

                // 边标签（距离）
                var mx = (fn.x + tn.x) / 2;
                var my = (fn.y + tn.y) / 2;
                var etxt = document.createElementNS("http://www.w3.org/2000/svg", "text");
                etxt.setAttribute("x", mx);
                etxt.setAttribute("y", my - 4);
                etxt.setAttribute("class", "edge-label");
                etxt.setAttribute("text-anchor", "middle");
                etxt.textContent = e.distance + "m";
                svg.appendChild(etxt);
            });

            // 节点
            floorNodes.forEach(function (n) {
                var isPathNode = pathSet.has(n.id);
                var r = isPathNode ? 9 : 7;
                var color = nodeColor(n.type);

                var circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                circle.setAttribute("cx", n.x);
                circle.setAttribute("cy", n.y);
                circle.setAttribute("r", r);
                circle.setAttribute("fill", color);
                circle.setAttribute("stroke", isPathNode ? "#333" : "#fff");
                circle.setAttribute("stroke-width", isPathNode ? 2 : 1);
                circle.setAttribute("class", "node-circle");

                // 电梯/楼梯特殊标记
                if (n.type === "elevator") {
                    circle.setAttribute("stroke", "#2e7d32");
                    circle.setAttribute("stroke-width", 2.5);
                } else if (n.type === "stairs") {
                    circle.setAttribute("stroke", "#e65100");
                    circle.setAttribute("stroke-width", 2.5);
                }

                var title = document.createElementNS("http://www.w3.org/2000/svg", "title");
                title.textContent = n.name + " [" + n.type + "]";
                circle.appendChild(title);
                svg.appendChild(circle);

                // 名称标签
                var label = document.createElementNS("http://www.w3.org/2000/svg", "text");
                label.setAttribute("x", n.x + 10);
                label.setAttribute("y", n.y + 3);
                label.setAttribute("class", "node-label");
                label.setAttribute("font-weight", isPathNode ? "bold" : "normal");
                label.textContent = n.name;
                svg.appendChild(label);
            });

            wrapper.appendChild(svg);
            container.appendChild(wrapper);
        });
    }

    // ================================================================
    // 辅助
    // ================================================================

    function clearResults() {
        document.getElementById("route-result-panel").style.display = "none";
        document.getElementById("steps-panel").style.display = "none";
        document.getElementById("route-summary").innerHTML = "";
        document.getElementById("steps-table").querySelector("tbody").innerHTML = "";
    }

    function clearFloorGraphs() {
        document.getElementById("floor-graphs-container").innerHTML = "";
        document.getElementById("floor-graphs-panel").style.display = "none";
    }

    function showIndoorError(err) {
        API.showError("indoor-error", err);
    }

    // ================================================================
    // 导出
    // ================================================================
    window.indoorNav = {
        loadBuildings: loadBuildings,
        onBuildingChange: onBuildingChange,
        planIndoorRoute: planIndoorRoute,
        renderIndoorRoute: renderIndoorRoute,
        renderFloorGraphs: renderFloorGraphs,
        renderSteps: renderSteps,
        showIndoorError: showIndoorError,
    };

    // 页面初始化
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
