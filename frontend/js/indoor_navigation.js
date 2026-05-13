/**
 * PathPal 室内导航 Demo 页面 JS
 */
(function () {
    "use strict";

    var API = window.PathPalAPI;
    if (!API) return;

    var buildingNodesCache = {}; // buildingId -> nodes array

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

    // ---- 渲染 ----

    function renderRouteResult(data) {
        var el = document.getElementById("indoor-result");
        if (!el) return;

        var html = "";

        html += '<table style="margin-bottom:12px;">';
        var rows = [
            ["建筑", API.escapeHtml(data.building_name || data.building_id)],
            ["算法", '<span class="tag tag-algorithm">' + API.escapeHtml(data.algorithm || "") + "</span>"],
            ["是否可达", data.reachable ? '<span class="tag tag-campus">可达</span>' : '<span class="tag tag-warning">不可达</span>'],
            ["总距离", API.formatDistance(data.total_distance)],
        ];

        if (data.path && data.path.length > 0) {
            rows.push(["路径节点数", data.path.length]);
        }

        rows.forEach(function (r) {
            html += "<tr><td style='width:120px;font-weight:600;'>" + r[0] + "</td><td>" + r[1] + "</td></tr>";
        });
        html += "</table>";

        // 路径
        if (data.path && data.path.length > 0) {
            html +=
                '<p style="font-size:0.85em; color:#777; margin-top:8px;">路径: ' +
                data.path.map(function (n) {
                    return "<code>" + API.escapeHtml(n) + "</code>";
                }).join(" → ") +
                "</p>";
        }

        el.innerHTML = html;

        // 步骤详情
        renderSteps(data.steps);
    }

    function renderSteps(steps) {
        var card = document.getElementById("indoor-steps-card");
        var container = document.getElementById("indoor-steps-container");
        if (!card || !container) return;
        if (!steps || steps.length === 0) {
            card.style.display = "none";
            return;
        }

        card.style.display = "";
        var html = '<table><thead><tr><th>步骤</th><th>起点</th><th>终点</th><th>距离</th></tr></thead><tbody>';

        steps.forEach(function (step, i) {
            html += "<tr>";
            html += "<td>" + (i + 1) + "</td>";
            html += "<td>" + API.escapeHtml(step.from_name || step.from) + "</td>";
            html += "<td>" + API.escapeHtml(step.to_name || step.to) + "</td>";
            html += "<td>" + API.formatDistance(step.distance) + "</td>";
            html += "</tr>";
        });

        html += "</tbody></table>";
        container.innerHTML = html;
    }

    // ---- 业务 ----

    function loadBuildings() {
        API.apiGet("/indoor/buildings")
            .then(function (data) {
                var buildings = data.buildings || [];
                setOptions("select-building", buildings, "building_id", "name");

                // 缓存建筑信息
                buildings.forEach(function (b) {
                    buildingNodesCache[b.building_id] = null; // 待加载
                });
            })
            .catch(function (err) {
                API.showError("indoor-result", err);
            });
    }

    function onBuildingChange() {
        var buildingId = getVal("select-building");
        if (!buildingId) {
            setOptions("select-start-room", [], "", "");
            setOptions("select-end-room", [], "", "");
            return;
        }

        // 获取建筑详情（含节点列表）
        API.apiGet("/indoor/buildings")
            .then(function (buildingsData) {
                var buildings = buildingsData.buildings || [];
                var found = null;
                for (var i = 0; i < buildings.length; i++) {
                    if (buildings[i].building_id === buildingId) {
                        found = buildings[i];
                        break;
                    }
                }
                if (!found) return;

                // 用已知的建筑信息，构造节点列表
                // 实际节点详情需通过 route 端点测试，这里先尝试用 buildings 列表中的 node_count
                // 如果没有详细节点，用简单提示
                if (found.floors !== undefined && found.node_count > 0) {
                    // 需要获取节点详情来填充下拉框，尝试用 route 查询间接获取
                    // 由于 API 没有直接获取节点的端点，我们提供一个文本输入备选
                    var hintHtml =
                        '<p class="hint">该建筑有 ' +
                        found.node_count +
                        " 个节点，" +
                        found.edge_count +
                        " 条边。" +
                        "请在下方输入框中输入节点 ID（如 IN_B101, IN_B201 等）。</p>";

                    // 改为文本输入方式
                    var startEl = document.getElementById("select-start-room");
                    var endEl = document.getElementById("select-end-room");

                    // 如果是 select，替换为 input
                    if (startEl.tagName === "SELECT") {
                        var startInput = document.createElement("input");
                        startInput.type = "text";
                        startInput.id = "select-start-room";
                        startInput.placeholder = "例如: IN_B101";
                        startInput.style.width = "200px;";
                        startEl.parentNode.replaceChild(startInput, startEl);

                        var endInput = document.createElement("input");
                        endInput.type = "text";
                        endInput.id = "select-end-room";
                        endInput.placeholder = "例如: IN_B201";
                        endInput.style.width = "200px;";
                        endEl.parentNode.replaceChild(endInput, endEl);
                    }
                }
            })
            .catch(function () {
                // 忽略
            });
    }

    function planIndoorRoute() {
        var buildingId = getVal("select-building");
        var start = getVal("select-start-room");
        var end = getVal("select-end-room");

        if (!buildingId || !start || !end) {
            API.showError("indoor-result", new Error("请选择建筑并输入起点和终点"));
            return;
        }

        API.showLoading("indoor-result", "正在规划室内路线...");
        document.getElementById("indoor-steps-card").style.display = "none";

        API.apiGet("/indoor/route", {
            building_id: buildingId,
            start: start,
            end: end,
        })
            .then(function (data) {
                renderRouteResult(data);
            })
            .catch(function (err) {
                API.showError("indoor-result", err);
            });
    }

    // ---- 初始化 ----

    function init() {
        loadBuildings();

        document.getElementById("select-building").addEventListener("change", onBuildingChange);
        document.getElementById("btn-plan-indoor").addEventListener("click", planIndoorRoute);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
