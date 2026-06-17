"""报告查看 API"""
import os
from flask import Blueprint, jsonify, render_template, send_from_directory, current_app

from webapp.db import list_test_runs, get_test_run

api = Blueprint("reports_api", __name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")


@api.route("/reports")
def page_reports():
    """历史报告页面"""
    return render_template("reports.html")


@api.route("/api/reports", methods=["GET"])
def api_list():
    runs = list_test_runs(limit=30)
    return jsonify(runs)


@api.route("/api/reports/<int:id>", methods=["GET"])
def api_get(id):
    run = get_test_run(id)
    if not run:
        return jsonify({"error": "记录不存在"}), 404
    return jsonify(run)


@api.route("/reports/<path:filename>")
def serve_report(filename):
    """直接提供 reports/ 下的静态 HTML 报告文件"""
    return send_from_directory(REPORTS_DIR, filename)
