"""
旅游推荐 API 路由
"""
from flask import Blueprint, request, jsonify
from backend.services.recommendation_service import RecommendationService

recommendation_bp = Blueprint("recommendation", __name__, url_prefix="/api")

_service = RecommendationService()


@recommendation_bp.route("/destinations", methods=["GET"])
def list_destinations():
    limit = request.args.get("limit", type=int)
    dest_type = request.args.get("type")
    if dest_type and dest_type not in ("campus", "attraction"):
        return jsonify({"error": "type must be 'campus' or 'attraction'", "type": "ValueError"}), 400
    return jsonify(_service.list_destinations(limit=limit, dest_type=dest_type))


@recommendation_bp.route("/destinations/<destination_id>", methods=["GET"])
def get_destination(destination_id):
    try:
        return jsonify(_service.get_destination_detail(destination_id))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@recommendation_bp.route("/recommendations/hot", methods=["GET"])
def hot_recommendations():
    k = request.args.get("k", 10, type=int)
    return jsonify(_service.get_hot_recommendations(k=k))


@recommendation_bp.route("/recommendations/rating", methods=["GET"])
def rating_recommendations():
    k = request.args.get("k", 10, type=int)
    return jsonify(_service.get_rating_recommendations(k=k))


@recommendation_bp.route("/recommendations/interest", methods=["GET"])
def interest_recommendations():
    user_id = request.args.get("user_id")
    k = request.args.get("k", 10, type=int)
    if not user_id:
        return jsonify({"error": "user_id is required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.get_interest_recommendations(user_id=user_id, k=k))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@recommendation_bp.route("/destinations/search", methods=["GET"])
def search_destinations():
    keyword = request.args.get("keyword")
    sort_by = request.args.get("sort_by")
    if not keyword:
        return jsonify({"error": "keyword is required", "type": "ValueError"}), 400
    if sort_by and sort_by not in ("popularity", "rating"):
        return jsonify({"error": "sort_by must be 'popularity' or 'rating'", "type": "ValueError"}), 400
    return jsonify(_service.search_destinations(keyword=keyword, sort_by=sort_by))


@recommendation_bp.route("/destinations/category", methods=["GET"])
def filter_by_category():
    category = request.args.get("category")
    sort_by = request.args.get("sort_by")
    if not category:
        return jsonify({"error": "category is required", "type": "ValueError"}), 400
    if sort_by and sort_by not in ("popularity", "rating"):
        return jsonify({"error": "sort_by must be 'popularity' or 'rating'", "type": "ValueError"}), 400
    return jsonify(_service.filter_by_category(category=category, sort_by=sort_by))
