"""测试执行 API —— 动态生成 pytest 文件并运行"""
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from webapp.db import (
    get_testcase_by_case_id, list_testcases, create_test_run,
)

api = Blueprint("runner_api", __name__)

_running_lock = threading.Lock()
_is_running = False

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")


def _pytest_output_to_html(output: str, report_filename: str, css_path: str) -> str:
    """将 pytest 的终端输出转为简单的 HTML，嵌入到报告页面下方。"""
    escaped = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<details open style="margin-top:20px;background:#fff;border-radius:8px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
<summary style="cursor:pointer;font-size:16px;font-weight:bold;color:#2c3e50;padding:8px 0;">Terminal Output</summary>
<pre style="background:#f8f9fa;color:#2c3e50;padding:16px;border-radius:4px;overflow-x:auto;font-size:12px;line-height:1.5;max-height:600px;overflow-y:auto;border:1px solid #dee2e6;">{escaped}</pre>
</details>"""


@api.route("/api/run", methods=["POST"])
def api_run():
    global _is_running
    data = request.get_json() or {}

    if _is_running:
        return jsonify({"error": "已有测试正在执行中，请稍后再试"}), 409

    case_ids = data.get("case_ids", [])
    if not case_ids:
        # 未指定则跑全部
        all_cases = list_testcases()
        case_ids = [c["case_id"] for c in all_cases]

    # 从数据库加载用例
    cases = []
    for cid in case_ids:
        case = get_testcase_by_case_id(cid)
        if case:
            cases.append(case)

    if not cases:
        return jsonify({"error": "没有找到可执行的用例"}), 400

    # 转换为 parametrize 所需格式
    parametrize_data = []
    for c in cases:
        parametrize_data.append({
            "case_id": c["case_id"],
            "description": c["description"],
            "method": c["method"],
            "path": c["path"],
            "headers": c["headers"],      # JSON 字符串
            "body": c["body"],            # JSON 字符串
            "expected_status": c["expected_status"],
            "expected_contains": c["expected_contains"],
            "extract_path": c["extract_path"],
            "save_as": c["save_as"],
        })

    # 动态生成临时测试文件（放在项目根目录，避免 platform 包名冲突）
    temp_test_path = os.path.join(PROJECT_ROOT, "_temp_platform_test.py")
    _generate_temp_test_file(temp_test_path, parametrize_data)

    # 生成报告文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"report_platform_{timestamp}.html"
    report_path = os.path.join(REPORTS_DIR, report_filename)
    css_path = os.path.join(PROJECT_ROOT, "report_style.css")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    cmd = [
        sys.executable, "-m", "pytest", temp_test_path,
        "-v", "--tb=short",
        f"--html={report_path}",
        "--self-contained-html",
        f"--css={css_path}",
    ]

    try:
        with _running_lock:
            _is_running = True

        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=600)
        output = result.stdout + result.stderr

        # 解析结果
        total = passed = failed = skipped = 0
        m = re.search(r"(\d+) passed", output)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+) failed", output)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+) skipped", output)
        if m:
            skipped = int(m.group(1))
        total = passed + failed + skipped

        # 提取耗时
        duration = 0
        m = re.search(r"([\d.]+)s ==", output)
        if m:
            duration = float(m.group(1))
        else:
            m = re.search(r"in ([\d.]+)s", output)
            if m:
                duration = float(m.group(1))

        # 将终端输出附加到报告末尾
        _append_terminal_output(report_path, output)

        # 保存执行记录
        run_id = create_test_run(report_filename, total, passed, failed, skipped, duration)

    except subprocess.TimeoutExpired:
        return jsonify({"error": "测试执行超时（超过10分钟）"}), 500
    finally:
        with _running_lock:
            _is_running = False

    # 清理临时文件
    try:
        os.remove(temp_test_path)
        for ext in ("", "c", "o"):
            cache_dir = os.path.join(os.path.dirname(__file__), "__pycache__")
            for f in os.listdir(cache_dir) if os.path.exists(cache_dir) else []:
                if "_temp_test" in f:
                    os.remove(os.path.join(cache_dir, f))
    except Exception:
        pass

    return jsonify({
        "run_id": run_id,
        "report_url": f"/reports/{report_filename}",
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
    })


@api.route("/api/run/status", methods=["GET"])
def api_run_status():
    return jsonify({"is_running": _is_running})


def _generate_temp_test_file(filepath: str, cases: list):
    """生成临时的 pytest 测试文件"""
    cases_json = json.dumps(cases, ensure_ascii=False, indent=4)

    code = f'''# 自动生成的临时测试文件，请勿手动编辑
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.context import VarContext
from utils.jsonpath_util import extract_by_path

_cases = {cases_json}

_ids = [f"{{c['case_id']}}-{{c['description']}}" for c in _cases]


class TestPlatformRun:
    """平台执行测试"""

    @pytest.fixture(scope="class")
    def ctx(self):
        c = VarContext()
        yield c
        c.clear()

    @pytest.mark.parametrize("case", _cases, ids=_ids)
    def test_case(self, client, ctx, case):
        path = ctx.substitute(case["path"])
        headers_raw = case.get("headers", "")
        headers = ctx.substitute(json.loads(headers_raw) if headers_raw else {{}})
        body_raw = case.get("body", "")
        body = ctx.substitute(json.loads(body_raw) if body_raw else None)

        rsp = client.request(
            method=case["method"],
            path=path,
            headers=headers,
            json=body,
        )

        assert rsp.status_code == case["expected_status"], (
            f"[{{case['case_id']}}] 状态码不符: "
            f"期望 {{case['expected_status']}}, 实际 {{rsp.status_code}}"
        )

        resp_text = rsp.text
        contains_raw = case.get("expected_contains", "")
        for keyword in [s.strip() for s in contains_raw.split(";;") if s.strip()]:
            assert keyword in resp_text, (
                f"[{{case['case_id']}}] 响应中缺少关键字: '{{keyword}}'"
            )

        if case.get("save_as") and case.get("extract_path"):
            try:
                resp_data = rsp.json()
                value = extract_by_path(resp_data, case["extract_path"])
                ctx.set(case["save_as"], value)
                print(f"  📌 提取变量: {{case['save_as']}} = {{str(value)[:80]}}")
            except (KeyError, IndexError, TypeError, ValueError) as e:
                raise AssertionError(
                    f"[{{case['case_id']}}] 提取变量 '{{case['save_as']}}' 失败: {{e}}"
                ) from e
'''
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)


def _append_terminal_output(report_path: str, output: str):
    """将终端输出追加到 HTML 报告中"""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            html = f.read()

        terminal_html = _pytest_output_to_html(output, "", "")
        html = html.replace("</body>", f"{terminal_html}</body>")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass
