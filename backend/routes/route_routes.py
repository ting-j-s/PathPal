"""
路线规划 API 路由
"""
from flask import Blueprint, request, jsonify
from backend.services.route_service import RouteService

route_bp = Blueprint("route", __name__, url_prefix="/api")

_service = RouteService()


@route_bp.route("/route/nodes", methods=["GET"])
def list_nodes():
    destination_id = request.args.get("destination_id")
    if not destination_id:
        return jsonify({"error": "destination_id is required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.list_nodes(destination_id))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@route_bp.route("/route/shortest-distance", methods=["GET"])
def shortest_distance():
    destination_id = request.args.get("destination_id")
    start = request.args.get("start")
    end = request.args.get("end")
    if not all([destination_id, start, end]):
        return jsonify({"error": "destination_id, start, end are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.plan_shortest_distance(destination_id, start, end))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@route_bp.route("/route/shortest-time", methods=["GET"])
def shortest_time():
    destination_id = request.args.get("destination_id")
    start = request.args.get("start")
    end = request.args.get("end")
    transport = request.args.get("transport", "walk")
    if not all([destination_id, start, end]):
        return jsonify({"error": "destination_id, start, end are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.plan_shortest_time(destination_id, start, end, transport))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@route_bp.route("/route/transport-time", methods=["GET"])
def transport_time():
    destination_id = request.args.get("destination_id")
    start = request.args.get("start")
    end = request.args.get("end")
    transport = request.args.get("transport", "walk")
    if not all([destination_id, start, end]):
        return jsonify({"error": "destination_id, start, end are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.plan_transport_time(destination_id, start, end, transport))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@route_bp.route("/route/mixed-time", methods=["GET"])
def mixed_time():
    destination_id = request.args.get("destination_id")
    start = request.args.get("start")
    end = request.args.get("end")
    if not all([destination_id, start, end]):
        return jsonify({"error": "destination_id, start, end are required", "type": "ValueError"}), 400
    try:
        return jsonify(_service.plan_mixed_time(destination_id, start, end))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400


@route_bp.route("/route/multi-point", methods=["POST"])
def multi_point():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON", "type": "ValueError"}), 400
    destination_id = data.get("destination_id")
    start = data.get("start")
    targets = data.get("targets")
    strategy = data.get("strategy", "shortest_distance")
    if not all([destination_id, start, targets]):
        return jsonify({"error": "destination_id, start, targets are required", "type": "ValueError"}), 400
    if strategy not in ("shortest_distance", "shortest_time", "mixed_time"):
        return jsonify({"error": "strategy must be shortest_distance, shortest_time, or mixed_time", "type": "ValueError"}), 400
    try:
        return jsonify(_service.plan_multi_point(destination_id, start, targets, strategy))
    except ValueError as e:
        return jsonify({"error": str(e), "type": "ValueError"}), 400
