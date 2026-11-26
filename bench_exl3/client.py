"""OpenAI-compatible streaming client for TabbyAPI, standard library only.

Timings use time.perf_counter. Token counts prefer the SSE usage payload.
If the server omits usage, completion tokens fall back to the number of
non-empty content deltas and usage_source is chunk_count_fallback.
Connection failures, timeouts, non-200 responses, and empty or malformed
streams raise BenchmarkEndpointError. Nothing here fabricates a successful sample.
"""

from __future__ import annotations

import http.client
import json
import time
from dataclasses import dataclass
from urllib.parse import urlparse


class BenchmarkEndpointError(Exception):
    """A live endpoint could not produce a usable streaming measurement."""


@dataclass(frozen=True)
class StreamMetrics:
    endpoint: str
    ttft_ms: float | None
    e2e_ms: float
    prompt_tokens: int | None
    completion_tokens: int
    usage_source: str
    decode_tps: float
    chunk_count: int


def compute_decode_tps(completion_tokens: int, ttft_ms: float | None, e2e_ms: float) -> float:
    """Tokens per second over the decode window.

    When more than one completion token arrived and the stream continued after
    the first content delta, later tokens are `(n - 1) / decode_seconds`.
    Otherwise the rate is `n / e2e_seconds`.
    """

    if completion_tokens < 0:
        raise BenchmarkEndpointError("negative completion_tokens")
    if e2e_ms <= 0:
        raise BenchmarkEndpointError("non-positive end-to-end duration")
    if ttft_ms is not None and completion_tokens > 1 and e2e_ms > ttft_ms:
        return (completion_tokens - 1) / ((e2e_ms - ttft_ms) / 1000.0)
    return completion_tokens / (e2e_ms / 1000.0)


def _split_endpoint(base_url: str, suffix: str) -> tuple[str, str, int, str]:
    parsed = urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BenchmarkEndpointError(f"endpoint must be an absolute http(s) URL with a host: {base_url}")
    if parsed.port is None:
        port = 443 if parsed.scheme == "https" else 80
    else:
        port = parsed.port
    path = parsed.path.rstrip("/") + (suffix if suffix.startswith("/") else "/" + suffix)
    return parsed.scheme, parsed.hostname, port, path


def _connection(scheme: str, host: str, port: int, timeout: float) -> http.client.HTTPConnection:
    if scheme == "https":
        return http.client.HTTPSConnection(host, port, timeout=timeout)
    return http.client.HTTPConnection(host, port, timeout=timeout)


def _as_int_token(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkEndpointError(f"malformed usage.{field}")
    if isinstance(value, float) and not value.is_integer():
        raise BenchmarkEndpointError(f"malformed usage.{field}")
    number = int(value)
    if number < 0:
        raise BenchmarkEndpointError(f"negative usage.{field}")
    return number


def _content_delta(payload: dict) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    choice = choices[0]
    if not isinstance(choice, dict):
        return ""
    delta = choice.get("delta")
    if not isinstance(delta, dict):
        return ""
    content = delta.get("content")
    if isinstance(content, str) and content != "":
        return content
    return ""


def _read_error_body(resp: http.client.HTTPResponse) -> str:
    try:
        raw = resp.read(4096)
    except (TimeoutError, OSError, http.client.HTTPException):
        return ""
    return raw.decode("utf-8", errors="replace")[:500]


def preflight(base_url: str, timeout: float, expected_model: str) -> list[str]:
    """GET {base_url}/models and require `expected_model` to be loaded.

    A refused connection, timeout, non-200 status, or model list that does not
    contain the requested preset aborts the run before any matrix row is written.
    """

    if timeout <= 0:
        raise BenchmarkEndpointError("timeout must be positive")
    scheme, host, port, path = _split_endpoint(base_url, "/models")
    conn = _connection(scheme, host, port, timeout)
    try:
        try:
            conn.request(
                "GET",
                path,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Connection": "close",
                    "User-Agent": "bench_exl3",
                },
            )
            resp = conn.getresponse()
        except (TimeoutError, OSError, http.client.HTTPException) as exc:
            raise BenchmarkEndpointError(f"endpoint unreachable: {base_url}: {exc}") from exc
        try:
            raw = resp.read()
        except (TimeoutError, OSError, http.client.HTTPException) as exc:
            raise BenchmarkEndpointError(f"failed reading /models from {base_url}: {exc}") from exc
        body = raw.decode("utf-8", errors="replace")
        if resp.status != 200:
            raise BenchmarkEndpointError(f"{base_url}/models returned HTTP {resp.status}: {body[:500]}")
        try:
            payload = json.loads(body) if body else None
        except json.JSONDecodeError as exc:
            raise BenchmarkEndpointError(f"malformed /models response from {base_url}: {exc}") from exc
    finally:
        conn.close()
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise BenchmarkEndpointError(f"malformed /models response from {base_url}: missing data list")
    ids: list[str] = []
    for item in payload["data"]:
        if isinstance(item, dict) and item.get("id"):
            ids.append(str(item["id"]))
    if expected_model not in ids:
        loaded = ", ".join(ids) if ids else "(none)"
        raise BenchmarkEndpointError(
            f"{base_url} does not list model {expected_model!r}; loaded ids: {loaded}. "
            "Refusing to record benchmark rows for a model the endpoint is not serving."
        )
    return ids


