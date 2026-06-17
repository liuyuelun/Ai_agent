"""
自动化测试平台 — Flask 应用入口

启动方式:
    python -m webapp.app
    # 然后浏览器访问 http://localhost:5000
"""

import os
import sys
import webbrowser
from flask import Flask, render_template

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webapp.db import init_db
from webapp.routes_testcases import api as tc_api
from webapp.routes_runner import api as runner_api
from webapp.routes_reports import api as reports_api


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    app.config["SECRET_KEY"] = "automation-platform-secret"

    init_db()

    app.register_blueprint(tc_api)
    app.register_blueprint(runner_api)
    app.register_blueprint(reports_api)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


def main():
    app = create_app()
    port = 5000
    print(f"\n{'=' * 50}")
    print(f"  自动化测试平台已启动")
    print(f"  地址: http://localhost:{port}")
    print(f"{'=' * 50}\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
