"""
测试用例变量上下文，支持跨用例传递数据。

用法:
    from utils.context import VarContext

    ctx = VarContext()
    ctx.set("token", "eyJhbGciOi...")
    token = ctx.get("token")  # "eyJhbGciOi..."

    # 在字符串中替换变量
    body = ctx.substitute('{"token":"{{token}}"}')  # → '{"token":"eyJhbGciOi..."}'
"""

import json
import re
from typing import Any

_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")


class VarContext:
    """跨用例共享的变量容器（非线程安全，用例顺序执行无需锁）"""

    __test__ = False  # 避免 pytest 误收集

    def __init__(self):
        self._vars: dict[str, Any] = {}

    def set(self, key: str, value: Any):
        self._vars[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._vars.get(key, default)

    def clear(self):
        self._vars.clear()

    def substitute(self, raw: Any) -> Any:
        """
        递归替换对象中的 {{var}} 占位符。
        支持 str / dict / list / 其他基本类型。
        """
        if isinstance(raw, str):
            def _replacer(m):
                var_name = m.group(1)
                val = self._vars.get(var_name)
                if val is None:
                    raise KeyError(
                        f"变量 '{{{{{var_name}}}}}' 未定义，请检查前置用例是否设置了 save_as='{var_name}'"
                    )
                # 如果是字符串类型，直接替换；否则保留原类型标记以便后续 JSON 序列化
                return val if isinstance(val, str) else str(val)
            return _VAR_PATTERN.sub(_replacer, raw)

        elif isinstance(raw, dict):
            return {k: self.substitute(v) for k, v in raw.items()}

        elif isinstance(raw, list):
            return [self.substitute(item) for item in raw]

        return raw
