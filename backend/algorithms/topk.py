"""
PathPal Top-K 算法（自行实现）
包含：小顶堆 Top-K、快速选择 Top-K、按字段 Top-K
不依赖 sorted() 或 heapq 完成核心逻辑。
"""
from .sorting import get_value, quick_sort


# ============================================================
# 小顶堆 Top-K
# ============================================================
def top_k_heap(items, k, key=None, reverse=True):
    """
    用小顶堆取 Top-K。
    reverse=True: 取 key 最大的前 k 个。
    reverse=False: 取 key 最小的前 k 个。
    返回结果按 key 排好序。
    """
    if k <= 0 or not items:
        return []

    n = len(items)
    if k >= n:
        result = list(items)
        return quick_sort(result, key=key, reverse=reverse)

    # reverse=True → 取最大的 k → 维护大小为 k 的小顶堆
    # reverse=False → 取最小的 k → 维护大小为 k 的大顶堆
    heap = []
    for item in items:
        val = get_value(item, key)
        if len(heap) < k:
            heap.append((val, item))
            # reverse=True → 取最大k → 小顶堆(use_max=False)
            _sift_up(heap, len(heap) - 1, not reverse)
        else:
            # 判断是否应该进入堆
            should_enter = False
            if reverse:
                # 小顶堆堆顶最小，新值 > 堆顶则进入
                if val > heap[0][0]:
                    should_enter = True
            else:
                # 大顶堆堆顶最大，新值 < 堆顶则进入
                if val < heap[0][0]:
                    should_enter = True
            if should_enter:
                heap[0] = (val, item)
                _sift_down(heap, 0, k, not reverse)

    result = [item for _, item in heap]
    return quick_sort(result, key=key, reverse=reverse)


def _sift_up(heap, idx, use_max):
    """上浮操作。use_max=True 表示大顶堆，False 表示小顶堆。"""
    while idx > 0:
        parent = (idx - 1) // 2
        should_swap = False
        if use_max:
            if heap[idx][0] > heap[parent][0]:
                should_swap = True
        else:
            if heap[idx][0] < heap[parent][0]:
                should_swap = True
        if not should_swap:
            break
        heap[idx], heap[parent] = heap[parent], heap[idx]
        idx = parent


def _sift_down(heap, idx, size, use_max):
    """下沉操作。use_max=True 表示大顶堆，False 表示小顶堆。"""
    while True:
        target = idx
        left = 2 * idx + 1
        right = 2 * idx + 2

        if left < size:
            should_update = False
            if use_max:
                if heap[left][0] > heap[target][0]:
                    should_update = True
            else:
                if heap[left][0] < heap[target][0]:
                    should_update = True
            if should_update:
                target = left

        if right < size:
            should_update = False
            if use_max:
                if heap[right][0] > heap[target][0]:
                    should_update = True
            else:
                if heap[right][0] < heap[target][0]:
                    should_update = True
            if should_update:
                target = right

        if target == idx:
            break

        heap[idx], heap[target] = heap[target], heap[idx]
        idx = target


# ============================================================
# 快速选择 Top-K
# ============================================================
def top_k_quickselect(items, k, key=None, reverse=True):
    """
    用快速选择思想取 Top-K。
    reverse=True: 取 key 最大的前 k 个。
    reverse=False: 取 key 最小的前 k 个。
    """
    if k <= 0 or not items:
        return []

    n = len(items)
    if k >= n:
        result = list(items)
        return quick_sort(result, key=key, reverse=reverse)

    arr = list(items)
    _quickselect(arr, 0, len(arr) - 1, k, key, reverse)
    result = arr[:k]
    return quick_sort(result, key=key, reverse=reverse)


def _quickselect(arr, lo, hi, k, key, reverse):
    """在 arr[lo..hi] 中找出第 k 小/大的分界。"""
    if lo >= hi:
        return
    p = _qs_partition(arr, lo, hi, key, reverse)
    # p 是分区后 pivot 的位置
    if p == k:
        return
    elif p > k:
        _quickselect(arr, lo, p - 1, k, key, reverse)
    else:
        _quickselect(arr, p + 1, hi, k, key, reverse)


def _qs_partition(arr, lo, hi, key, reverse):
    pivot_val = get_value(arr[hi], key)
    i = lo
    # reverse=True: 降序排列 → 大的在前
    # reverse=False: 升序排列 → 小的在前
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
# 按字段取 Top-K
# ============================================================
def get_top_k_by_field(items, k, field, reverse=True):
    """针对 dict 字段取 Top-K，内部调用 top_k_heap。"""
    return top_k_heap(items, k, key=field, reverse=reverse)
