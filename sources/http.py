"""client HTTP ساده با backoff روی 429."""

from __future__ import annotations

import time

import requests


class HttpError(Exception):
    """خطای HTTP غیر-2xx (یا غیرقابل انتقال)."""

    def __init__(self, status: int, text: str):
        self.status = status
        self.text = text
        super().__init__(f"HTTP {status}: {text}")


def http_get(
    url: str,
    *,
    headers: dict | None = None,
    params: dict | None = None,
    timeout: float = 15.0,
    max_retries: int = 4,
    backoff_base: float = 6.0,
) -> requests.Response:
    """GET با retry: روی 429 مقدار retry_after را بخوان و صبر کن."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        except requests.RequestException as exc:
            raise HttpError(0, str(exc)) from exc
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "")
            try:
                wait = float(retry_after)
            except ValueError:
                wait = backoff_base * (attempt + 1)
            time.sleep(min(wait, 30.0))
            continue
        if resp.status_code >= 400:
            raise HttpError(resp.status_code, resp.text[:300])
        return resp
    raise HttpError(429, "هنوز rate-limit (حداکثر retry)")
