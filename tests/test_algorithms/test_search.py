"""
查找算法测试
"""
import pytest
from backend.algorithms.search import (
    linear_search, exact_search, build_hash_index, hash_search,
    keyword_search, filter_by_field, filter_by_map_id,
)


class TestLinearSearch:
    def test_chinese_keyword(self):
        items = [
            {"id": 1, "name": "故宫博物院", "category": "museum"},
            {"id": 2, "name": "天坛公园", "category": "park"},
            {"id": 3, "name": "颐和园", "category": "park"},
        ]
        results = linear_search(items, "公园", ["name", "category"])
        # "天坛公园" name matches; "颐和园" name doesn't contain "公园" and
        # category "park" doesn't match Chinese "公园"
        assert len(results) == 1
        assert results[0]["id"] == 2

    def test_case_insensitive(self):
        items = [
            {"name": "Museum"},
            {"name": "museum"},
        ]
        results = linear_search(items, "MUSEUM", ["name"])
        assert len(results) == 2

    def test_list_field(self):
        items = [
            {"id": 1, "tags": ["历史", "文化"]},
            {"id": 2, "tags": ["自然", "公园"]},
        ]
        results = linear_search(items, "历史", ["tags"])
        assert len(results) == 1
        assert results[0]["id"] == 1

    def test_numeric_field(self):
        items = [
            {"id": 10, "name": "A"},
            {"id": 20, "name": "B"},
        ]
        results = linear_search(items, "10", ["id"])
        assert len(results) == 1
        assert results[0]["id"] == 10

    def test_keyword_none(self):
        assert linear_search([{"a": 1}], None, ["a"]) == []

    def test_empty_items(self):
        assert linear_search([], "test", ["a"]) == []

    def test_no_match(self):
        items = [{"name": "A"}, {"name": "B"}]
        results = linear_search(items, "Z", ["name"])
        assert results == []


class TestExactSearch:
    def test_exact_match(self):
        items = [
            {"id": 1, "type": "campus"},
            {"id": 2, "type": "attraction"},
        ]
        results = exact_search(items, "campus", "type")
        assert len(results) == 1
        assert results[0]["id"] == 1

    def test_no_exact_match(self):
        items = [{"type": "campus"}]
        results = exact_search(items, "Campus", "type")  # case-sensitive
        assert results == []


class TestHashIndex:
    def test_build_and_search(self):
        items = [
            {"type": "campus", "name": "A"},
            {"type": "attraction", "name": "B"},
            {"type": "campus", "name": "C"},
        ]
        index = build_hash_index(items, "type")
        results = hash_search(index, "campus")
        assert len(results) == 2

    def test_missing_value(self):
        index = build_hash_index([{"type": "campus"}], "type")
        assert hash_search(index, "nonexist") == []


class TestFilterFunctions:
    def test_filter_by_field(self):
        items = [
            {"id": 1, "map_id": "M1"},
            {"id": 2, "map_id": "M2"},
            {"id": 3, "map_id": "M1"},
        ]
        results = filter_by_field(items, "map_id", "M1")
        assert len(results) == 2

    def test_filter_by_map_id(self):
        items = [
            {"id": 1, "map_id": "M1"},
            {"id": 2, "map_id": "M2"},
        ]
        results = filter_by_map_id(items, "M1")
        assert len(results) == 1


class TestKeywordSearch:
    def test_delegates_to_linear_search(self):
        items = [{"name": "Hello"}, {"name": "World"}]
        assert keyword_search(items, "hello", ["name"]) == linear_search(items, "hello", ["name"])
