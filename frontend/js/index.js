/**
 * PathPal 首页 — 加载统计数据
 */
(function () {
    "use strict";

    var API = window.PathPalAPI;
    if (!API) {
        console.error("PathPalAPI not loaded");
        return;
    }

    function renderStats(data) {
        var container = document.getElementById("stats-container");
        if (!container) return;

        var items = [
            { key: "destinations", label: "目的地" },
            { key: "internal_maps", label: "内部地图模板" },
            { key: "internal_nodes", label: "内部节点" },
            { key: "internal_edges", label: "道路边" },
            { key: "facilities", label: "服务设施" },
            { key: "facility_categories", label: "设施类别" },
            { key: "users", label: "用户" },
        ];

        var html = '<div class="stats-grid">';
        items.forEach(function (item) {
            var val = data[item.key] !== undefined ? data[item.key] : "—";
            html +=
                '<div class="stat-card">' +
                '<div class="stat-value">' +
                val +
                "</div>" +
                '<div class="stat-label">' +
                API.escapeHtml(item.label) +
                "</div>" +
                "</div>";
        });
        html += "</div>";
        container.innerHTML = html;
    }

    function init() {
        API.loadStats()
            .then(renderStats)
            .catch(function (err) {
                API.showError("stats-container", err);
            });
    }

    // 页面加载完成后执行
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
