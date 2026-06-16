import json
import requests
from config.settings import BASE_URL, TIMEOUT
from utils.logger import logger


class HttpClient:
    """带自动日志的 HTTP 客户端。每次请求/响应自动记录到 HTML 报告的 Details 区。"""

    def __init__(self, base_url: str = BASE_URL, timeout: int = TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.hooks["response"].append(self._log_response)

    # ── 日志 hook ──

    def _log_response(self, resp, *args, **kwargs):
        req = resp.request
        lines = [
            "=" * 60,
            ">>> REQUEST",
            f"    Method : {req.method}",
            f"    URL    : {req.url}",
        ]
        if req.body:
            body = req.body.decode("utf-8") if isinstance(req.body, bytes) else req.body
            try:
                body = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
            except Exception:
                pass
            lines.append(f"    Body   : {body}")

        lines.append("<<< RESPONSE")
        lines.append(f"    Status : {resp.status_code} {resp.reason}")
        lines.append(f"    Time   : {resp.elapsed.total_seconds():.3f}s")
        try:
            resp_body = resp.json()
            for key in ("accessToken", "refreshToken", "token"):
                if key in resp_body and isinstance(resp_body[key], str) and len(resp_body[key]) > 80:
                    resp_body[key] = resp_body[key][:80] + "...(truncated)"
            lines.append(f"    Body   : {json.dumps(resp_body, ensure_ascii=False, indent=2)}")
        except Exception:
            lines.append(f"    Body   : {resp.text[:800]}")
        lines.append("=" * 60)

        logger.info("\n".join(lines))

    # ── HTTP 方法 ──

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def request(self, method: str, path: str, **kwargs):
        """通用 HTTP 请求，供数据驱动用例调用。"""
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, self._url(path), **kwargs)

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.request("DELETE", path, **kwargs)

    def close(self):
        self.session.close()
