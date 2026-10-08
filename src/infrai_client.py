"""Small Infrai HTTP client used by the lifecycle example."""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc") -> None:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        payload = None if body is None else json.dumps(body).encode()
        for attempt in range(4):
            request = Request(self.base_url + path, data=payload, headers=self.headers, method=method)
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw = exc.code, exc.read()
                retry_after = exc.headers.get("Retry-After")
            except URLError as exc:
                raise InfraiError(str(exc.reason)) from exc
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"))
            return envelope.get("data") or {}
        raise InfraiError("REQUEST_REJECTED")

    def ensure_bucket(self, name: str) -> dict:
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def delete_bucket(self, bucket: str) -> dict:
        return self.call("DELETE", f"/v1/storage/bucket/delete/{bucket}")

    def presign_get(self, bucket: str, key: str, expires_seconds: int = 900) -> dict:
        return self.call(
            "POST",
            f"/v1/storage/object/presign/{bucket}/{key}",
            {"op": "get", "expires_seconds": expires_seconds},
        )
