"""
PathPal 排序算法（自行实现）
包含：快速排序、归并排序、堆排序、多键排序
"""


def get_value(item, key):
    """从 item 中获取排序键值。支持 callable、字符串字段名、None。"""
    if key is None:
        return item
    if callable(key):
        return key(item)
    if isinstance(key, str):
        return item[key]
    return item


# ============================================================
# 快速排序
# ============================================================
def quick_sort(items, key=None, reverse=False):
    """快速排序，返回新列表，不修改原列表。"""
    if len(items) <= 1:
        return list(items)

    arr = list(items)
    _quick_sort_inplace(arr, 0, len(arr) - 1, key, reverse)
    return arr


def _quick_sort_inplace(arr, lo, hi, key, reverse):
    if lo >= hi:
        return
    p = _partition(arr, lo, hi, key, reverse)
    _quick_sort_inplace(arr, lo, p - 1, key, reverse)
    _quick_sort_inplace(arr, p + 1, hi, key, reverse)


def _partition(arr, lo, hi, key, reverse):
    pivot_val = get_value(arr[hi], key)
    i = lo
    for j in range(lo, hi):
        v = get_value(arr[j], key)
        if reverse:
            if v > pivot_val:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
        else:
            if v < pivot_val:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
    arr[i], arr[hi] = arr[hi], arr[i]
    return i


# ============================================================
# 归并排序
# ============================================================
def merge_sort(items, key=None, reverse=False):
    """归并排序，返回新列表，不修改原列表。"""
    if len(items) <= 1:
        return list(items)

    arr = list(items)
    _merge_sort_range(arr, 0, len(arr) - 1, key, reverse)
    return arr


def _merge_sort_range(arr, lo, hi, key, reverse):
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    _merge_sort_range(arr, lo, mid, key, reverse)
    _merge_sort_range(arr, mid + 1, hi, key, reverse)
    _merge(arr, lo, mid, hi, key, reverse)


def _merge(arr, lo, mid, hi, key, reverse):
    left = arr[lo:mid + 1]
    right = arr[mid + 1:hi + 1]
    i = j = 0
    k = lo
    while i < len(left) and j < len(right):
        lv = get_value(left[i], key)
        rv = get_value(right[j], key)
        if reverse:
            take_left = lv >= rv
        else:
            take_left = lv <= rv
        if take_left:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1


# ============================================================
# 堆排序
# ============================================================
def heap_sort(items, key=None, reverse=False):
    """堆排序，返回新列表，不修改原列表。自行实现堆调整逻辑。"""
    if len(items) <= 1:
        return list(items)

    arr = list(items)
    n = len(arr)

    # 建堆
    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i, key, reverse)

    # 逐个提取
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        _heapify(arr, i, 0, key, reverse)

    return arr


def _heapify(arr, n, i, key, reverse):
    """以 i 为根的子树堆化（大顶堆或小顶堆）。"""
    while True:
        largest_or_smallest = i
        left = 2 * i + 1
        right = 2 * i + 2

        if left < n:
            root_v = get_value(arr[largest_or_smallest], key)
            child_v = get_value(arr[left], key)
            if reverse:
                if child_v < root_v:
                    largest_or_smallest = left
            else:
                if child_v > root_v:
                    largest_or_smallest = left

        if right < n:
            root_v = get_value(arr[largest_or_smallest], key)
            child_v = get_value(arr[right], key)
            if reverse:
                if child_v < root_v:
                    largest_or_smallest = right
            else:
                if child_v > root_v:
                    largest_or_smallest = right

        if largest_or_smallest == i:
            break

        arr[i], arr[largest_or_smallest] = arr[largest_or_smallest], arr[i]
        i = largest_or_smallest


# ============================================================
# 多键排序
# ============================================================
def multi_key_sort(items, key_specs):
    """
    多键排序。key_specs 示例:
        [("popularity", True), ("rating", True), ("name", False)]
    True = 降序, False = 升序。
    支持 item 为 dict，返回新列表。
    """
    if not items:
        return []

    arr = list(items)

    # 自定义比较键：从最低优先级开始稳定排序
    # 使用归并排序的稳定特性，从低优先级到高优先级逐次排序
    for field, desc in reversed(key_specs):
        def make_key(f):
            return lambda x: get_value(x, f)
        arr = merge_sort(arr, key=make_key(field), reverse=desc)

    return arr
