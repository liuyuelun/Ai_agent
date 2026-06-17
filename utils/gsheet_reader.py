"""
从 Google Sheets 在线表格读取测试用例。

使用方式：
    1. 在 Google Cloud Console 创建服务账号，下载 JSON 密钥文件
    2. 将密钥文件路径设为环境变量 GOOGLE_CREDENTIALS
    3. 将服务账号邮箱添加为表格的查看者

表格格式同 Excel：
    case_id | description | method | path | headers | body
    | expected_status | expected_contains | category
    | extract_path | save_as

也支持公开只读表格（无需鉴权），通过 CSV 导出 URL 读取。
"""

import json
import csv
import os
import io
from typing import List, Dict, Any
import requests


def _parse_rows(rows: list, headers: list) -> List[Dict[str, Any]]:
    """将行列数据转为测试用例 dict 列表"""
    cases = []
    for row in rows:
        if not row or not row[0]:  # 跳过空行
            continue
        case = dict(zip(headers, row + [""] * (len(headers) - len(row))))

        case["expected_status"] = int(case.get("expected_status", 200))
        case["method"] = (case.get("method") or "GET").upper()

        raw_headers = case.get("headers")
        case["headers"] = json.loads(raw_headers) if raw_headers else {}

        raw_body = case.get("body")
        case["body"] = json.loads(raw_body) if raw_body else None

        raw_contains = case.get("expected_contains") or ""
        case["expected_contains"] = [s.strip() for s in raw_contains.split(";;") if s.strip()]

        case["extract_path"] = (case.get("extract_path") or "").strip()
        case["save_as"] = (case.get("save_as") or "").strip()

        cases.append(case)
    return cases


def load_from_csv_url(url: str) -> List[Dict[str, Any]]:
    """
    从 CSV 导出 URL 读取测试用例（适用于公开 Google Sheet）。

    用法：将 Google Sheet 发布为 CSV，传入 CSV 导出链接。
    """
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    reader = csv.reader(io.StringIO(resp.text))
    rows = list(reader)
    if not rows:
        return []
    headers = rows[0]
    return _parse_rows(rows[1:], headers)


def load_from_gspread(spreadsheet_name: str, sheet_name: str = None) -> List[Dict[str, Any]]:
    """
    通过 gspread + 服务账号读取 Google Sheet。

    需要：
    - pip install gspread oauth2client
    - 环境变量 GOOGLE_CREDENTIALS 指向服务账号 JSON 密钥
    """
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except ImportError:
        raise ImportError("需要安装: pip install gspread oauth2client")

    creds_file = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_file or not os.path.exists(creds_file):
        raise RuntimeError(
            "请设置环境变量 GOOGLE_CREDENTIALS 为服务账号 JSON 密钥文件的路径\n"
            "导出方式: export GOOGLE_CREDENTIALS=/path/to/credentials.json"
        )

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)

    sh = client.open(spreadsheet_name)
    ws = sh.worksheet(sheet_name) if sheet_name else sh.sheet1

    all_values = ws.get_all_values()
    if not all_values:
        return []
    headers = all_values[0]
    return _parse_rows(all_values[1:], headers)
