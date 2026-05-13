/**
 * PathPal 旅游推荐页面 JS
 */
(function () {
    "use strict";

    var API = window.PathPalAPI;
    if (!API) return;

    function renderResults(data, containerId) {
        var el = document.getElementById(containerId);
        if (!el) return;

        var results = data.results || [];
        if (results.length === 0) {
            el.innerHTML = '<p class="hint">没有找到匹配的目的地</p>';
            return;
        }

        var html = "";

        // 算法/数据结构标签
        if (data.algorithm) {
            html +=
                '<p style="margin-bottom:10px;">' +
                '<span class="tag tag-algorithm">算法: ' +
                API.escapeHtml(data.algorithm) +
                "</span> " +
                '<span class="tag tag-info">数据结构: ' +
                API.escapeHtml(data.data_structure) +
                "</span> " +
                '<span class="tag tag-info">结果数: ' +
                (data.count !== undefined ? data.count : results.length) +
                "</span>" +
                "</p>";
        }
        if (data.user_id) {
            html +=
                '<p style="margin-bottom:8px;font-size:0.85em;">用户: <strong>' +
                API.escapeHtml(data.user_id) +
                "</strong> | 兴趣: " +
                (data.user_interests || []).map(API.escapeHtml).join(", ") +
                "</p>";
        }
        if (data.keyword) {
            html +=
                '<p style="margin-bottom:8px;font-size:0.85em;">关键词: <strong>' +
                API.escapeHtml(data.keyword) +
                "</strong>" +
                (data.sort_by ? " | 排序: " + API.escapeHtml(data.sort_by) : "") +
                "</p>";
        }
        if (data.category) {
            html +=
                '<p style="margin-bottom:8px;font-size:0.85em;">类别: <strong>' +
                API.escapeHtml(data.category) +
                "</strong>" +
                (data.sort_by ? " | 排序: " + API.escapeHtml(data.sort_by) : "") +
                "</p>";
        }

        // 结果表格
        html += '<table><thead><tr>';
        html += "<th>名称</th><th>类型</th><th>类别</th><th>热度</th><th>评分</th><th>标签</th>";
        if (results[0] && results[0].interest_score !== undefined) {
            html += "<th>兴趣分</th><th>推荐理由</th>";
        }
        html += "</tr></thead><tbody>";

        results.forEach(function (r) {
            html += "<tr>";
            html += "<td><strong>" + API.escapeHtml(r.name || "") + "</strong></td>";
            html +=
                "<td>" +
                (r.type === "campus"
                    ? '<span class="tag tag-campus">校园</span>'
                    : r.type === "attraction"
                    ? '<span class="tag tag-attraction">景区</span>'
                    : API.escapeHtml(r.type || "")) +
                "</td>";
            html += "<td>" + API.escapeHtml(r.category || "") + "</td>";
            html += "<td>" + (r.popularity !== undefined ? r.popularity : "—") + "</td>";
            html += "<td>" + (r.rating !== undefined ? r.rating : "—") + "</td>";
            html +=
                "<td>" +
                (r.tags || []).map(function (t) {
                    return '<span class="tag tag-info">' + API.escapeHtml(t) + "</span>";
                }).join(" ") +
                "</td>";
            if (r.interest_score !== undefined) {
                html += "<td><strong>" + r.interest_score + "</strong></td>";
                html +=
                    "<td style='font-size:0.85em;'>" +
                    (r.matched_terms || r.recommendation_reason || []).map(API.escapeHtml).join(", ") +
                    "</td>";
            }
            html += "</tr>";
        });

        html += "</tbody></table>";
        el.innerHTML = html;
    }

    function handleError(err) {
        API.showError("result-container", err);
    }

    // ---- 事件绑定 ----

    function bindClick(id, handler) {
        var btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener("click", handler);
        }
    }

    function init() {
        bindClick("btn-hot", function () {
            API.showLoading("result-container", "正在加载热度推荐...");
            API.apiGet("/recommendations/hot", { k: 10 })
                .then(function (d) {
                    renderResults(d, "result-container");
                })
                .catch(handleError);
        });

        bindClick("btn-rating", function () {
            API.showLoading("result-container", "正在加载评分推荐...");
            API.apiGet("/recommendations/rating", { k: 10 })
                .then(function (d) {
                    renderResults(d, "result-container");
                })
                .catch(handleError);
        });

        bindClick("btn-interest", function () {
            var uid = document.getElementById("input-user-id").value.trim();
            if (!uid) {
                API.showError("result-container", new Error("请输入用户 ID"));
                return;
            }
            API.showLoading("result-container", "正在加载兴趣推荐...");
            API.apiGet("/recommendations/interest", { user_id: uid, k: 10 })
                .then(function (d) {
                    renderResults(d, "result-container");
                })
                .catch(handleError);
        });

        bindClick("btn-search", function () {
            var kw = document.getElementById("input-keyword").value.trim();
            if (!kw) {
                API.showError("result-container", new Error("请输入关键词"));
                return;
            }
            var sortBy = document.getElementById("select-sort").value;
            var params = { keyword: kw };
            if (sortBy) params.sort_by = sortBy;
            API.showLoading("result-container", "正在搜索...");
            API.apiGet("/destinations/search", params)
                .then(function (d) {
                    renderResults(d, "result-container");
                })
                .catch(handleError);
        });

        bindClick("btn-category", function () {
            var cat = document.getElementById("input-category").value.trim();
            if (!cat) {
                API.showError("result-container", new Error("请输入类别"));
                return;
            }
            var sortBy = document.getElementById("select-cat-sort").value;
            var params = { category: cat };
            if (sortBy) params.sort_by = sortBy;
            API.showLoading("result-container", "正在过滤...");
            API.apiGet("/destinations/category", params)
                .then(function (d) {
                    renderResults(d, "result-container");
                })
                .catch(handleError);
        });

        bindClick("btn-list", function () {
            var typeVal = document.getElementById("select-type").value;
            var params = { limit: 100 };
            if (typeVal) params.type = typeVal;
            API.showLoading("result-container", "正在加载目的地列表...");
            API.apiGet("/destinations", params)
                .then(function (d) {
                    renderResults(d, "result-container");
                })
                .catch(handleError);
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
