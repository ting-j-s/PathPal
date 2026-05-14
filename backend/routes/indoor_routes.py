"""
室内导航 API 路由
"""
from flask import Blueprint, request, jsonify
from backend.services.indoor_service import IndoorService

indoor_bp = Blueprint("indoor", __name__, url_prefix="/api")

_service = IndoorService()


@indoor_bp.route("/indoor/buildings", methods=["GET"])
def list_buildings():
    """列出所有室内建筑。"""
    return jsonify(_service.list_buildings())


@indoor_bp.route("/indoor/buildings/<building_id>", methods=["GET"])
def get_building(building_id):
    """获取单个建筑详情。"""
    try:
        return jsonify(_service.get_building(building_id))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 404


@indoor_bp.route("/indoor/nodes", methods=["GET"])
def list_nodes():
    """获取建筑内节点，可按楼层过滤。"""
    building_id = request.args.get("building_id")
    floor = request.args.get("floor")
    if not building_id:
        return jsonify({"error": "building_id is required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.list_nodes(building_id, floor=floor))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 404


@indoor_bp.route("/indoor/floors", methods=["GET"])
def list_floors():
    """获取建筑楼层信息。"""
    building_id = request.args.get("building_id")
    if not building_id:
        return jsonify({"error": "building_id is required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.list_floors(building_id))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 404


@indoor_bp.route("/indoor/route", methods=["GET"])
def indoor_route():
    """规划室内路径。"""
    building_id = request.args.get("building_id")
    start = request.args.get("start")
    end = request.args.get("end")
    strategy = request.args.get("strategy", "shortest_distance")

    if not all([building_id, start, end]):
        return jsonify({
            "error": "building_id, start, end are required",
            "type": "ValueError"
        }), 400

    try:
        result = _service.plan_indoor_route(
            building_id, start, end, strategy=strategy
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400
