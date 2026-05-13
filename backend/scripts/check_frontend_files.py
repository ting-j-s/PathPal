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