def stream_chat(
    base_url: str,
    *,
    model: str,
    prompt: str,
    output_tokens: int,
    timeout: float,
    temperature: float = 0.0,
) -> StreamMetrics:
    """POST {base_url}/chat/completions and time the SSE stream."""

    if timeout <= 0:
        raise BenchmarkEndpointError("timeout must be positive")
    if isinstance(output_tokens, bool) or not isinstance(output_tokens, int) or output_tokens < 1:
        raise BenchmarkEndpointError("output_tokens must be a positive integer")
    scheme, host, port, path = _split_endpoint(base_url, "/chat/completions")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "stream_options": {"include_usage": True},
        "temperature": temperature,
        "max_tokens": output_tokens,
        # TabbyAPI: ban EOS/stop until output_tokens so each cell decodes the target length.
        "min_tokens": output_tokens,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Accept-Encoding": "identity",
        "Connection": "close",
        "User-Agent": "bench_exl3",
    }
    conn = _connection(scheme, host, port, timeout)
    ttft_ms: float | None = None
    chunk_count = 0
    usage: dict | None = None
    saw_done = False
    saw_event = False
    try:
        t0 = time.perf_counter()
        try:
            conn.request("POST", path, body=body, headers=headers)
            resp = conn.getresponse()
        except (TimeoutError, OSError, http.client.HTTPException) as exc:
            raise BenchmarkEndpointError(f"endpoint unreachable: {base_url}: {exc}") from exc
        if resp.status != 200:
            detail = _read_error_body(resp)
            raise BenchmarkEndpointError(f"{base_url} returned HTTP {resp.status}: {detail}")
        while True:
            try:
                raw = resp.readline()
            except (TimeoutError, OSError, http.client.HTTPException) as exc:
                raise BenchmarkEndpointError(f"failed reading SSE from {base_url}: {exc}") from exc
            if raw == b"":
                break
            line = raw.decode("utf-8", errors="replace").lstrip("\ufeff").strip()
            if not line or line.startswith(":"):
                continue
            if not line.startswith("data:"):
                continue
            data = line[len("data:") :].lstrip()
            if not data:
                continue
            saw_event = True
            if data == "[DONE]":
                saw_done = True
                break
            try:
                event = json.loads(data)
            except json.JSONDecodeError as exc:
                raise BenchmarkEndpointError(f"malformed SSE payload from {base_url}: {exc}") from exc
            if not isinstance(event, dict):
                raise BenchmarkEndpointError(f"malformed SSE payload from {base_url}: expected a JSON object")
            if event.get("error"):
                raise BenchmarkEndpointError(f"stream error from {base_url}: {event['error']}")
            text = _content_delta(event)
            if text:
                chunk_count += 1
                if ttft_ms is None:
                    ttft_ms = (time.perf_counter() - t0) * 1000.0
            raw_usage = event.get("usage")
            if isinstance(raw_usage, dict):
                usage = raw_usage
        e2e_ms = (time.perf_counter() - t0) * 1000.0
    finally:
        conn.close()

    if not saw_event:
        raise BenchmarkEndpointError(f"empty SSE stream from {base_url}")

    prompt_tokens: int | None = None
    if usage is not None and "prompt_tokens" in usage and usage.get("prompt_tokens") is not None:
        prompt_tokens = _as_int_token(usage.get("prompt_tokens"), "prompt_tokens")

    if usage is not None and "completion_tokens" in usage and usage.get("completion_tokens") is not None:
        completion_tokens = _as_int_token(usage.get("completion_tokens"), "completion_tokens")
        usage_source = "server_usage"
    else:
        completion_tokens = chunk_count
        usage_source = "chunk_count_fallback"

    if completion_tokens == 0:
        done = "after [DONE]" if saw_done else "when the stream closed"
        raise BenchmarkEndpointError(f"empty completion from {base_url} {done}")

    decode_tps = compute_decode_tps(completion_tokens, ttft_ms, e2e_ms)
    return StreamMetrics(
        endpoint=base_url,
        ttft_ms=ttft_ms,
        e2e_ms=e2e_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        usage_source=usage_source,
        decode_tps=decode_tps,
        chunk_count=chunk_count,
    )
