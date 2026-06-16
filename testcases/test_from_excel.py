"""
从 Excel 表格读取的测试用例。
用例数据源: testdata/login_cases.xlsx

Excel 表头定义：
    case_id | description | method | path | headers | body | expected_status | expected_contains | category
"""
import pytest
from utils.excel_reader import load_testcases

# 从 Excel 加载所有用例
_excel_cases = load_testcases("login_cases.xlsx")

# 生成 pytest 的 parametrize id
_ids = [f"{c['case_id']}-{c['description']}" for c in _excel_cases]


class TestFromExcel:
    """Excel 数据驱动测试"""

    @pytest.mark.parametrize("case", _excel_cases, ids=_ids)
    def test_by_excel(self, client, case):
        """按 Excel 中定义的参数执行接口测试"""
        # 构造请求
        rsp = client.request(
            method=case["method"],
            path=case["path"],
            headers=case["headers"],
            json=case["body"],
        )

        # 断言状态码
        assert rsp.status_code == case["expected_status"], (
            f"[{case['case_id']}] 状态码不符: "
            f"期望 {case['expected_status']}, 实际 {rsp.status_code}"
        )

        # 断言响应内容包含期望字符串
        resp_text = rsp.text
        for keyword in case["expected_contains"]:
            assert keyword in resp_text, (
                f"[{case['case_id']}] 响应中缺少关键字: '{keyword}'"
            )
