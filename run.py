#!/usr/bin/env python3
"""
一键运行自动化测试并生成 HTML 报告。

用法:
    python run.py                  # 跑全部用例
    python run.py -m smoke         # 只跑冒烟测试
    python run.py -k "login"       # 按关键字筛选
"""

import subprocess
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(PROJECT_ROOT, "reports")

os.makedirs(REPORT_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = os.path.join(REPORT_DIR, f"report_{timestamp}.html")

# 透传额外参数给 pytest
extra_args = sys.argv[1:] if len(sys.argv) > 1 else []

cmd = [
    sys.executable, "-m", "pytest",
    "-v",
    "--tb=short",
    f"--html={report_path}",
    "--self-contained-html",
    f"--css={os.path.join(PROJECT_ROOT, 'report_style.css')}",
    *extra_args,
]

print(f"{'=' * 60}")
print(f"  自动化测试框架")
print(f"{'=' * 60}")
print(f"报告路径: file://{report_path}")
print()

result = subprocess.run(cmd, cwd=PROJECT_ROOT)

# macOS 自动打开报告
if sys.platform == "darwin" and result.returncode in (0, 1):
    subprocess.run(["open", report_path])

sys.exit(result.returncode)
