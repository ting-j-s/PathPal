"""
室内导航 API 路由（简单 Demo）
"""
from flask import Blueprint, request, jsonify
from backend.services.indoor_service import IndoorService

indoor_bp = Blueprint("indoor", __name__, url_prefix="/api")

_service = IndoorService()


@indoor_bp.route("/indoor/buildings", methods=["GET"])
def list_buildings():
    return jsonify(_service.list_buildings())


@indoor_bp.route("/indoor/route", methods=["GET"])
def indoor_route():
    building_id = request.args.get("building_id")
    start = request.args.get("start")
    end = request.args.get("end")
    if not all([building_id, start, end]):
        return jsonify({"error": "building_id, start, end are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.plan_indoor_route(building_id, start, end))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400
