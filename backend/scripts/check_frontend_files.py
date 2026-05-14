"""
Frontend files check — 检查必要前端文件是否完整、引用是否正确、是否包含关键算法说明文字。
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

REQUIRED_HTML = [
    "index.html",
    "recommendation.html",
    "route_planning.html",
    "nearby.html",
    "indoor_navigation.html",
]

REQUIRED_CSS = [
    "css/style.css",
]

REQUIRED_JS = [
    "js/api.js",
    "js/map.js",
    "js/index.js",
    "js/recommendation.js",
    "js/route_planning.js",
    "js/nearby.js",
    "js/indoor_navigation.js",
]

# HTML -> expected JS references (at least one match per group)
HTML_JS_REFS = {
    "index.html": ["js/api.js", "js/index.js"],
    "recommendation.html": ["js/api.js", "js/recommendation.js"],
    "route_planning.html": ["js/api.js", "js/map.js", "js/route_planning.js"],
    "nearby.html": ["js/api.js", "js/map.js", "js/nearby.js"],
    "indoor_navigation.html": ["js/api.js", "js/indoor_navigation.js"],
}

# 关键算法文字（至少一个匹配即通过）
ALGO_KEYWORDS = [
    "Dijkstra",
    "Top-K",
    "道路距离",
    # 英文时间公式
    "distance / (congestion",
    "real_speed",
    "拥挤度",
    "time = distance",
]

# 地图真实性修正相关文字
MAP_AUTH_KEYWORDS = [
    "show_tile",
    "抽象内部地图模板",
    "不叠加真实地图瓦片",
    "真实 OSM 内部道路图",
    "map-source-note",
]

# 地图分层管理关键字
MAP_LAYER_KEYWORDS = [
    "baseLayer",
    "routeLayer",
    "markerLayer",
    "drawBaseNetwork",
    "clearBaseLayers",
    "clearRouteLayers",
]

# map-layers API 调用关键字
MAP_LAYERS_API_KEYWORDS = [
    "map-layers",
    "getMapLayers",
]

# 不应该出现的业务页面引用
FORBIDDEN_KEYWORDS = [
    "diary",
    "food",
    "美食",
    "日记",
    "login",
    "register",
    "登录",
    "注册",
]

errors = []


def check_file_exists(rel_path):
    """检查文件是否存在。"""
    fpath = FRONTEND_DIR / rel_path
    if not fpath.is_file():
        errors.append(f"MISSING: frontend/{rel_path}")
        return False
    return True


def check_js_refs(html_file, expected_js_list):
    """检查 HTML 文件是否引用了预期的 JS 文件。"""
    fpath = FRONTEND_DIR / html_file
    if not fpath.is_file():
        return
    content = fpath.read_text(encoding="utf-8")
    for js in expected_js_list:
        if js not in content:
            errors.append(f"MISSING JS REF: {html_file} 未引用 {js}")


def check_algo_text():
    """检查所有 HTML 页面是否包含关键算法说明文字。"""
    all_text = ""
    for html_file in REQUIRED_HTML:
        fpath = FRONTEND_DIR / html_file
        if fpath.is_file():
            all_text += fpath.read_text(encoding="utf-8")

    for kw in ALGO_KEYWORDS:
        if kw.lower() not in all_text.lower():
            errors.append(f"MISSING ALGO KEYWORD: 所有页面未包含 '{kw}'")


def check_forbidden():
    """检查不应出现的关键词（不在"不做"上下文中）。"""
    for html_file in REQUIRED_HTML:
        fpath = FRONTEND_DIR / html_file
        if not fpath.is_file():
            continue
        lines = fpath.read_text(encoding="utf-8").split("\n")
        for kw in FORBIDDEN_KEYWORDS:
            kw_lower = kw.lower()
            for line in lines:
                line_lower = line.lower()
                if kw_lower in line_lower:
                    # 允许在"明确不做"/"不要"上下文中提及
                    if "不做" in line_lower or "不要" in line_lower:
                        continue
                    errors.append(f"FORBIDDEN: {html_file} 包含 '{kw}'")
                    break


def check_leaflet():
    """检查路线规划和场所查询页面是否包含 Leaflet 引用。"""
    for html_file in ["route_planning.html", "nearby.html"]:
        fpath = FRONTEND_DIR / html_file
        if not fpath.is_file():
            continue
        content = fpath.read_text(encoding="utf-8")
        if "leaflet" not in content.lower():
            errors.append(f"MISSING LEAFLET: {html_file} 未包含 Leaflet 引用")


def check_map_authenticity():
    """检查前端页面是否包含地图真实性相关逻辑。"""
    all_text = ""
    for html_file in ["route_planning.html", "nearby.html"]:
        fpath = FRONTEND_DIR / html_file
        if fpath.is_file():
            all_text += fpath.read_text(encoding="utf-8")
    for js_file in ["js/route_planning.js", "js/nearby.js"]:
        fpath = FRONTEND_DIR / js_file
        if fpath.is_file():
            all_text += fpath.read_text(encoding="utf-8")

    # 至少有一个 match
    found = False
    for kw in MAP_AUTH_KEYWORDS:
        if kw.lower() in all_text.lower():
            found = True
            break
    if not found:
        errors.append(f"MISSING MAP AUTH: 页面/JS 未包含 show_tile 或地图真实性提示逻辑")


def check_map_layer_management():
    """检查 map.js 是否包含分层管理函数。"""
    fpath = FRONTEND_DIR / "js/map.js"
    if not fpath.is_file():
        errors.append("MISSING: frontend/js/map.js")
        return
    content = fpath.read_text(encoding="utf-8")
    for kw in MAP_LAYER_KEYWORDS:
        if kw not in content:
            errors.append(f"MISSING MAP LAYER: map.js 未包含 '{kw}'")


def check_map_layers_api():
    """检查是否使用了 map-layers API。"""
    all_text = ""
    for js_file in ["js/api.js", "js/route_planning.js", "js/nearby.js"]:
        fpath = FRONTEND_DIR / js_file
        if fpath.is_file():
            all_text += fpath.read_text(encoding="utf-8")
    for kw in MAP_LAYERS_API_KEYWORDS:
        if kw not in all_text:
            errors.append(f"MISSING MAP LAYERS API: 前端 JS 未包含 '{kw}'")


# 室内导航页面关键字
INDOOR_HTML_KEYWORDS = [
    "indoor",
    "室内",
    "svg",
    "楼层",
]

INDOOR_ALGO_KEYWORDS = [
    "Dijkstra",
    "最短距离",
    "邻接表",
    "室内图",
    "电梯",
    "distance",
]

INDOOR_JS_FUNCTIONS = [
    "loadBuildings",
    "planIndoorRoute",
    "renderFloorGraphs",
    "svg",
]


def check_indoor_navigation():
    """检查室内导航页面的完整性。"""
    # HTML 检查
    html_path = FRONTEND_DIR / "indoor_navigation.html"
    if not html_path.is_file():
        errors.append("MISSING: frontend/indoor_navigation.html")
        return
    html_content = html_path.read_text(encoding="utf-8").lower()

    for kw in INDOOR_HTML_KEYWORDS:
        if kw.lower() not in html_content:
            errors.append(f"INDOOR HTML: indoor_navigation.html 未包含 '{kw}'")

    for kw in INDOOR_ALGO_KEYWORDS:
        if kw.lower() not in html_content:
            errors.append(f"INDOOR ALGO: indoor_navigation.html 未包含算法说明 '{kw}'")

    # JS 检查
    js_path = FRONTEND_DIR / "js/indoor_navigation.js"
    if not js_path.is_file():
        errors.append("MISSING: frontend/js/indoor_navigation.js")
        return
    js_content = js_path.read_text(encoding="utf-8")

    for fn in INDOOR_JS_FUNCTIONS:
        if fn not in js_content:
            errors.append(f"INDOOR JS: indoor_navigation.js 未包含 '{fn}'")


def check_route_geometry():
    """检查前端是否正确使用 route_geometry。"""
    all_text = ""
    for js_file in ["js/map.js", "js/route_planning.js", "js/nearby.js"]:
        fpath = FRONTEND_DIR / js_file
        if fpath.is_file():
            all_text += fpath.read_text(encoding="utf-8")
    # map.js 中 drawRouteWithSegments 应使用 geometry
    if "seg.geometry" not in all_text:
        errors.append("ROUTE GEOMETRY: map.js drawRouteWithSegments 未优先使用 segment.geometry")
    # route_planning.js 应使用 route_geometry
    if "route_geometry" not in all_text:
        errors.append("ROUTE GEOMETRY: route_planning.js 未使用 route_geometry")
    # nearby.js 应使用 route_geometry
    if "route_geometry" not in all_text:
        errors.append("ROUTE GEOMETRY: nearby.js 未使用 route_geometry")


def main():
    print("Frontend Files Check")
    print("=" * 40)

    # 1. 检查 HTML 文件
    for html_file in REQUIRED_HTML:
        if check_file_exists(html_file):
            print(f"  {html_file} OK")

    # 2. 检查 CSS
    for css_file in REQUIRED_CSS:
        if check_file_exists(css_file):
            print(f"  {css_file} OK")

    # 3. 检查 JS 文件
    for js_file in REQUIRED_JS:
        if check_file_exists(js_file):
            print(f"  {js_file} OK")

    # 4. 检查 JS 引用
    all_html_ok = all((FRONTEND_DIR / h).is_file() for h in REQUIRED_HTML)
    all_js_ok = all((FRONTEND_DIR / j).is_file() for j in REQUIRED_JS)
    if all_html_ok and all_js_ok:
        for html_file, js_list in HTML_JS_REFS.items():
            check_js_refs(html_file, js_list)
        if not any("MISSING JS REF" in e for e in errors):
            print("  JS references OK")

    # 5. 检查 Leaflet
    check_leaflet()
    if not any("LEAFLET" in e for e in errors):
        print("  Leaflet references OK")

    # 5.5 检查地图真实性逻辑
    check_map_authenticity()
    if not any("MAP AUTH" in e for e in errors):
        print("  Map authenticity logic OK")

    # 5.6 检查地图分层管理
    check_map_layer_management()
    if not any("MAP LAYER" in e for e in errors):
        print("  Map layer management OK")

    # 5.7 检查 map-layers API 使用
    check_map_layers_api()
    if not any("MAP LAYERS API" in e for e in errors):
        print("  Map layers API usage OK")

    # 5.8 检查 route_geometry 使用
    check_route_geometry()
    if not any("ROUTE GEOMETRY" in e for e in errors):
        print("  Route geometry usage OK")

    # 5.9 检查室内导航页面
    check_indoor_navigation()
    if not any("INDOOR" in e for e in errors):
        print("  Indoor navigation page OK")

    # 6. 检查算法说明文字
    check_algo_text()
    if not any("ALGO KEYWORD" in e for e in errors):
        print("  Algorithm explanation text OK")

    # 7. 检查禁止内容
    check_forbidden()
    if not any("FORBIDDEN" in e for e in errors):
        print("  No forbidden content OK")

    print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
        print()
        print("Some checks FAILED.")
        sys.exit(1)
    else:
        print("All frontend checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
