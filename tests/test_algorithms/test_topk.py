"""
Top-K 算法测试
"""
import pytest
from backend.algorithms.topk import top_k_heap, top_k_quickselect, get_top_k_by_field


class TestTopKHeap:
    def test_basic_top_k_by_popularity(self):
        items = [
            {"name": "A", "popularity": 50},
            {"name": "B", "popularity": 90},
            {"name": "C", "popularity": 30},
            {"name": "D", "popularity": 80},
            {"name": "E", "popularity": 60},
        ]
        result = top_k_heap(items, 3, key="popularity", reverse=True)
        assert len(result) == 3
        # should be top 3 by popularity desc
        pops = [x["popularity"] for x in result]
        assert pops == [90, 80, 60]

    def test_result_count_not_exceed_k(self):
        items = list(range(20))
        result = top_k_heap(items, 5, key=None, reverse=True)
        assert len(result) == 5

    def test_k_larger_than_list(self):
        items = [1, 2, 3]
        result = top_k_heap(items, 10, key=None, reverse=True)
        assert len(result) == 3

    def test_k_zero(self):
        assert top_k_heap([1, 2, 3], 0, key=None) == []

    def test_empty(self):
        assert top_k_heap([], 5, key=None) == []

    def test_reverse_false(self):
        items = [5, 3, 1, 4, 2]
        result = top_k_heap(items, 3, key=None, reverse=False)
        assert result == [1, 2, 3]

    def test_compare_with_sorted(self):
        items = [{"v": i} for i in range(100, 0, -1)]
        import random
        random.seed(42)
        random.shuffle(items)

        k = 10
        heap_result = top_k_heap(items, k, key="v", reverse=True)
        sorted_top = sorted(items, key=lambda x: x["v"], reverse=True)[:k]
        assert [x["v"] for x in heap_result] == [x["v"] for x in sorted_top]

    def test_sorted_desc(self):
        items = [{"pop": 80}, {"pop": 90}, {"pop": 70}]
        result = top_k_heap(items, 2, key="pop", reverse=True)
        pops = [x["pop"] for x in result]
        assert pops == [90, 80]


class TestTopKQuickselect:
    def test_basic_top_k(self):
        items = [
            {"name": "A", "popularity": 50},
            {"name": "B", "popularity": 90},
            {"name": "C", "popularity": 30},
            {"name": "D", "popularity": 80},
            {"name": "E", "popularity": 60},
        ]
        result = top_k_quickselect(items, 3, key="popularity", reverse=True)
        assert len(result) == 3
        pops = [x["popularity"] for x in result]
        assert pops == [90, 80, 60]

    def test_k_larger_than_list(self):
        items = [1, 2, 3]
        result = top_k_quickselect(items, 10, key=None, reverse=True)
        assert len(result) == 3

    def test_k_zero(self):
        assert top_k_quickselect([1, 2, 3], 0, key=None) == []

    def test_empty(self):
        assert top_k_quickselect([], 5, key=None) == []

    def test_reverse_false(self):
        items = [5, 3, 1, 4, 2]
        result = top_k_quickselect(items, 3, key=None, reverse=False)
        assert result == [1, 2, 3]

    def test_compare_with_sorted(self):
        items = [{"v": i} for i in range(100)]
        import random
        random.seed(42)
        random.shuffle(items)

        k = 10
        qs_result = top_k_quickselect(items, k, key="v", reverse=True)
        sorted_top = sorted(items, key=lambda x: x["v"], reverse=True)[:k]
        assert sorted([x["v"] for x in qs_result]) == sorted([x["v"] for x in sorted_top])


class TestGetTopKByField:
    def test_by_popularity(self):
        items = [
            {"name": "A", "popularity": 50},
            {"name": "B", "popularity": 90},
            {"name": "C", "popularity": 30},
            {"name": "D", "popularity": 80},
        ]
        result = get_top_k_by_field(items, 3, "popularity", reverse=True)
        assert len(result) == 3
        assert result[0]["popularity"] >= result[1]["popularity"] >= result[2]["popularity"]

    def test_by_rating(self):
        items = [
            {"name": "A", "rating": 3.5},
            {"name": "B", "rating": 4.8},
            {"name": "C", "rating": 4.0},
            {"name": "D", "rating": 4.2},
        ]
        result = get_top_k_by_field(items, 2, "rating", reverse=True)
        assert len(result) == 2
        assert result[0]["rating"] == 4.8
