"""
PathPal E2E Smoke Check
端到端自动化检查脚本 —— 通过 HTTP 请求验证所有 API 端点。

用法：
  1. 先启动后端： cd backend && python app.py
  2. 再运行本脚本： python backend/scripts/e2e_smoke_check.py

如果后端未启动，脚本会输出清晰提示并退出。
"""

import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"
API = f"{BASE_URL}/api"

passed = 0
failed = 0
warnings = 0
errors = []


def _req(url, params=None, body=None, method="GET"):
    """发送 HTTP 请求，返回 (status, data)。"""
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    if body:
        data_bytes = json.dumps(body).encode("utf-8")
        req.add_header("Content-Length", str(len(data_bytes)))
    else:
        data_bytes = None
    try:
        with urllib.request.urlopen(req, data=data_bytes, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        try:
            body_data = json.loads(raw)
        except Exception:
            body_data = {"error": raw}
        return e.code, body_data
    except urllib.error.URLError as e:
        return 0, {"_error": str(e.reason)}


def ok(msg):
    global passed
    passed += 1
    print(f"  [PASS] {msg}")


def fail(msg):
    global failed
    failed += 1
    print(f"  [FAIL] {msg}")


def warn(msg):
    global warnings
    warnings += 1
    print(f"  [WARN] {msg}")


def check(condition, ok_msg, fail_msg):
    if condition:
        ok(ok_msg)
    else:
        fail(fail_msg)


# ============================================================
# 0. Backend connectivity
# ============================================================
print("PathPal E2E Smoke Check")
print("=" * 50)

status, health = _req(f"{API}/health")
if status == 0:
    print()
    print("ERROR: Backend is not running at", BASE_URL)
    print("Please start it first:")
    print("  cd backend && python app.py")
    print()
    sys.exit(2)

check(status == 200, "Backend health: OK", f"Backend health: got status {status}")
if status != 200:
    print("Backend returned unexpected status, stopping.")
    sys.exit(1)

# ============================================================
# 1. Stats
# ============================================================
status, stats = _req(f"{API}/stats")
check(status == 200 and isinstance(stats, dict) and "destinations" in stats,
      "Stats: OK", f"Stats: FAILED (status={status}, keys={list(stats.keys()) if isinstance(stats, dict) else 'N/A'})")
if status == 200 and isinstance(stats, dict):
    for key in ["destinations", "internal_maps", "internal_nodes", "internal_edges",
                "facilities", "facility_categories", "users"]:
        if key not in stats:
            warn(f"Stats missing key: {key}")
    print(f"         Data: {stats.get('destinations', '?')} destinations, "
          f"{stats.get('internal_edges', '?')} edges, "
          f"{stats.get('facilities', '?')} facilities, "
          f"{stats.get('users', '?')} users")

def _unwrap(data):
    """兼容新旧 API 格式：若返回 dict 包裹的 {results: [...]}，提取 results 列表。"""
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data

# ============================================================
# 2. Recommendations
# ============================================================
# 2a. Hot top-10
status, hot = _req(f"{API}/recommendations/hot", {"k": 10})
hot_results = _unwrap(hot) if status == 200 else []
check(status == 200 and isinstance(hot_results, list) and len(hot_results) <= 10,
      f"Recommendations hot (got {len(hot_results) if isinstance(hot_results, list) else 0}): OK",
      f"Recommendations hot: FAILED (status={status})")

# 2b. Rating top-10
status, rating = _req(f"{API}/recommendations/rating", {"k": 10})
rating_results = _unwrap(rating) if status == 200 else []
check(status == 200 and isinstance(rating_results, list) and len(rating_results) <= 10,
      f"Recommendations rating (got {len(rating_results) if isinstance(rating_results, list) else 0}): OK",
      f"Recommendations rating: FAILED (status={status})")

# 2c. Interest recommendations
status, interest = _req(f"{API}/recommendations/interest", {"user_id": "USER_001", "k": 10})
interest_results = _unwrap(interest) if status == 200 else []
check(status == 200 and isinstance(interest_results, list) and len(interest_results) <= 10,
      f"Recommendations interest USER_001 (got {len(interest_results) if isinstance(interest_results, list) else 0}): OK",
      f"Recommendations interest: FAILED (status={status})")
if status == 200 and isinstance(interest_results, list) and len(interest_results) > 0:
    has_interest_score = any("interest_score" in item for item in interest_results)
    check(has_interest_score,
          "Interest results contain interest_score: OK",
          "Interest results missing interest_score: FAILED")

# 2d. Keyword search
status, search = _req(f"{API}/destinations/search", {"keyword": "北京"})
search_results = _unwrap(search) if status == 200 else []
check(status == 200 and isinstance(search_results, list),
      f"Search '北京' (got {len(search_results) if isinstance(search_results, list) else 0}): OK",
      f"Search '北京': FAILED (status={status})")

# 2e. List destinations
status, dest_list = _req(f"{API}/destinations", {"limit": 5})
dest_results = _unwrap(dest_list) if status == 200 else []
check(status == 200 and isinstance(dest_results, list) and len(dest_results) <= 5,
      f"List destinations limit=5 (got {len(dest_results) if isinstance(dest_results, list) else 0}): OK",
      f"List destinations: FAILED (status={status})")

# 2f. Destination detail
if isinstance(dest_results, list) and len(dest_results) > 0:
    first_id = dest_results[0].get("id")
    status, detail = _req(f"{API}/destinations/{first_id}")
    # 兼容新旧格式：新版 API 将详情包裹在 result 字段中
    detail_data = detail.get("result", detail) if isinstance(detail, dict) else detail
    check(status == 200 and isinstance(detail_data, dict) and detail_data.get("id") == first_id,
          f"Destination detail ({first_id}): OK",
          f"Destination detail: FAILED (status={status})")

# ============================================================
# 3. Route Planning
# ============================================================

# Find a campus and an attraction from destinations
all_status, all_data = _req(f"{API}/destinations", {"limit": 250})
all_dests_list = _unwrap(all_data) if all_status == 200 else []
campus_dest = None
attraction_dest = None
if all_status == 200 and isinstance(all_dests_list, list):
    for d in all_dests_list:
        if d.get("type") == "campus" and campus_dest is None:
            campus_dest = d
        if d.get("type") == "attraction" and attraction_dest is None:
            attraction_dest = d
        if campus_dest and attraction_dest:
            break

if campus_dest is None:
    fail("No campus destination found for route tests")
if attraction_dest is None:
    fail("No attraction destination found for route tests")

# --- Campus route tests ---
if campus_dest:
    campus_id = campus_dest["id"]
    campus_name = campus_dest.get("name", campus_id)

    # Get nodes
    status, cnodes = _req(f"{API}/route/nodes", {"destination_id": campus_id})
    cnodes_list = cnodes.get("nodes", cnodes) if isinstance(cnodes, dict) else cnodes if isinstance(cnodes, list) else []
    real_nodes = [n for n in cnodes_list
                  if n.get("latitude", 0) > 0.01] if status == 200 else []
    check(status == 200 and len(real_nodes) >= 2,
          f"Campus '{campus_name}' nodes (real={len(real_nodes)}): OK",
          f"Campus nodes: FAILED (status={status}, nodes={len(real_nodes)})")

    if len(real_nodes) >= 2:
        start = real_nodes[0]["id"]
        end = real_nodes[-1]["id"]

        # Shortest distance
        status, sd = _req(f"{API}/route/shortest-distance",
                          {"destination_id": campus_id, "start": start, "end": end})
        has_path = status == 200 and isinstance(sd, dict) and "path" in sd
        check(has_path,
              f"Campus shortest distance ({start}->{end}): OK",
              f"Campus shortest distance: FAILED (status={status})")
        if has_path:
            has_segments = "segments" in sd
            check(has_segments,
                  "Campus route has segments detail: OK",
                  "Campus route missing segments: FAILED")

        # Shortest time (walk)
        status, st = _req(f"{API}/route/shortest-time",
                          {"destination_id": campus_id, "start": start, "end": end, "transport": "walk"})
        has_path2 = status == 200 and isinstance(st, dict) and "path" in st
        check(has_path2,
              f"Campus shortest time walk ({start}->{end}): OK",
              f"Campus shortest time walk: FAILED (status={status})")

        # Mixed time
        status, mt = _req(f"{API}/route/mixed-time",
                          {"destination_id": campus_id, "start": start, "end": end})
        has_path3 = status == 200 and isinstance(mt, dict) and "path" in mt
        check(has_path3,
              f"Campus mixed time ({start}->{end}): OK",
              f"Campus mixed time: FAILED (status={status})")

        # Bike route
        status, br = _req(f"{API}/route/shortest-time",
                          {"destination_id": campus_id, "start": start, "end": end, "transport": "bike"})
        has_path4 = status == 200 and isinstance(br, dict) and "path" in br
        check(has_path4,
              f"Campus bike route ({start}->{end}): OK",
              f"Campus bike route: FAILED (status={status})")

        # Campus sightseeing_car should be rejected
        status, sc = _req(f"{API}/route/shortest-time",
                          {"destination_id": campus_id, "start": start, "end": end, "transport": "sightseeing_car"})
        rejected = status == 400 or (status == 200 and isinstance(sc, dict) and "error" in sc)
        check(rejected,
              f"Campus sightseeing_car rejected (status={status}): OK",
              f"Campus sightseeing_car NOT rejected: FAILED (status={status})")

        # Multi-point route
        if len(real_nodes) >= 3:
            mid_node = real_nodes[len(real_nodes) // 2]["id"]
            status, mp = _req(f"{API}/route/multi-point",
                              body={"destination_id": campus_id, "start": start,
                                    "targets": [mid_node], "strategy": "shortest_distance"},
                              method="POST")
            has_mp = status == 200 and isinstance(mp, dict) and "path" in mp
            check(has_mp,
                  f"Campus multi-point route ({start}->{mid_node}->{end}): OK",
                  f"Campus multi-point route: FAILED (status={status})")

# --- Attraction route tests ---
if attraction_dest:
    attr_id = attraction_dest["id"]
    attr_name = attraction_dest.get("name", attr_id)

    status, anodes = _req(f"{API}/route/nodes", {"destination_id": attr_id})
    anodes_list = anodes.get("nodes", anodes) if isinstance(anodes, dict) else anodes if isinstance(anodes, list) else []
    real_anodes = [n for n in anodes_list
                   if n.get("latitude", 0) > 0.01] if status == 200 else []
    check(status == 200 and len(real_anodes) >= 2,
          f"Attraction '{attr_name}' nodes (real={len(real_anodes)}): OK",
          f"Attraction nodes: FAILED (status={status})")

    if len(real_anodes) >= 2:
        a_start = real_anodes[0]["id"]
        a_end = real_anodes[-1]["id"]

        # Sightseeing car route
        status, scr = _req(f"{API}/route/shortest-time",
                           {"destination_id": attr_id, "start": a_start, "end": a_end,
                            "transport": "sightseeing_car"})
        if status == 200 and isinstance(scr, dict) and "path" in scr:
            ok(f"Attraction sightseeing_car route: OK")
        elif status == 400 and isinstance(scr, dict) and "error" in scr:
            warn(f"Attraction sightseeing_car route rejected ({scr.get('error')}) — may be expected for some map types")
        else:
            warn(f"Attraction sightseeing_car route: unexpected status {status}")

        # Attraction bike should be rejected
        status, br2 = _req(f"{API}/route/shortest-time",
                           {"destination_id": attr_id, "start": a_start, "end": a_end, "transport": "bike"})
        rejected2 = status == 400 or (status == 200 and isinstance(br2, dict) and "error" in br2)
        check(rejected2,
              f"Attraction bike rejected (status={status}): OK",
              f"Attraction bike NOT rejected: FAILED (status={status})")

        # Mixed for attraction
        status, mt2 = _req(f"{API}/route/mixed-time",
                           {"destination_id": attr_id, "start": a_start, "end": a_end})
        has_mt2 = status == 200 and isinstance(mt2, dict) and "path" in mt2
        check(has_mt2,
              f"Attraction mixed time ({a_start}->{a_end}): OK",
              f"Attraction mixed time: FAILED (status={status})")

# ============================================================
# 4. Nearby
# ============================================================
if campus_dest and len(real_nodes) >= 1:
    nid = real_nodes[0]["id"]

    # All nearby
    status, nearby = _req(f"{API}/nearby",
                          {"destination_id": campus_id, "node_id": nid})
    check(status == 200 and isinstance(nearby, (dict, list)),
          f"Nearby all (node={nid}): OK",
          f"Nearby all: FAILED (status={status})")

    near_items = nearby if isinstance(nearby, list) else nearby.get("facilities", nearby.get("results", []))
    if isinstance(near_items, list) and len(near_items) > 0:
        # Check road_distance sorting
        distances = [item.get("road_distance", float("inf")) for item in near_items]
        sorted_ok = all(distances[i] <= distances[i + 1] for i in range(len(distances) - 1))
        check(sorted_ok,
              "Nearby results sorted by road_distance ascending: OK",
              "Nearby results NOT sorted by road_distance: FAILED")

    # Note check
    if isinstance(nearby, dict):
        note = nearby.get("note", "")
        has_road_note = "道路距离" in note or "道路" in note or "road" in note.lower()
        if not has_road_note:
            warn("Nearby note may not mention road-distance sorting")

    # Categories
    status, cats = _req(f"{API}/nearby/categories", {"destination_id": campus_id})
    cat_list = cats if isinstance(cats, list) else cats.get("categories", [])
    check(status == 200 and isinstance(cat_list, list) and len(cat_list) > 0,
          f"Nearby categories (got {len(cat_list) if isinstance(cat_list, list) else 0}): OK",
          f"Nearby categories: FAILED (status={status})")

    # By category
    if isinstance(cat_list, list) and len(cat_list) > 0:
        test_cat = cat_list[0]
        status, cat_fac = _req(f"{API}/nearby/category",
                               {"destination_id": campus_id, "node_id": nid, "category": test_cat})
        check(status == 200,
              f"Nearby by category '{test_cat}': OK",
              f"Nearby by category '{test_cat}': FAILED (status={status})")

    # Keyword search
    status, kw_fac = _req(f"{API}/nearby/search",
                          {"destination_id": campus_id, "node_id": nid, "keyword": "超市"})
    check(status == 200,
          f"Nearby search '超市': OK",
          f"Nearby search '超市': FAILED (status={status})")

# ============================================================
# 5. Indoor Navigation (Demo)
# ============================================================
status, buildings = _req(f"{API}/indoor/buildings")
bld_list = buildings if isinstance(buildings, list) else buildings.get("buildings", [])
check(status == 200 and isinstance(bld_list, list),
      f"Indoor buildings (got {len(bld_list) if isinstance(bld_list, list) else 0}): OK",
      f"Indoor buildings: FAILED (status={status})")

if isinstance(bld_list, list) and len(bld_list) > 0:
    bid = bld_list[0] if isinstance(bld_list[0], str) else (bld_list[0].get("building_id") or bld_list[0].get("id", ""))
    if bid:
        # Get first building's nodes from data to pick start/end
        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        indoor_file = data_dir / "indoor_graphs.json"
        try:
            with open(indoor_file, "r", encoding="utf-8") as f:
                indoor_data = json.load(f)
            indoor_maps = indoor_data if isinstance(indoor_data, list) else indoor_data.get("indoor_maps", [])
            if indoor_maps:
                bld = indoor_maps[0] if isinstance(indoor_maps[0], dict) else {}
                bld_nodes = bld.get("nodes", [])
                if len(bld_nodes) >= 2:
                    i_start = bld_nodes[0].get("id", bld_nodes[0]) if isinstance(bld_nodes[0], dict) else bld_nodes[0]
                    i_end = bld_nodes[-1].get("id", bld_nodes[-1]) if isinstance(bld_nodes[-1], dict) else bld_nodes[-1]
                    status, iroute = _req(f"{API}/indoor/route",
                                          {"building_id": bid, "start": i_start, "end": i_end})
                    check(status == 200 and isinstance(iroute, dict) and ("path" in iroute or "steps" in iroute),
                          f"Indoor route ({i_start}->{i_end}): OK",
                          f"Indoor route: FAILED (status={status})")
                else:
                    warn(f"Indoor building '{bid}' has < 2 nodes, skipping route test")
        except Exception as e:
            warn(f"Could not load indoor data for route test: {e}")

# ============================================================
# Summary
# ============================================================
print()
total = passed + failed
print(f"Summary: {passed} passed, {failed} failed, {warnings} warnings")

if failed > 0:
    print()
    print("Some checks FAILED.")
    sys.exit(1)
else:
    print("All smoke checks passed.")
    sys.exit(0)
