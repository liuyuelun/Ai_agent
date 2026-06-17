"""
JSON 路径提取工具（dot-notation）。

支持格式:
    accessToken          → {"accessToken": "abc"}              → "abc"
    data.token           → {"data": {"token": "abc"}}          → "abc"
    users.0.name         → {"users": [{"name": "John"}]}       → "John"
    items.1.sub.value    → 多层嵌套 + 数组混合
"""

from typing import Any


def extract_by_path(data: Any, path: str) -> Any:
    """
    按点号分隔的路径从 JSON 对象中提取值。

    Raises:
        KeyError: 路径不存在
        IndexError: 数组索引越界
        TypeError: 对非 dict/list 类型做深层访问
    """
    if not path or not path.strip():
        return None

    current = data
    for part in path.split("."):
        part = part.strip()

        if isinstance(current, dict):
            if part not in current:
                raise KeyError(
                    f"路径 '{path}' 提取失败: 字段 '{part}' 不存在，"
                    f"当前对象字段: {list(current.keys())[:10]}"
                )
            current = current[part]

        elif isinstance(current, list):
            try:
                idx = int(part)
            except ValueError:
                raise TypeError(
                    f"路径 '{path}' 提取失败: '{part}' 不是有效数字，"
                    f"但当前值是列表（共 {len(current)} 项）"
                )
            if idx < 0 or idx >= len(current):
                raise IndexError(
                    f"路径 '{path}' 提取失败: 索引 {idx} 越界，"
                    f"列表共 {len(current)} 项"
                )
            current = current[idx]

        else:
            raise TypeError(
                f"路径 '{path}' 提取失败: 无法从 {type(current).__name__} 类型继续取 '{part}'"
            )

    return current
