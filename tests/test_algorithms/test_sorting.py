"""
排序算法测试
"""
import pytest
from backend.algorithms.sorting import (
    quick_sort, merge_sort, heap_sort, multi_key_sort, get_value
)


class TestGetValue:
    def test_none(self):
        assert get_value(5, None) == 5

    def test_callable(self):
        assert get_value({"a": 3}, lambda x: x["a"]) == 3

    def test_string_field(self):
        assert get_value({"a": 3}, "a") == 3

    def test_plain_value(self):
        assert get_value(42, None) == 42


class TestQuickSort:
    def test_basic_ascending(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = quick_sort(arr)
        assert result == sorted(arr)

    def test_descending(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = quick_sort(arr, reverse=True)
        assert result == sorted(arr, reverse=True)

    def test_with_key(self):
        arr = [{"v": 3}, {"v": 1}, {"v": 2}]
        result = quick_sort(arr, key="v")
        assert [x["v"] for x in result] == [1, 2, 3]

    def test_with_key_desc(self):
        arr = [{"v": 3}, {"v": 1}, {"v": 2}]
        result = quick_sort(arr, key="v", reverse=True)
        assert [x["v"] for x in result] == [3, 2, 1]

    def test_empty(self):
        assert quick_sort([]) == []

    def test_single(self):
        assert quick_sort([1]) == [1]

    def test_original_unchanged(self):
        arr = [3, 1, 2]
        quick_sort(arr)
        assert arr == [3, 1, 2]

    def test_sorted(self):
        arr = [1, 2, 3, 4, 5]
        assert quick_sort(arr) == [1, 2, 3, 4, 5]


class TestMergeSort:
    def test_basic_ascending(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = merge_sort(arr)
        assert result == sorted(arr)

    def test_descending(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = merge_sort(arr, reverse=True)
        assert result == sorted(arr, reverse=True)

    def test_with_key(self):
        arr = [{"v": 3}, {"v": 1}, {"v": 2}]
        result = merge_sort(arr, key="v")
        assert [x["v"] for x in result] == [1, 2, 3]

    def test_empty(self):
        assert merge_sort([]) == []

    def test_original_unchanged(self):
        arr = [3, 1, 2]
        merge_sort(arr)
        assert arr == [3, 1, 2]

    def test_stability(self):
        arr = [{"k": 1, "id": 1}, {"k": 1, "id": 2}, {"k": 2, "id": 3}]
        result = merge_sort(arr, key="k")
        # stable: items with same k keep relative order
        ids = [x["id"] for x in result if x["k"] == 1]
        assert ids == [1, 2]


class TestHeapSort:
    def test_basic_ascending(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = heap_sort(arr)
        assert result == sorted(arr)

    def test_descending(self):
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = heap_sort(arr, reverse=True)
        assert result == sorted(arr, reverse=True)

    def test_with_key(self):
        arr = [{"v": 3}, {"v": 1}, {"v": 2}]
        result = heap_sort(arr, key="v")
        assert [x["v"] for x in result] == [1, 2, 3]

    def test_empty(self):
        assert heap_sort([]) == []

    def test_original_unchanged(self):
        arr = [3, 1, 2]
        heap_sort(arr)
        assert arr == [3, 1, 2]

    def test_large(self):
        arr = list(range(100, 0, -1))
        result = heap_sort(arr)
        assert result == list(range(1, 101))


class TestMultiKeySort:
    def test_popularity_desc_rating_desc(self):
        items = [
            {"name": "A", "popularity": 80, "rating": 4.0},
            {"name": "B", "popularity": 90, "rating": 4.5},
            {"name": "C", "popularity": 90, "rating": 4.0},
        ]
        specs = [("popularity", True), ("rating", True)]
        result = multi_key_sort(items, specs)
        assert result[0]["name"] == "B"  # pop=90, rating=4.5
        assert result[1]["name"] == "C"  # pop=90, rating=4.0
        assert result[2]["name"] == "A"  # pop=80

    def test_popularity_desc_name_asc(self):
        items = [
            {"name": "Zoo", "popularity": 80},
            {"name": "Park", "popularity": 80},
            {"name": "Museum", "popularity": 90},
        ]
        specs = [("popularity", True), ("name", False)]
        result = multi_key_sort(items, specs)
        assert result[0]["name"] == "Museum"
        assert result[1]["name"] == "Park"
        assert result[2]["name"] == "Zoo"

    def test_empty(self):
        assert multi_key_sort([], [("k", True)]) == []
