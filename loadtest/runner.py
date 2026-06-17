"""
多线程压测引擎。

使用 ThreadPoolExecutor 并发发送 HTTP 请求，收集每次请求的：
    - 响应时间 (ms)
    - HTTP 状态码
    - 成功/失败
    - 时间戳
"""

import time
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
import requests


class LoadTestResult:
    """压测结果容器"""

    def __init__(self):
        self.latencies: List[float] = []        # 每次请求的响应时间 (ms)
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.success_count = 0
        self.failure_count = 0
        self.errors: List[str] = []             # 错误信息
        self.timestamps: List[float] = []        # 每个请求的开始时间（相对时间）
        self.total_duration: float = 0            # 总耗时 (s)
        self.total_requests: int = 0
        self.start_time: float = 0

    @property
    def success_rate(self) -> float:
        if not self.total_requests:
            return 0
        return self.success_count / self.total_requests * 100

    @property
    def avg_latency(self) -> float:
        if not self.latencies:
            return 0
        return sum(self.latencies) / len(self.latencies)

    @property
    def min_latency(self) -> float:
        return min(self.latencies) if self.latencies else 0

    @property
    def max_latency(self) -> float:
        return max(self.latencies) if self.latencies else 0

    @property
    def rps(self) -> float:
        if not self.total_duration:
            return 0
        return self.total_requests / self.total_duration

    def percentile(self, p: float) -> float:
        """计算第 p 百分位响应时间，p 取值 0~100"""
        if not self.latencies:
            return 0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        idx = min(idx, len(sorted_lat) - 1)
        return sorted_lat[idx]


class LoadTestRunner:
    """
    多线程压测执行器。

    用法:
        runner = LoadTestRunner(url="https://dummyjson.com/auth/login",
                                method="POST",
                                json={"username":"emilys","password":"emilyspass"})
        result = runner.run(num_threads=10, total_requests=100, ramp_up=2)
    """

    def __init__(self, url: str, method: str = "GET",
                 headers: dict = None, json: dict = None, data: dict = None,
                 timeout: int = 30):
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.json = json
        self.data = data
        self.timeout = timeout

    def run(self, num_threads: int = 5, total_requests: int = 50,
            ramp_up: float = 0) -> LoadTestResult:
        """
        执行压测。

        Args:
            num_threads:   并发线程数
            total_requests: 总请求数
            ramp_up:        线程启动间隔（秒），0 表示同时启动
        """
        result = LoadTestResult()
        result.total_requests = total_requests
        result.start_time = time.time()

        # 计算每个线程分配的请求数
        per_thread = total_requests // num_threads
        remainders = total_requests % num_threads

        lock = threading.Lock()
        done_count = [0]  # 用 list 包装以在线程间共享

        def worker(thread_id: int, num: int):
            """单个线程的执行逻辑"""
            for i in range(num):
                t_start = time.time()
                try:
                    rsp = requests.request(
                        method=self.method, url=self.url,
                        headers=self.headers, json=self.json, data=self.data,
                        timeout=self.timeout,
                    )
                    elapsed = (time.time() - t_start) * 1000
                    with lock:
                        result.latencies.append(elapsed)
                        result.status_codes[rsp.status_code] += 1
                        result.timestamps.append(time.time() - result.start_time)
                        if 200 <= rsp.status_code < 500:
                            result.success_count += 1
                        else:
                            result.failure_count += 1
                            result.errors.append(
                                f"[thread-{thread_id}] status={rsp.status_code} "
                                f"body={rsp.text[:200]}"
                            )
                except Exception as e:
                    elapsed = (time.time() - t_start) * 1000
                    with lock:
                        result.latencies.append(elapsed)
                        result.timestamps.append(time.time() - result.start_time)
                        result.failure_count += 1
                        result.errors.append(f"[thread-{thread_id}] {type(e).__name__}: {e}")

                with lock:
                    done_count[0] += 1

        # 启动线程
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for tid in range(num_threads):
                n = per_thread + (1 if tid < remainders else 0)
                if n == 0:
                    continue
                futures.append(executor.submit(worker, tid, n))
                if ramp_up > 0 and tid < num_threads - 1:
                    time.sleep(ramp_up / num_threads)

            for f in as_completed(futures):
                f.result()  # 抛出线程中的异常（如果有）

        result.total_duration = time.time() - result.start_time
        return result
