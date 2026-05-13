"""
PathPal 查找算法（自行实现）
包含：线性查找、精确查找、哈希索引、关键词搜索、字段过滤
"""


def linear_search(items, keyword, fields):
    """
    在 items 中线性查找 keyword。
    - 字符串字段：大小写不敏感包含匹配
    - 数值字段：转为字符串后匹配
    - 列表字段：逐个元素匹配
    - 中文：直接包含匹配
    返回匹配 item 列表。
    """
    if not items or keyword is None:
        return []

    kw_lower = str(keyword).lower()
    results = []

    for item in items:
        found = False
        for field in fields:
            val = item.get(field) if isinstance(item, dict) else item
            if _match_value(val, kw_lower):
                found = True
                break
        if found:
            results.append(item)

    return results


def _match_value(val, kw_lower):
    """检查单个值是否匹配关键词。"""
    if val is None:
        return False
    if isinstance(val, str):
        return kw_lower in val.lower()
    if isinstance(val, (int, float)):
        return kw_lower in str(val).lower()
    if isinstance(val, list):
        for elem in val:
            if isinstance(elem, str) and kw_lower in elem.lower():
                return True
            if isinstance(elem, (int, float)) and kw_lower in str(elem).lower():
                return True
    return False


def exact_search(items, value, field):
    """精确匹配字段值。返回匹配 item 列表。"""
    results = []
    for item in items:
        item_val = item.get(field) if isinstance(item, dict) else item
        if item_val == value:
            results.append(item)
    return results


def build_hash_index(items, field):
    """
    构建哈希索引: {field_value: [item1, item2, ...]}
    field_value 使用 str() 归一化。
    """
    index = {}
    for item in items:
        val = item.get(field) if isinstance(item, dict) else item
        key = str(val)
        if key not in index:
            index[key] = []
        index[key].append(item)
    return index


def hash_search(index, value):
    """从哈希索引查找 value。返回列表。"""
    key = str(value)
    return index.get(key, [])


def keyword_search(items, keyword, fields):
    """关键词搜索的业务语义接口。直接委托 linear_search。"""
    return linear_search(items, keyword, fields)


def filter_by_field(items, field, value):
    """过滤字段等于 value 的 item。"""
    results = []
    for item in items:
        item_val = item.get(field) if isinstance(item, dict) else item
        if item_val == value:
            results.append(item)
    return results


def filter_by_map_id(items, map_id):
    """过滤 item["map_id"] == map_id。"""
    return filter_by_field(items, "map_id", map_id)
