"""
从 Google Sheets 在线表格读取的测试用例。

使用方式（任选其一）：

1. 公开表格（推荐）：
   将 Google Sheet 发布为 CSV：
   - 文件 → 共享 → 发布到网络 → 选择 sheet → CSV → 复制链接
   - 设置环境变量: export GSHEET_CSV_URL="https://docs.google.com/spreadsheets/d/.../pub?output=csv"

2. 服务账号（私密表格）：
   - 创建 GCP 服务账号 → 下载 JSON 密钥
   - export GOOGLE_CREDENTIALS="/path/to/credentials.json"
   - 将服务账号邮箱添加为表格查看者
   - python run.py -k "test_from_gsheet" 时传 GSHEET_NAME 和 GSHEET_SHEET
"""
import os
import pytest
from utils.gsheet_reader import load_from_csv_url, load_from_gspread


def _load_cases():
    """按优先级选择数据源：GSHEET_NAME > GSHEET_CSV_URL"""
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
    """在线表格数据驱动测试"""

    @pytest.mark.parametrize("case", _gsheet_cases, ids=_ids)
    def test_by_gsheet(self, client, case):
        """按在线表格中定义的参数执行接口测试"""
        rsp = client.request(
            method=case["method"],
            path=case["path"],
            headers=case["headers"],
            json=case["body"],
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
