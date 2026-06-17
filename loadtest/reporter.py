"""
压测结果可视化：生成图表 PNG + HTML 汇总页。
"""

import os
import time
from datetime import datetime
from .runner import LoadTestResult

import matplotlib
matplotlib.use("Agg")  # 非交互式后端，无需 GUI
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 中文字体设置
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")


def generate_report(result: LoadTestResult, title: str = "接口压测报告") -> str:
    """
    生成完整报告：4 张图表 + 1 个 HTML 汇总页。

    Returns: HTML 报告文件路径
    """
    os.makedirs(_REPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成 4 张图表
    chart_latency_dist = _chart_latency_distribution(result, timestamp)
    chart_latency_scatter = _chart_latency_scatter(result, timestamp)
    chart_status_pie = _chart_status_pie(result, timestamp)
    chart_percentiles = _chart_percentiles_bar(result, timestamp)

    # 生成 HTML
    html_path = os.path.join(_REPORT_DIR, f"loadtest_report_{timestamp}.html")
    _generate_html(result, title, timestamp, html_path,
                   chart_latency_dist, chart_latency_scatter,
                   chart_status_pie, chart_percentiles)

    return html_path


# ═══════════════════════════════════════════════
# 图表 1: 响应时间分布直方图
# ═══════════════════════════════════════════════

def _chart_latency_distribution(result: LoadTestResult, ts: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(result.latencies, bins=40, color="#3498db", edgecolor="#fff", alpha=0.85)
    ax.axvline(result.avg_latency, color="#e74c3c", linestyle="--", linewidth=2,
               label=f"Avg: {result.avg_latency:.0f}ms")
    ax.axvline(result.percentile(90), color="#f39c12", linestyle="--", linewidth=2,
               label=f"P90: {result.percentile(90):.0f}ms")
    ax.set_xlabel("Response Time (ms)")
    ax.set_ylabel("Count")
    ax.set_title("Response Time Distribution")
    ax.legend()
    path = os.path.join(_REPORT_DIR, f"latency_dist_{ts}.png")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return os.path.basename(path)


# ═══════════════════════════════════════════════
# 图表 2: 响应时间时序散点图
# ═══════════════════════════════════════════════

def _chart_latency_scatter(result: LoadTestResult, ts: str) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(result.timestamps, result.latencies, alpha=0.5, s=10,
               c="#3498db", edgecolors="none")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title("Response Time Over Time")
    ax.axhline(result.avg_latency, color="#e74c3c", linestyle="--",
               label=f"Avg: {result.avg_latency:.0f}ms")
    ax.legend()
    path = os.path.join(_REPORT_DIR, f"latency_scatter_{ts}.png")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return os.path.basename(path)


# ═══════════════════════════════════════════════
# 图表 3: 成功/失败饼图
# ═══════════════════════════════════════════════

def _chart_status_pie(result: LoadTestResult, ts: str) -> str:
    fig, ax = plt.subplots(figsize=(6, 6))
    labels = [f"Success ({result.success_count})", f"Failure ({result.failure_count})"]
    sizes = [result.success_count, result.failure_count]
    colors = ["#27ae60", "#e74c3c"]
    explode = (0, 0.05) if result.failure_count > 0 else (0, 0)

    ax.pie(sizes, explode=explode, labels=labels, colors=colors,
           autopct="%1.1f%%", startangle=90, textprops={"fontsize": 13})
    ax.set_title(f"Success Rate: {result.success_rate:.1f}%")
    path = os.path.join(_REPORT_DIR, f"status_pie_{ts}.png")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return os.path.basename(path)


# ═══════════════════════════════════════════════
# 图表 4: 分位数柱状图
# ═══════════════════════════════════════════════

def _chart_percentiles_bar(result: LoadTestResult, ts: str) -> str:
    percentiles = [50, 75, 90, 95, 99]
    values = [result.percentile(p) for p in percentiles]
    labels = [f"P{p}" for p in percentiles]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=["#2ecc71", "#3498db", "#f39c12", "#e67e22", "#e74c3c"])
    ax.set_ylabel("Response Time (ms)")
    ax.set_title("Response Time Percentiles")

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                f"{val:.0f}ms", ha="center", fontsize=10)

    path = os.path.join(_REPORT_DIR, f"percentiles_{ts}.png")
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return os.path.basename(path)


