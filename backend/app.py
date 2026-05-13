"""
PathPal Flask 应用入口
启动后端 API 服务
"""
import sys
from pathlib import Path

# 确保项目根目录在 sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify
import config

from backend.routes.recommendation_routes import recommendation_bp
from backend.routes.route_routes import route_bp
from backend.routes.nearby_routes import nearby_bp
from backend.routes.indoor_routes import indoor_bp
from backend.services.data_loader import get_stats


def create_app():
    app = Flask(__name__)

    # CORS 支持
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    # 注册蓝图
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(route_bp)
    app.register_blueprint(nearby_bp)
    app.register_blueprint(indoor_bp)

    # 健康检查
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "project": "PathPal",
            "phase": "phase1-backend-api",
        })

    # 统计接口
    @app.route("/api/stats", methods=["GET"])
    def stats():
        return jsonify(get_stats())

    # 全局错误处理
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"error": str(e), "type": "ValueError"}), 400

    @app.errorhandler(FileNotFoundError)
    def handle_file_not_found(e):
        return jsonify({"error": f"File not found: {str(e)}", "type": "FileNotFoundError"}), 500

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({"error": "Internal server error", "type": "InternalError"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
    )
