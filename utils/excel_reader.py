"""
从 Excel 文件读取测试用例。

Excel 表头定义：
    case_id | description | method | path | headers | body | expected_status | expected_contains | category

- headers: JSON 字符串，如 {"Authorization":"Bearer xxx"}
- body: JSON 字符串，请求体
- expected_contains: 期望响应中包含的字符串（多个以 ;; 分隔表示 AND 关系）
"""

import json
import os
from typing import List, Dict, Any
import openpyxl

_EXCEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "testdata")


def load_testcases(filename: str, sheet_name: str = None) -> List[Dict[str, Any]]:
    """
    读取 Excel 中的测试用例，返回 pytest parametrize 可用的列表。

    返回每条记录为一个 dict：
        {
            "case_id": "TC001",
            "description": "正常登录",
            "method": "POST",
            "path": "/auth/login",
            "headers": {},
            "body": {...},
            "expected_status": 200,
            "expected_contains": ["accessToken"],
            "category": "smoke",
        }
    """
    filepath = os.path.join(_EXCEL_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Excel 文件不存在: {filepath}")

    wb = openpyxl.load_workbook(filepath)
    ws = wb[sheet_name] if sheet_name else wb.active

    rows = list(ws.iter_rows(min_row=2, values_only=True))  # 跳过表头
    headers_row = [cell.value for cell in ws[1]]

    cases = []
    for row in rows:
        if not row[0]:  # 跳过空行（case_id 为空）
            continue

        case = dict(zip(headers_row, row))

        # 类型转换
        case["expected_status"] = int(case.get("expected_status", 200))
        case["method"] = (case.get("method") or "GET").upper()

        # 解析 headers JSON
        raw_headers = case.get("headers")
        case["headers"] = json.loads(raw_headers) if raw_headers else {}

        # 解析 body JSON
        raw_body = case.get("body")
        case["body"] = json.loads(raw_body) if raw_body else None

        # 解析 expected_contains（;; 分隔多个期望值）
        raw_contains = case.get("expected_contains") or ""
        case["expected_contains"] = [s.strip() for s in raw_contains.split(";;") if s.strip()]

        cases.append(case)

    wb.close()
    return cases
