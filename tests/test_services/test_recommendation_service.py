"""
推荐服务测试
"""
import pytest
from backend.services.recommendation_service import RecommendationService


@pytest.fixture
def service():
    return RecommendationService()


class TestRecommendationService:

    def test_get_hot_recommendations(self, service):
        result = service.get_hot_recommendations(k=5)
        assert result["algorithm"] == "Top-K Heap"
        assert result["count"] == 5
        assert len(result["results"]) == 5
        # 按 popularity 降序
        pops = [r["popularity"] for r in result["results"]]
        assert pops == sorted(pops, reverse=True)

    def test_get_rating_recommendations(self, service):
        result = service.get_rating_recommendations(k=5)
        assert result["algorithm"] == "Top-K Heap"
        assert result["count"] == 5
        assert len(result["results"]) == 5

    def test_get_interest_recommendations(self, service):
        result = service.get_interest_recommendations("USER_001", k=5)
        assert result["algorithm"] == "Top-K Heap (Interest Score)"
        assert result["user_id"] == "USER_001"
        assert result["count"] == 5
        assert len(result["results"]) == 5
        # 每个结果应有 interest_score 和 recommendation_reason
        for r in result["results"]:
            assert "interest_score" in r
            assert "recommendation_reason" in r
            assert isinstance(r["recommendation_reason"], list)

    def test_interest_invalid_user(self, service):
        with pytest.raises(ValueError):
            service.get_interest_recommendations("NONEXIST", k=5)

    def test_search_destinations(self, service):
        result = service.search_destinations("北京")
        assert result["keyword"] == "北京"
        assert result["count"] > 0
        assert len(result["results"]) > 0

    def test_search_destinations_with_sort(self, service):
        result = service.search_destinations("北京", sort_by="popularity")
        pops = [r["popularity"] for r in result["results"]]
        assert pops == sorted(pops, reverse=True)

        result2 = service.search_destinations("北京", sort_by="rating")
        ratings = [r["rating"] for r in result2["results"]]
        assert ratings == sorted(ratings, reverse=True)

    def test_search_chinese_keyword(self, service):
        result = service.search_destinations("故宫")
        assert result["count"] > 0

    def test_filter_by_category(self, service):
        result = service.filter_by_category("park")
        assert result["category"] == "park"
        for r in result["results"]:
            assert r["category"] == "park"

    def test_filter_by_category_with_sort(self, service):
        result = service.filter_by_category("museum", sort_by="popularity")
        if result["count"] >= 2:
            pops = [r["popularity"] for r in result["results"]]
            assert pops == sorted(pops, reverse=True)

    def test_get_destination_detail(self, service):
        result = service.get_destination_detail("DEST_001")
        assert result["result"]["id"] == "DEST_001"

    def test_get_destination_detail_invalid(self, service):
        with pytest.raises(ValueError):
            service.get_destination_detail("NONEXIST")

    def test_list_destinations(self, service):
        result = service.list_destinations()
        assert result["count"] == 217

    def test_list_destinations_with_type(self, service):
        result = service.list_destinations(dest_type="campus")
        assert result["count"] == 30
        for r in result["results"]:
            assert r["type"] == "campus"

    def test_list_destinations_with_limit(self, service):
        result = service.list_destinations(limit=10)
        assert result["count"] == 10