# ═══════════════════════════════════════════════
# HTML 汇总页
# ═══════════════════════════════════════════════

def _generate_html(result, title, ts, html_path, *chart_files):
    error_rows = ""
    for e in result.errors[:20]:
        error_rows += f"<tr><td class='error-msg'>{e}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f6fa; padding: 24px; }}
  h1 {{ background: linear-gradient(135deg, #2c3e50, #e74c3c); color: #fff; padding: 24px; border-radius: 8px; margin-bottom: 24px; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: #fff; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .card .value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
  .card .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
  .card.success .value {{ color: #27ae60; }}
  .card.failure .value {{ color: #e74c3c; }}
  .chart-section {{ margin-bottom: 24px; }}
  .chart-section h2 {{ margin-bottom: 12px; color: #2c3e50; border-left: 4px solid #3498db; padding-left: 12px; }}
  .chart-section img {{ width: 100%; max-width: 900px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .errors {{ background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  .errors h2 {{ color: #e74c3c; margin-bottom: 12px; }}
  .errors table {{ width: 100%; border-collapse: collapse; }}
  .errors td {{ padding: 6px; border-bottom: 1px solid #eee; font-size: 12px; font-family: Menlo, monospace; }}
  .error-msg {{ color: #e74c3c; word-break: break-all; }}
</style>
</head>
<body>
<h1>{title}</h1>

<div class="summary">
  <div class="card">
    <div class="value">{result.total_requests}</div>
    <div class="label">Total Requests</div>
  </div>
  <div class="card success">
    <div class="value">{result.success_rate:.1f}%</div>
    <div class="label">Success Rate</div>
  </div>
  <div class="card">
    <div class="value">{result.rps:.1f}</div>
    <div class="label">Throughput (RPS)</div>
  </div>
  <div class="card">
    <div class="value">{result.avg_latency:.0f}ms</div>
    <div class="label">Avg Latency</div>
  </div>
  <div class="card">
    <div class="value">{result.min_latency:.0f}ms</div>
    <div class="label">Min Latency</div>
  </div>
  <div class="card">
    <div class="value">{result.max_latency:.0f}ms</div>
    <div class="label">Max Latency</div>
  </div>
  <div class="card">
    <div class="value">{result.percentile(50):.0f}ms</div>
    <div class="label">P50</div>
  </div>
  <div class="card">
    <div class="value">{result.percentile(90):.0f}ms</div>
    <div class="label">P90</div>
  </div>
  <div class="card">
    <div class="value">{result.percentile(95):.0f}ms</div>
    <div class="label">P95</div>
  </div>
  <div class="card">
    <div class="value">{result.percentile(99):.0f}ms</div>
    <div class="label">P99</div>
  </div>
  <div class="card">
    <div class="value">{result.total_duration:.1f}s</div>
    <div class="label">Duration</div>
  </div>
</div>

<div class="chart-section">
  <h2>Response Time Distribution</h2>
  <img src="{chart_files[0]}" alt="Latency Distribution">
</div>

<div class="chart-section">
  <h2>Response Time Over Time</h2>
  <img src="{chart_files[1]}" alt="Latency Scatter">
</div>

<div class="chart-section">
  <h2>Success / Failure</h2>
  <img src="{chart_files[2]}" alt="Status Pie">
</div>

<div class="chart-section">
  <h2>Latency Percentiles</h2>
  <img src="{chart_files[3]}" alt="Percentiles Bar">
</div>

<div class="errors">
  <h2>Errors ({len(result.errors)})</h2>
  <table>{error_rows}</table>
  {f"<p style='color:#888;margin-top:8px'>... 仅展示前 20 条</p>" if len(result.errors) > 20 else ""}
</div>

</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
