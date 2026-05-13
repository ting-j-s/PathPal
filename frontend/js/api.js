/**
 * PathPal API 调用封装
 * 所有 API 请求统一通过此模块发出，挂载到 window.PathPalAPI
 */
(function () {
    "use strict";

    const API_BASE_URL = "http://127.0.0.1:5000/api";

    async function apiGet(path, params = {}) {
        const url = new URL(API_BASE_URL + path);
        Object.entries(params).forEach(function ([k, v]) {
            if (v !== null && v !== undefined && v !== "") {
                url.searchParams.append(k, v);
            }
        });
        const resp = await fetch(url);
        const data = await resp.json();
        if (!resp.ok) {
            throw new Error(data.error || ("HTTP " + resp.status));
        }
        return data;
    }

    async function apiPost(path, body = {}) {
        const resp = await fetch(API_BASE_URL + path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (!resp.ok) {
            throw new Error(data.error || ("HTTP " + resp.status));
        }
        return data;
    }

    function showError(containerId, error) {
        var el = document.getElementById(containerId);
        if (el) {
            el.innerHTML =
                '<div class="error-box">错误: ' +
                escapeHtml(String(error.message || error)) +
                '<br><small>请确认后端已启动: <code>python backend/app.py</code></small></div>';
        }
    }

    function showLoading(containerId, message) {
        var el = document.getElementById(containerId);
        if (el) {
            el.innerHTML = '<div class="loading-box">' + escapeHtml(message || "加载中...") + "</div>";
        }
    }

    function formatDistance(meters) {
        if (meters === null || meters === undefined) return "—";
        if (meters >= 1000) {
            return (meters / 1000).toFixed(2) + " km";
        }
        return Math.round(meters) + " m";
    }

    function formatTime(seconds) {
        if (seconds === null || seconds === undefined) return "—";
        if (seconds >= 60) {
            var min = Math.floor(seconds / 60);
            var sec = Math.round(seconds % 60);
            return min + " 分 " + sec + " 秒";
        }
        return Math.round(seconds) + " 秒";
    }

    function escapeHtml(str) {
        var div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // ---- 业务 API ----

    function loadStats() {
        return apiGet("/stats");
    }

    function loadDestinations(params) {
        return apiGet("/destinations", params);
    }

    function loadRouteNodes(destinationId) {
        return apiGet("/route/nodes", { destination_id: destinationId });
    }

    function getInternalMaps() {
        return apiGet("/internal-maps");
    }

    function getInternalMap(mapId) {
        return apiGet("/internal-maps/" + mapId);
    }

    function getMapLayers(destinationId) {
        return apiGet("/destinations/" + encodeURIComponent(destinationId) + "/map-layers");
    }

    // ---- 挂载到 window ----
    window.PathPalAPI = {
        API_BASE_URL: API_BASE_URL,
        apiGet: apiGet,
        apiPost: apiPost,
        showError: showError,
        showLoading: showLoading,
        formatDistance: formatDistance,
        formatTime: formatTime,
        escapeHtml: escapeHtml,
        loadStats: loadStats,
        loadDestinations: loadDestinations,
        loadRouteNodes: loadRouteNodes,
        getInternalMaps: getInternalMaps,
        getInternalMap: getInternalMap,
        getMapLayers: getMapLayers,
    };
})();
