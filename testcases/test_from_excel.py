"""
从 Excel 表格读取的测试用例。支持接口间参数传递。

Excel 表头定义：
    case_id | description | method | path | headers | body
    | expected_status | expected_contains | category
    | extract_path | save_as

变量引用规则：
    - 在 headers / body / path 中使用 {{变量名}} 引用前序用例已提取的值
    - 在 extract_path 中填写 JSON dot-notation 路径（如 accessToken）
    - 在 save_as 中填写变量名，提取后的值会存为变量供后续用例使用

典型场景（链式调用）：
    TC001  登录    → extract_path=accessToken  save_as=token
    TC002  查用户  → headers={"Authorization":"Bearer {{token}}"}
"""
import pytest
from utils.excel_reader import load_testcases
from utils.context import VarContext
from utils.jsonpath_util import extract_by_path

_excel_cases = load_testcases("login_cases.xlsx")
_ids = [f"{c['case_id']}-{c['description']}" for c in _excel_cases]


class TestFromExcel:
    """Excel 数据驱动测试（支持变量传递）"""

    @pytest.fixture(scope="class")
    def ctx(self):
        """跨用例共享的变量上下文"""
        c = VarContext()
        yield c
        c.clear()

    @pytest.mark.parametrize("case", _excel_cases, ids=_ids)
    def test_by_excel(self, client, ctx, case):
        """按 Excel 中定义的参数执行接口测试"""
        # 1. 替换 body / headers / path 中的 {{变量}} 占位符
        path = ctx.substitute(case["path"])
        headers = ctx.substitute(case["headers"])
        body = ctx.substitute(case["body"])

        # 2. 发送请求
        rsp = client.request(
            method=case["method"],
            path=path,
            headers=headers,
            json=body,
        )

        # 3. 断言状态码
        assert rsp.status_code == case["expected_status"], (
            f"[{case['case_id']}] 状态码不符: "
            f"期望 {case['expected_status']}, 实际 {rsp.status_code}"
        )

        # 4. 断言响应内容
        resp_text = rsp.text
        for keyword in case["expected_contains"]:
            assert keyword in resp_text, (
                f"[{case['case_id']}] 响应中缺少关键字: '{keyword}'"
            )

        # 5. 提取变量（如果配置了 extract_path + save_as）
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
