"""
第二遍清理：翻译剩余纯英文节点名 + 统一设施分类为中文。
"""
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

# 具体翻译映射（从分析中提取的纯英文名）
SPECIFIC_TRANSLATIONS = {
    "7-Eleven": "7-11便利店",
    "APM Beijing Puhua International Hospital": "北京普华国际医院",
    "Bondi Cafe": "邦迪咖啡馆",
    "Capital M": "Capital M餐厅",
    "Chengfu Tiantian Supermart": "成府天天超市",
    "Coffee Bene": "Coffee Bene咖啡",
    "Decathlon": "迪卡侬",
    "Golden Oasis": "金色绿洲",
    "Grid Coffee": "Grid Coffee咖啡",
    "HongYunLou Restaurant": "鸿运楼餐厅",
    "Isaac Newton": "艾萨克·牛顿像",
    "King": "King餐厅",
    "LINES": "LINES",
    "Lejia Vegetable Market": "乐家菜市场",
    "Lost Heaven": "迷失天堂",
    "Luka Suyouji Supermart": "卢卡苏优集超市",
    "M Stand": "M Stand咖啡",
    "Nanmen Snacks": "南门小吃",
    "New World Taihua Serviced Apartment": "新世界太华公寓",
    "Old Beijing": "老北京",
    "Old Hong Kong": "老香港",
    "PAGEONE": "PageOne书店",
    "Pekin apartamento": "北京公寓",
    "Pick up": "取货点",
    "Pinwei Wenxiang Tea House": "品味闻香茶楼",
    "Shitong Tianxiang Zhudu Baoji": "食通天香煮肚包鸡",
    "Spoonful of sugar": "一勺糖甜品",
    "The Reds": "红人馆",
    "Voyage Coffee": "Voyage咖啡",
    "Western Restaurant": "西餐厅",
    "Xinleilei Store": "新蕾蕾商店",
    "Yishu Zaoxing": "艺术造型",
    "Yitel": "怡莱酒店",
    "book design shop": "书籍设计店",
    "buudal 2": "布达尔酒店",
    "clock": "钟楼",
    "government": "政府机构",
    "gymnasium": "体育馆",
    "information": "信息中心",
    "office": "办公楼",
    "pitch": "球场",
    "tea": "茶庄",
    "telecommunication": "通信站",
    "toilets": "卫生间",
}

# 设施分类 英→中
FACILITY_CAT_TRANSLATION = {
    "toilet": "卫生间",
    "cafe": "餐饮",
    "shop": "商店",
    "restaurant": "餐饮",
    "service_desk": "服务",
    "office": "办公楼",
    "supermarket": "商店",
    "dormitory": "宿舍",
    "canteen": "餐饮",
    "library": "图书馆",
    "classroom": "教学楼",
    "clinic": "医疗",
    "service": "服务",
    "ticket": "售票处",
}


def main():
    # ── 1. 翻译剩余英文节点名 ──
    with open(DATA_DIR / "internal_nodes.json", "r", encoding="utf-8") as f:
        nodes = json.load(f)

    trans_count = 0
    for n in nodes:
        name = n.get("name", "")
        if not name:
            continue
        # 检查纯英文
        if re.match(r'^[a-zA-Z0-9\s\(\)\'\-\.]+$', name):
            # 先去掉末尾的 (N) 后缀（由去重逻辑添加）
            base = re.sub(r'\(\d+\)$', '', name).strip()
            suffix_match = re.search(r'(\(\d+\))$', name)

            # 尝试精确匹配
            if name in SPECIFIC_TRANSLATIONS:
                n["name"] = SPECIFIC_TRANSLATIONS[name]
                trans_count += 1
            elif base in SPECIFIC_TRANSLATIONS:
                cn = SPECIFIC_TRANSLATIONS[base]
                if suffix_match:
                    cn += suffix_match.group(1)
                n["name"] = cn
                trans_count += 1
            else:
                # 尝试逐词翻译
                print(f"  UNTRANSLATED: {n['id']}: '{name}' type={n.get('type')}")

    print(f"Translated English names: {trans_count}")
    print()

    # 保存
    with open(DATA_DIR / "internal_nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    print("Saved internal_nodes.json")

    # ── 2. 翻译设施分类 ──
    with open(DATA_DIR / "facilities.json", "r", encoding="utf-8") as f:
        facs = json.load(f)

    cat_changes = 0
    for f_item in facs:
        old_cat = f_item.get("category", "")
        if old_cat in FACILITY_CAT_TRANSLATION:
            f_item["category"] = FACILITY_CAT_TRANSLATION[old_cat]
            cat_changes += 1

    print(f"Translated facility categories: {cat_changes}")

    with open(DATA_DIR / "facilities.json", "w", encoding="utf-8") as f:
        json.dump(facs, f, ensure_ascii=False, indent=2)
    print("Saved facilities.json")

    # ── 3. 最终统计 ──
    from collections import Counter

    # 剩余英文
    eng_left = [n for n in nodes if n.get('name') and re.match(r'^[a-zA-Z0-9\s\(\)\'\-\.]+$', n['name'])]
    print(f"\nRemaining pure English names: {len(eng_left)}")
    for n in eng_left:
        print(f"  {n['id']}: '{n['name']}' type={n.get('type')}")

    # 重新统计设施分类
    cat_counts = Counter(f.get("category") for f in facs)
    print(f"\nFacility categories ({len(facs)} total):")
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat}: {cnt}")


if __name__ == "__main__":
    main()
