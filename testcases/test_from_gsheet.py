"""
从 Google Sheets 在线表格读取的测试用例。支持接口间参数传递。

使用方式（任选其一）：

1. 公开表格（推荐）：
   export GSHEET_CSV_URL="https://docs.google.com/spreadsheets/d/.../pub?output=csv"

2. 服务账号：
   export GOOGLE_CREDENTIALS="/path/to/credentials.json"
   export GSHEET_NAME="测试用例表"
"""
import os
import pytest
from utils.gsheet_reader import load_from_csv_url, load_from_gspread
from utils.context import VarContext
from utils.jsonpath_util import extract_by_path


def _load_cases():
    gsheet_name = os.environ.get("GSHEET_NAME")
    gsheet_sheet = os.environ.get("GSHEET_SHEET")
    csv_url = os.environ.get("GSHEET_CSV_URL")

    if gsheet_name:
        return load_from_gspread(gsheet_name, gsheet_sheet)
    elif csv_url:
        return load_from_csv_url(csv_url)
    else:
        pytest.skip(
            "未配置在线表格数据源。请设置环境变量:\n"
            "  export GSHEET_CSV_URL='https://docs.google.com/spreadsheets/d/.../pub?output=csv'\n"
            "  或\n"
            "  export GSHEET_NAME='你的表格名'\n"
            "  export GOOGLE_CREDENTIALS='/path/to/credentials.json'",
            allow_module_level=True,
        )


_gsheet_cases = _load_cases()
_ids = [f"{c['case_id']}-{c['description']}" for c in _gsheet_cases]


class TestFromGSheet:
    """在线表格数据驱动测试（支持变量传递）"""

    @pytest.fixture(scope="class")
    def ctx(self):
        c = VarContext()
        yield c
        c.clear()

    @pytest.mark.parametrize("case", _gsheet_cases, ids=_ids)
    def test_by_gsheet(self, client, ctx, case):
        path = ctx.substitute(case["path"])
        headers = ctx.substitute(case["headers"])
        body = ctx.substitute(case["body"])

        rsp = client.request(
            method=case["method"],
            path=path,
            headers=headers,
            json=body,
        )

        assert rsp.status_code == case["expected_status"], (
            f"[{case['case_id']}] 状态码不符: "
            f"期望 {case['expected_status']}, 实际 {rsp.status_code}"
        )

        resp_text = rsp.text
        for keyword in case["expected_contains"]:
            assert keyword in resp_text, (
                f"[{case['case_id']}] 响应中缺少关键字: '{keyword}'"
            )

        if case["save_as"] and case["extract_path"]:
            try:
                resp_data = rsp.json()
                value = extract_by_path(resp_data, case["extract_path"])
                ctx.set(case["save_as"], value)
                print(f"  📌 提取变量: {case['save_as']} = {str(value)[:80]}")
            except (KeyError, IndexError, TypeError, ValueError) as e:
                raise AssertionError(
                    f"[{case['case_id']}] 提取变量 '{case['save_as']}' 失败: {e}"
                ) from e
