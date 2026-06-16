import pytest
import sys
import os

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.dirname(__file__))

from utils.http_client import HttpClient


@pytest.fixture(scope="session")
def client():
    """全局 HTTP 客户端，一个 session 跑完全部用例"""
    c = HttpClient()
    yield c
    c.close()


# ═══════════════════════════════════════════════
# pytest-html 报告定制
# ═══════════════════════════════════════════════

def pytest_html_report_title(report):
    report.title = "自动化测试报告"


def pytest_html_results_summary(prefix, summary, postfix):
    from datetime import datetime
    prefix.extend([
        f"<p>执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
    ])


def pytest_html_results_table_header(cells):
    cells.insert(2, '<th class="sortable category" data-column-type="category">分类</th>')


def pytest_html_results_table_row(report, cells):
    category = "—"
    if hasattr(report, "user_properties"):
        for prop in report.user_properties:
            if prop[0] == "category":
                category = prop[1]
    cells.insert(2, f'<td class="col-category">{category}</td>')


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    category_map = {"smoke": "冒烟", "positive": "正向", "negative": "异常", "structure": "结构"}
    markers = [m.name for m in item.iter_markers() if m.name in category_map]
    category = category_map.get(markers[0], "—") if markers else "—"
    report.user_properties = [("category", category)]
