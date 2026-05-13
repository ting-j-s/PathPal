"""
场所查询 API 路由
"""
from flask import Blueprint, request, jsonify
from backend.services.nearby_service import NearbyService

nearby_bp = Blueprint("nearby", __name__, url_prefix="/api")

_service = NearbyService()


@nearby_bp.route("/nearby", methods=["GET"])
def find_nearby():
    destination_id = request.args.get("destination_id")
    node_id = request.args.get("node_id")
    radius = request.args.get("radius", type=float)
    if not all([destination_id, node_id]):
        return jsonify({"error": "destination_id and node_id are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.find_nearby(destination_id, node_id, radius=radius))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@nearby_bp.route("/nearby/category", methods=["GET"])
def find_by_category():
    destination_id = request.args.get("destination_id")
    node_id = request.args.get("node_id")
    category = request.args.get("category")
    radius = request.args.get("radius", type=float)
    if not all([destination_id, node_id, category]):
        return jsonify({"error": "destination_id, node_id, category are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.find_by_category(destination_id, node_id, category, radius=radius))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@nearby_bp.route("/nearby/search", methods=["GET"])
def search_nearby():
    destination_id = request.args.get("destination_id")
    node_id = request.args.get("node_id")
    keyword = request.args.get("keyword")
    radius = request.args.get("radius", type=float)
    if not all([destination_id, node_id, keyword]):
        return jsonify({"error": "destination_id, node_id, keyword are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.search_nearby(destination_id, node_id, keyword, radius=radius))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@nearby_bp.route("/nearby/categories", methods=["GET"])
def list_categories():
    destination_id = request.args.get("destination_id")
    return jsonify(_service.list_facility_categories(destination_id=destination_id))


@nearby_bp.route("/nearby/facilities", methods=["GET"])
def list_facilities():
    destination_id = request.args.get("destination_id")
    if not destination_id:
        return jsonify({"error": "destination_id is required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.list_facilities(destination_id))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400
