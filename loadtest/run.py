#!/usr/bin/env python3
"""
多线程接口压测工具 - CLI 入口。

用法:
    # 对登录接口压测：10 线程，100 次请求
    python -m loadtest.run --url https://dummyjson.com/auth/login \
        --method POST --body '{"username":"emilys","password":"emilyspass"}' \
        --threads 10 --requests 100

    # 快速冒烟：5 线程 30 次请求
    python -m loadtest.run --url https://dummyjson.com/auth/login \
        --method POST --body '{"username":"emilys","password":"emilyspass"}' \
        --threads 5 --requests 30

    # 递增启动（ramp-up 2 秒）
    python -m loadtest.run --url https://dummyjson.com/auth/login \
        --method POST --body '{"username":"emilys","password":"emilyspass"}' \
        --threads 20 --requests 200 --ramp-up 2
"""

import argparse
import json
import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loadtest.runner import LoadTestRunner
from loadtest.reporter import generate_report


def main():
    parser = argparse.ArgumentParser(
        description="多线程接口压测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m loadtest.run --url https://dummyjson.com/auth/login \\
      --method POST --body '{"username":"emilys","password":"emilyspass"}' \\
      --threads 10 --requests 100
        """,
    )
    parser.add_argument("--url", required=True, help="目标 URL")
    parser.add_argument("--method", default="GET", help="HTTP 方法 (默认 GET)")
    parser.add_argument("--body", default=None, help="请求体 JSON 字符串")
    parser.add_argument("--headers", default=None, help="请求头 JSON 字符串")
    parser.add_argument("--threads", type=int, default=5, help="并发线程数 (默认 5)")
    parser.add_argument("--requests", type=int, default=50, help="总请求数 (默认 50)")
    parser.add_argument("--ramp-up", type=float, default=0,
                        help="线程递增启动间隔秒数 (默认 0，同时启动)")
    parser.add_argument("--timeout", type=int, default=30, help="单次请求超时秒数 (默认 30)")

    args = parser.parse_args()

    # 解析 JSON 参数
    body = json.loads(args.body) if args.body else None
    headers = json.loads(args.headers) if args.headers else None

    # 执行压测
    runner = LoadTestRunner(
        url=args.url, method=args.method,
        headers=headers, json=body,
        timeout=args.timeout,
    )

    print(f"{'=' * 60}")
    print(f"  多线程压测")
    print(f"{'=' * 60}")
    print(f"URL:      {args.url}")
    print(f"Method:   {args.method}")
    print(f"Threads:  {args.threads}")
    print(f"Requests: {args.requests}")
    print(f"Ramp-up:  {args.ramp_up}s")
    print(f"{'=' * 60}")
    print("Running...")

    result = runner.run(
        num_threads=args.threads,
        total_requests=args.requests,
        ramp_up=args.ramp_up,
    )

    # 终端输出摘要
    print()
    print(f"{'=' * 60}")
    print(f"  压测结果")
    print(f"{'=' * 60}")
    print(f"总请求:     {result.total_requests}")
    print(f"成功:       {result.success_count} ({result.success_rate:.1f}%)")
    print(f"失败:       {result.failure_count}")
    print(f"总耗时:     {result.total_duration:.2f}s")
    print(f"吞吐量:     {result.rps:.1f} req/s")
    print(f"平均延迟:   {result.avg_latency:.0f}ms")
    print(f"最小延迟:   {result.min_latency:.0f}ms")
    print(f"最大延迟:   {result.max_latency:.0f}ms")
    print(f"P50:        {result.percentile(50):.0f}ms")
    print(f"P90:        {result.percentile(90):.0f}ms")
    print(f"P95:        {result.percentile(95):.0f}ms")
    print(f"P99:        {result.percentile(99):.0f}ms")
    print(f"{'=' * 60}")

    # 生成图表报告
    html_path = generate_report(result, title=f"压测报告 - {args.url}")
    print(f"\n>>> 报告已生成: file://{html_path}")


if __name__ == "__main__":
    main()
