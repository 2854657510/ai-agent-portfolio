
import json
import os
from typing import Iterator

import requests

DEFAULT_BASE_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

class BackendDown(Exception):
    """连不上后端 """
class BackendError(Exception):
    """后端返回了错误状态码"""
    def __init__(self, status_code: int, detail):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}")
# 检测后端状态
def check_health(base_url: str, timeout: int = 5) -> bool:
    try:
        r = requests.get(f"{base_url.rstrip('/')}/health", timeout=timeout)
        return r.status_code == 200 and r.json().get("status") is True
    except Exception:
        return False
# 调接口
def extract(base_url: str, document: str, timeout: int = 120) -> dict:
    url = f"{base_url.rstrip('/')}/api/extract"
    try:
        r = requests.post(url, json={"document": document}, timeout=timeout)
    except requests.exceptions.ConnectionError as e:
        raise BackendDown(str(e)) from e
    except requests.exceptions.Timeout as e:
        raise BackendDown(f"请求超时（{timeout} 秒）") from e
    if r.status_code == 200:
        return r.json()
    # 422降级
    try:
        detail = r.json().get("detail", r.text)
    except Exception:
        detail = r.text
    raise BackendError(r.status_code, detail)

# 流式输出接口
def chat_stream(base_url: str, question: str, timeout: int = 120) -> Iterator[tuple]:
    url = f"{base_url.rstrip('/')}/api/chat/stream"
    try:
        with requests.post(
            url, json={"question": question}, stream=True, timeout=timeout
        ) as r:
            if r.status_code != 200:
                raise BackendError(r.status_code, r.text[:300])

            event_name = None
            for raw_line in r.iter_lines(decode_unicode=True):
                if raw_line is None:
                    continue
                line = raw_line.strip()

                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    payload = line.split(":", 1)[1].strip()
                    try:
                        data = json.loads(payload)
                    except json.JSONDecodeError:
                        data = {"raw": payload}
                    yield event_name or "message", data
                    event_name = None
    except requests.exceptions.ConnectionError as e:
        raise BackendDown(str(e)) from e
    except requests.exceptions.Timeout as e:
        raise BackendDown("流式请求超时") from e
