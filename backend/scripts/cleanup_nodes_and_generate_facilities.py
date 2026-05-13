"""
清理节点名称 + 从 POI 节点自动生成设施数据。

1. 清理节点名称：去 _XXXXX 后缀，英→中翻译
2. 从 building/scenic_spot/gate/facility_point 等节点生成 facilities.json
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# ── 英文标签 → 中文 翻译表 ──
EN_TO_CN = {
    "cafe": "咖啡馆",
    "restaurant": "餐厅",
    "supermarket": "超市",
    "shop": "商店",
    "convenience": "便利店",
    "dormitory": "宿舍楼",
    "toilet": "卫生间",
    "library": "图书馆",
    "atm": "ATM取款机",
    "parking_entrance": "停车场入口",
    "parking": "停车场",
    "charging_station": "充电站",
    "shelter": "避雨亭",
    "telephone": "公用电话",
    "bureau_de_change": "外币兑换",
    "outdoor_seating": "户外座位",
    "yes": "商店",
    "post_box": "邮筒",
    "post_office": "邮局",
    "bank": "银行",
    "hospital": "医院",
    "clinic": "诊所",
    "pharmacy": "药房",
    "school": "学校",
    "kindergarten": "幼儿园",
    "college": "学院",
    "university": "大学",
    "police": "派出所",
    "townhall": "社区中心",
    "recycling": "回收站",
    "fountain": "喷泉",
    "drinking_water": "饮水处",
    "bench": "长椅",
    "waste_basket": "垃圾桶",
    "bicycle_parking": "自行车停放处",
    "bicycle_rental": "自行车租赁",
    "fuel": "加油站",
    "bus_station": "公交站",
    "taxi": "出租车候车点",
    "theatre": "剧院",
    "cinema": "电影院",
    "bar": "酒吧",
    "pub": "酒馆",
    "fast_food": "快餐店",
    "ice_cream": "冰淇淋店",
    "marketplace": "市场",
    "gym": "健身房",
    "swimming_pool": "游泳池",
    "stadium": "体育场",
    "sports_centre": "体育中心",
    "sports_hall": "体育馆",
    "place_of_worship": "宗教场所",
    "church": "教堂",
    "temple": "寺庙",
    "mosque": "清真寺",
    "hotel": "酒店",
    "motel": "旅馆",
    "guesthouse": "招待所",
    "hostel": "青年旅舍",
    "museum": "博物馆",
    "gallery": "画廊",
    "viewpoint": "观景点",
    "picnic_site": "野餐区",
    "playground": "游乐场",
    "dog_park": "遛狗区",
    "social_facility": "社区服务站",
    "community_centre": "社区中心",
    "vending_machine": "自动售货机",
    "vending": "自动售货机",
    "water_point": "饮水点",
    "bbq": "烧烤区",
    "shower": "淋浴间",
    "internet_cafe": "网吧",
    "nightclub": "夜店",
    "sauna": "桑拿",
    "massage": "按摩",
    "beauty": "美容院",
    "hairdresser": "理发店",
    "car_wash": "洗车处",
    "car_rental": "租车处",
    "car_repair": "汽车维修",
    "dentist": "牙科诊所",
    "doctors": "诊所",
    "veterinary": "宠物医院",
    "childcare": "托儿所",
    "nursing_home": "养老院",
    "building": "建筑",
    "office_building": "办公楼",
    "teaching_building": "教学楼",
    "classroom_building": "教学楼",
    "service": "服务中心",
    "leisure": "休闲场所",
    "amenity": "公共设施",
    "civic": "政府机构",
    "religious": "宗教场所",
    "education": "教育机构",
    "sports": "体育设施",
    "activity": "活动中心",
    "conference": "会议中心",
    "artwork": "艺术装置",
    "landmark": "地标",
    "attraction": "景点",
    "gate": "出入口",
    "entrance": "入口",
    "exit": "出口",
    "bicycle_repair_station": "自行车维修站",
    "watering_place": "取水点",
    "dive_centre": "潜水中心",
    "events_venue": "活动场地",
    "boat_rental": "划船租赁",
    "fishing": "垂钓区",
    "hunting_stand": "观鸟台",
    "bicycle_wash": "洗车点",
    "love_hotel": "情侣酒店",
    "casino": "赌场",
    "stripclub": "脱衣舞俱乐部",
    "brothel": "妓院",
    "gambling": "赌博场所",
    "adult_gaming_centre": "成人游戏厅",
    "biergarten": "啤酒花园",
    "deli": "熟食店",
    "food_court": "美食广场",
    "confectionery": "糖果店",
    "greengrocer": "蔬菜水果店",
    "bakery": "面包店",
    "butcher": "肉铺",
    "seafood": "海鲜店",
    "alcohol": "酒类商店",
    "clothes": "服装店",
    "electronics": "电器店",
    "hardware": "五金店",
    "sports_shop": "体育用品店",
    "toys": "玩具店",
    "books": "书店",
    "gift": "礼品店",
    "jewelry": "珠宝店",
    "optician": "眼镜店",
    "florist": "花店",
    "stationery": "文具店",
    "mobile_phone": "手机店",
    "computer": "电脑店",
    "mall": "商场",
    "department_store": "百货商场",
    "kiosk": "小卖部",
    "laundry": "洗衣店",
    "tailor": "裁缝店",
    "travel_agency": "旅行社",
    "tobacco": "烟草店",
    "newsagent": "报刊亭",
    "chemist": "药店",
    "cosmetics": "化妆品店",
    "pet": "宠物店",
    "antiques": "古董店",
    "bed": "床上用品店",
    "beverages": "饮料店",
    "bicycle": "自行车店",
    "boat": "船店",
    "carpet": "地毯店",
    "cheese": "奶酪店",
    "chocolate": "巧克力店",
    "coffee": "咖啡店",
    "copyshop": "复印店",
    "curtain": "窗帘店",
    "dairy": "乳品店",
    "deli": "熟食店",
    "doityourself": "五金建材店",
    "doors": "门窗店",
    "e-cigarette": "电子烟店",
    "energy": "能源店",
    "erotic": "成人用品店",
    "fabric": "布艺店",
    "fashion": "时装店",
    "fishing": "渔具店",
    "frame": "装裱店",
    "funeral_directors": "殡仪馆",
    "furniture": "家具店",
    "garden_centre": "园艺中心",
    "gas": "燃气店",
    "general": "杂货店",
    "glaziery": "玻璃店",
    "hairdresser_supply": "理发用品店",
    "hearing_aids": "助听器店",
    "herbalist": "草药店",
    "houseware": "家居用品店",
    "hunting": "狩猎用品店",
    "interior_decoration": "室内装饰店",
    "kitchen": "厨房用品店",
    "locksmith": "锁匠",
    "massage": "按摩店",
    "medical_supply": "医疗器械店",
    "military_surplus": "军品店",
    "model": "模型店",
    "motorcycle": "摩托车店",
    "music": "乐器店",
    "musical_instrument": "乐器店",
    "nutrition_supplements": "保健品店",
    "organic": "有机食品店",
    "outdoor": "户外用品店",
    "paint": "油漆店",
    "party": "派对用品店",
    "pastry": "糕点店",
    "perfumery": "香水店",
    "photo": "照相馆",
    "pottery": "陶器店",
    "printer_ink": "打印机墨水店",
    "religious": "宗教用品店",
    "rental": "租赁店",
    "scuba_diving": "潜水用品店",
    "second_hand": "二手店",
    "security": "安防设备店",
    "sewing": "缝纫用品店",
    "shoe_repair": "修鞋店",
    "shoes": "鞋店",
    "skates": "滑冰用品店",
    "ski": "滑雪用品店",
    "spices": "香料店",
    "storage_rental": "仓储租赁",
    "sunglasses": "太阳镜店",
    "swimming_pool": "泳池用品店",
    "tabletop_games": "桌游店",
    "tattoo": "纹身店",
    "ticket": "售票处",
    "tiles": "瓷砖店",
    "tobacco": "烟草店",
    "tool_hire": "工具租赁",
    "toy": "玩具店",
    "trade": "建材店",
    "trophy": "奖杯店",
    "tyres": "轮胎店",
    "vacuum_cleaner": "吸尘器店",
    "variety_store": "杂货铺",
    "video": "音像店",
    "video_games": "游戏店",
    "watches": "手表店",
    "water": "水店",
    "weapons": "武器店",
    "wholesale": "批发店",
    "wigs": "假发店",
    "window_blind": "窗帘店",
    "wine": "酒庄",
}


def clean_name(raw_name, node_type, node_subtype):
    """清理节点名称。"""
    if not raw_name:
        return raw_name

    name = raw_name.strip()

    # 1. 处理 "OSM节点-XXXXX" 格式（交叉路口，不需要具体名称）
    m = re.match(r'^OSM节点-\d+$', name)
    if m:
        return "路口"

    # 2. 去掉末尾 _XXXXXX 后缀（OSM ID）
    #    例如 "图书馆_300087" → "图书馆", "cafe_300441" → "cafe"
    name = re.sub(r'_\d{4,}$', '', name)

    # 3. 英文名翻译
    lower_name = name.lower().strip()
    # 检查是否整个名字是英文标签
    if lower_name in EN_TO_CN:
        return EN_TO_CN[lower_name]

    # 4. 如果名字为纯英文/拼音，尝试翻译
    #    例如 "Decathlon" → "迪卡侬"
    if re.match(r'^[a-zA-Z\s]+$', name):
        lower = name.lower().strip()
        if lower in EN_TO_CN:
            return EN_TO_CN[lower]
        # 保留原名（可能是品牌名如 Decathlon）
        return name

    return name


def node_to_facility_category(node_type, node_subtype):
    """将节点类型/子类型映射为设施类别。"""
    subtype = (node_subtype or "").lower()

    # 直接映射
    subtype_cat = {
        "toilet": "卫生间",
        "restaurant": "餐饮",
        "cafe": "餐饮",
        "canteen": "餐饮",
        "supermarket": "商店",
        "shop": "商店",
        "convenience": "商店",
        "dormitory": "宿舍",
        "library": "图书馆",
        "office": "办公楼",
        "parking": "停车场",
        "clinic": "医疗",
        "hospital": "医疗",
        "pharmacy": "医疗",
        "sports": "体育设施",
        "religious": "宗教场所",
        "atm": "服务",
        "service": "服务",
        "ticket": "售票处",
        "education": "教育机构",
        "civic": "公共设施",
        "leisure": "休闲场所",
        "gate": "出入口",
        "entrance": "出入口",
        "attraction": "景点",
        "artwork": "景点",
        "landmark": "景点",
    }

    if subtype in subtype_cat:
        return subtype_cat[subtype]

    # 按节点类型回退
    type_cat = {
        "scenic_spot": "景点",
        "gate": "出入口",
        "building": "建筑",
        "canteen": "餐饮",
        "library": "图书馆",
        "dormitory": "宿舍",
        "teaching_building": "教学楼",
        "office_building": "办公楼",
        "classroom_building": "教学楼",
        "facility_point": "公共设施",
    }

    if node_type in type_cat:
        return type_cat[node_type]

    return "其他"


# POI 类型的节点（应生成设施）
FACILITY_NODE_TYPES = {
    "building", "scenic_spot", "gate", "facility_point",
    "canteen", "library", "dormitory", "teaching_building",
    "office_building", "classroom_building",
}


def main():
    print("=" * 60)
    print("1. 清理节点名称")
    print("=" * 60)

    with open(DATA_DIR / "internal_nodes.json", "r", encoding="utf-8") as f:
        nodes = json.load(f)

    rename_count = 0
    for n in nodes:
        old_name = n.get("name", "")
        new_name = clean_name(old_name, n.get("type"), n.get("subtype"))
        if old_name != new_name:
            n["name"] = new_name
            rename_count += 1

    print(f"  重命名: {rename_count} / {len(nodes)} 个节点")

    # 检查重名情况
    name_counts = Counter(n.get("name") for n in nodes)
    duplicates = {k: v for k, v in name_counts.items() if v > 1 and k != "路口"}
    print(f"  重名名称数: {len(duplicates)}")

    # 对重名的非路口节点添加区分后缀
    dup_counters = defaultdict(int)
    for n in nodes:
        name = n.get("name", "")
        if name == "路口" or name not in duplicates:
            continue
        dup_counters[name] += 1
        if dup_counters[name] > 1:
            n["name"] = f"{name}({dup_counters[name]})"

    # 重新计数重名
    name_counts2 = Counter(n.get("name") for n in nodes)
    duplicates2 = {k: v for k, v in name_counts2.items() if v > 1 and k != "路口"}
    print(f"  去重后重名名称数: {len(duplicates2)}")

    with open(DATA_DIR / "internal_nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    print("  已保存 internal_nodes.json")

    # ─────────────────────────────────────────────
    print()
    print("=" * 60)
    print("2. 从 POI 节点生成设施数据")
    print("=" * 60)

    # 加载现有设施
    with open(DATA_DIR / "facilities.json", "r", encoding="utf-8") as f:
        existing_facs = json.load(f)

    existing_linked = set()
    existing_ids = set()
    for f_item in existing_facs:
        existing_ids.add(f_item["id"])
        lid = f_item.get("linked_node_id")
        if lid:
            existing_linked.add(lid)

    # 为每个 POI 节点生成设施
    new_facs = []
    count_by_cat = Counter()
    count_by_map = Counter()

    for n in nodes:
        ntype = n.get("type", "")
        if ntype not in FACILITY_NODE_TYPES:
            continue

        # 跳过已有关联的
        if n["id"] in existing_linked:
            continue

        cat = node_to_facility_category(ntype, n.get("subtype"))
        map_id = n.get("map_id", "")

        # 只为真实地图生成设施（模拟地图已有手写设施）
        if map_id not in ("MAP_BUPT_REAL", "MAP_SCENIC_REAL"):
            continue

        # 跳过无名称的节点
        name = n.get("name", "")
        if not name or name == "路口":
            continue

        fac_id = f"FAC_AUTO_{n['id']}"
        fac = {
            "id": fac_id,
            "name": name,
            "category": cat,
            "map_id": map_id,
            "linked_node_id": n["id"],
            "latitude": n.get("latitude", 0),
            "longitude": n.get("longitude", 0),
            "description": f"{name}（{cat}）",
            "node_type": ntype,
            "node_subtype": n.get("subtype", ""),
        }
        new_facs.append(fac)
        count_by_cat[cat] += 1
        count_by_map[map_id] += 1

    print(f"  新增设施: {len(new_facs)}")
    print(f"  按地图: {dict(count_by_map)}")
    print(f"  按类别: {dict(count_by_cat)}")

    # 合并
    all_facs = existing_facs + new_facs
    with open(DATA_DIR / "facilities.json", "w", encoding="utf-8") as f:
        json.dump(all_facs, f, ensure_ascii=False, indent=2)
    print(f"  总设施数: {len(all_facs)}")
    print("  已保存 facilities.json")

    # ─────────────────────────────────────────────
    print()
    print("=" * 60)
    print("3. 更新节点类型标签（标准化）")
    print("=" * 60)

    # 统计改名后的样本
    sample_buildings = [n for n in nodes
                        if n.get("type") == "building"
                        and n.get("map_id") in ("MAP_BUPT_REAL", "MAP_SCENIC_REAL")][:20]
    print("  建筑名称样本:")
    for n in sample_buildings:
        print(f"    {n['id']}: '{n['name']}' subtype={n.get('subtype','')}")

    print()
    print("完成！")


if __name__ == "__main__":
    main()
