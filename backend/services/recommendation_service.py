"""
PathPal 旅游推荐服务
封装目的地推荐、搜索、过滤逻辑，调用第 2 步自定义算法。
"""
from backend.services import data_loader
from backend.algorithms.topk import top_k_heap, get_top_k_by_field
from backend.algorithms.sorting import multi_key_sort, quick_sort
from backend.algorithms.search import linear_search, filter_by_field


class RecommendationService:

    def get_hot_recommendations(self, k=10):
        """按 popularity 取 Top-K 热点推荐。"""
        destinations = data_loader.load_destinations()
        results = get_top_k_by_field(destinations, k, "popularity", reverse=True)
        return {
            "algorithm": "Top-K Heap",
            "data_structure": "Array + Min-Heap (size K)",
            "count": len(results),
            "results": self._format_results(results),
        }

    def get_rating_recommendations(self, k=10):
        """按 rating 取 Top-K 评分推荐。"""
        destinations = data_loader.load_destinations()
        results = get_top_k_by_field(destinations, k, "rating", reverse=True)
        return {
            "algorithm": "Top-K Heap",
            "data_structure": "Array + Min-Heap (size K)",
            "count": len(results),
            "results": self._format_results(results),
        }

    def get_interest_recommendations(self, user_id, k=10):
        """根据用户兴趣做个性化推荐。"""
        user = data_loader.get_user_by_id(user_id)
        destinations = data_loader.load_destinations()

        interests = set(i.lower() for i in user.get("interests", []))
        fav_cats = set(c.lower() for c in user.get("favorite_categories", []))
        pref_tags = set(t.lower() for t in user.get("preferred_tags", []))

        scored = []
        for dest in destinations:
            match_count = 0
            matched_terms = []

            cat = (dest.get("category") or "").lower()
            if cat in fav_cats:
                match_count += 1
                matched_terms.append(f"category:{dest['category']}")

            for kw in dest.get("keywords", []):
                if kw.lower() in interests:
                    match_count += 1
                    matched_terms.append(f"keyword:{kw}")

            for tag in dest.get("tags", []):
                if tag.lower() in pref_tags:
                    match_count += 1
                    matched_terms.append(f"tag:{tag}")

            # description 中的兴趣词匹配
            desc = (dest.get("description") or "").lower()
            for interest in interests:
                if len(interest) >= 2 and interest in desc:
                    match_count += 0.3
                    matched_terms.append(f"desc:{interest}")

            score = match_count * 10 + dest.get("popularity", 0) * 0.2 + dest.get("rating", 0) * 10

            scored.append({
                **dest,
                "interest_score": round(score, 1),
                "recommendation_reason": matched_terms if matched_terms else ["综合推荐"],
                "matched_terms": matched_terms,
            })

        results = top_k_heap(scored, k, key="interest_score", reverse=True)
        return {
            "algorithm": "Top-K Heap (Interest Score)",
            "data_structure": "Array + Min-Heap (size K)",
            "user_id": user_id,
            "user_interests": user.get("interests", []),
            "count": len(results),
            "results": self._format_results(results),
        }

    def search_destinations(self, keyword, sort_by=None):
        """按关键词搜索目的地，可选排序。"""
        destinations = data_loader.load_destinations()
        fields = ["name", "category", "keywords", "tags", "description"]
        results = linear_search(destinations, keyword, fields)

        if sort_by == "popularity":
            results = quick_sort(results, key="popularity", reverse=True)
        elif sort_by == "rating":
            results = quick_sort(results, key="rating", reverse=True)

        return {
            "algorithm": "Linear Search + Quick Sort",
            "data_structure": "Array",
            "keyword": keyword,
            "sort_by": sort_by,
            "count": len(results),
            "results": self._format_results(results),
        }

    def filter_by_category(self, category, sort_by=None):
        """按类别精确过滤。"""
        destinations = data_loader.load_destinations()
        results = filter_by_field(destinations, "category", category)

        if sort_by == "popularity":
            results = quick_sort(results, key="popularity", reverse=True)
        elif sort_by == "rating":
            results = quick_sort(results, key="rating", reverse=True)

        return {
            "algorithm": "Exact Filter + Quick Sort",
            "data_structure": "Array",
            "category": category,
            "sort_by": sort_by,
            "count": len(results),
            "results": self._format_results(results),
        }

    def get_destination_detail(self, destination_id):
        """返回单个目的地详情。"""
        dest = data_loader.get_destination_by_id(destination_id)
        return {
            "algorithm": "Hash Lookup (by ID)",
            "data_structure": "Array",
            "result": dest,
        }

    def list_destinations(self, limit=None, dest_type=None):
        """列出目的地，可按 type 过滤。"""
        destinations = data_loader.load_destinations()
        if dest_type:
            # 也支持 "mixed" → 过滤 type 为 mixed
            destinations = [d for d in destinations if d.get("type") == dest_type]
        if limit is not None:
            destinations = destinations[:limit]
        return {
            "algorithm": "Array Filter",
            "data_structure": "Array",
            "count": len(destinations),
            "results": self._format_results(destinations),
        }

    def _format_results(self, items):
        """精简输出，去掉冗余字段。"""
        out = []
        for item in items:
            entry = {
                "id": item.get("id"),
                "name": item.get("name"),
                "type": item.get("type"),
                "category": item.get("category"),
                "popularity": item.get("popularity"),
                "rating": item.get("rating"),
                "tags": item.get("tags"),
                "internal_map_id": item.get("internal_map_id"),
            }
            # 额外字段（个性化推荐等）
            for extra in ("interest_score", "recommendation_reason", "matched_terms"):
                if extra in item:
                    entry[extra] = item[extra]
            out.append(entry)
        return out
