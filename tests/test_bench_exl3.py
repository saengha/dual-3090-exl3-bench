"""Live-server tests for the Dual RTX 3090 EXL3 benchmark harness.

The in-test HTTP server emits real SSE. Assertions recompute TTFT, decode TPS,
and aggregate TPS from the recorded samples. Telemetry numbers come only from
parsed nvidia-smi text or from a sampler pointed at a missing binary.
"""

from __future__ import annotations

import ast
import csv
import json
import os
import socket
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from bench_exl3.client import BenchmarkEndpointError, compute_decode_tps, stream_chat
from bench_exl3.cli import main
from bench_exl3.models import (
    DEFAULT_CONCURRENCIES,
    DEFAULT_ENDPOINTS,
    DEFAULT_MODES,
    DEFAULT_OUTPUT_LENGTHS,
    DEFAULT_PROMPT_LENGTHS,
    GEMMA_31B,
    QWEN_27B,
    build_synthetic_prompt,
    estimate_prompt_tokens,
)
from bench_exl3.report import format_metric, load_matrix, write_report
from bench_exl3.runner import joules_per_token, percentile
from bench_exl3.telemetry import GpuTelemetrySampler, empty_telemetry, parse_nvidia_smi_csv, summarize_samples

ROOT = Path(__file__).resolve().parents[1]
QWEN = QWEN_27B.name


class _ReadyHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler]) -> None:
        super().__init__(address, handler)
        self.ready = threading.Event()

    def service_actions(self) -> None:
        self.ready.set()


class SseServer:
    def __init__(
        self,
        *,
        http_status: int = 200,
        models_status: int = 200,
        chunks: int | None = None,
        usage: str = "match",
        fixed_prompt_tokens: int = 70,
        fixed_completion_tokens: int | None = None,
        malformed: bool = False,
        empty: bool = False,
        first_delay: float = 0.02,
        inter_delay: float = 0.008,
    ) -> None:
        self.http_status = http_status
        self.models_status = models_status
        self.chunks = chunks
        self.usage = usage
        self.fixed_prompt_tokens = fixed_prompt_tokens
        self.fixed_completion_tokens = fixed_completion_tokens
        self.malformed = malformed
        self.empty = empty
        self.first_delay = first_delay
        self.inter_delay = inter_delay
        self.posts = 0
        self.max_inflight = 0
        self._inflight = 0
        self.bodies: list[dict] = []
        self.lock = threading.Lock()
        self.httpd = _ReadyHTTPServer(("127.0.0.1", 0), self._handler())
        self.thread = threading.Thread(
            target=self.httpd.serve_forever,
            kwargs={"poll_interval": 0.05},
            name="bench-exl3-test-sse",
            daemon=True,
        )
        self.thread.start()
        if not self.httpd.ready.wait(3):
            self.close()
            raise RuntimeError("test SSE server did not start")

    @property
    def base_url(self) -> str:
        host, port = self.httpd.server_address
        return f"http://{host}:{port}/v1"

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        state = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def log_message(self, fmt: str, *args: object) -> None:
                return

            def _bytes(self, payload: bytes) -> None:
                try:
                    self.wfile.write(payload)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return

            def do_GET(self) -> None:  # noqa: N802
                path = self.path.split("?", 1)[0]
                if path != "/v1/models":
                    self.send_error(404)
                    return
                if state.models_status != 200:
                    body = b'{"error":"models unavailable"}'
                    self.send_response(state.models_status)
                else:
                    body = json.dumps(
                        {
                            "object": "list",
                            "data": [
                                {"id": QWEN_27B.name, "object": "model"},
                                {"id": GEMMA_31B.name, "object": "model"},
                            ],
                        }
                    ).encode("utf-8")
                    self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self._bytes(body)

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0") or 0)
                raw = self.rfile.read(length) if length else b""
                try:
                    request = json.loads(raw.decode("utf-8")) if raw else {}
                except json.JSONDecodeError:
                    request = {}
                with state.lock:
                    state.posts += 1
                    state._inflight += 1
                    state.max_inflight = max(state.max_inflight, state._inflight)
                    if isinstance(request, dict):
                        state.bodies.append(request)
                try:
                    path = self.path.split("?", 1)[0]
                    if path != "/v1/chat/completions":
                        self.send_error(404)
                        return
                    if state.http_status != 200:
                        body = b'{"error":{"message":"forced failure"}}'
                        self.send_response(state.http_status)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(body)))
                        self.send_header("Connection", "close")
                        self.end_headers()
                        self._bytes(body)
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    if state.empty:
                        return
                    if state.malformed:
                        self._bytes(b"data: {not-json}\n\n")
                        return
                    if state.first_delay:
                        time.sleep(state.first_delay)
                    self._bytes(b'data: {"choices":[{"index":0,"delta":{"role":"assistant","content":""}}]}\n\n')
                    count = state.chunks if state.chunks is not None else int(request.get("max_tokens") or 1)
                    for index in range(count):
                        if index and state.inter_delay:
                            time.sleep(state.inter_delay)
                        event = {"choices": [{"index": 0, "delta": {"content": f"tok{index} "}}]}
                        self._bytes(b"data: " + json.dumps(event).encode("utf-8") + b"\n\n")
                    if state.usage != "omit":
                        completion = state.fixed_completion_tokens if state.fixed_completion_tokens is not None else count
                        usage = {
                            "choices": [],
                            "usage": {
                                "prompt_tokens": state.fixed_prompt_tokens,
                                "completion_tokens": completion,
                                "total_tokens": state.fixed_prompt_tokens + completion,
                            },
                        }
                        self._bytes(b"data: " + json.dumps(usage).encode("utf-8") + b"\n\n")
                    self._bytes(b"data: [DONE]\n\n")
                finally:
                    with state.lock:
                        state._inflight -= 1

        return Handler


@contextmanager
def sse_server(**kwargs: object):
    server = SseServer(**kwargs)  # type: ignore[arg-type]
    try:
        yield server
    finally:
        server.close()


def _run_args(endpoint: str, out_dir: Path, **overrides: object) -> list[str]:
    args = {
        "model": QWEN,
        "endpoints": endpoint,
        "mode": "single-gpu",
        "prompt_lengths": "32",
        "output_lengths": "4",
        "concurrencies": "1",
        "warmup": "0",
        "requests": "1",
        "timeout": "5",
    }
    args.update(overrides)
    return [
        "run",
        "--model",
        str(args["model"]),
        "--endpoints",
        str(args["endpoints"]),
        "--mode",
        str(args["mode"]),
        "--prompt-lengths",
        str(args["prompt_lengths"]),
        "--output-lengths",
        str(args["output_lengths"]),
        "--concurrencies",
        str(args["concurrencies"]),
        "--warmup",
        str(args["warmup"]),
        "--requests",
        str(args["requests"]),
        "--timeout",
        str(args["timeout"]),
        "--out-dir",
        str(out_dir),
    ]


def _closed_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def _load_jsonl(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _assert_no_measurements(out_dir: Path) -> None:
    for name in ("matrix.json", "matrix.csv", "requests.jsonl", "summary.md"):
        assert not (out_dir / name).exists()
    charts = out_dir / "charts"
    if charts.exists():
        assert not any(charts.iterdir())


def _assert_cell_math(out_dir: Path) -> dict:
    metadata, rows = load_matrix(out_dir / "matrix.json")
    records = _load_jsonl(out_dir / "requests.jsonl")
    grouped: dict[tuple, list[dict]] = {}
    for record in records:
        key = (record["prompt_tokens_target"], record["output_tokens_target"], record["concurrency"])
        grouped.setdefault(key, []).append(record)
    assert rows, "measured matrix was empty"
    for row in rows:
        key = (row["prompt_tokens_target"], row["output_tokens_target"], row["concurrency"])
        cell = grouped[key]
        assert len(cell) == row["measured_requests"]
        ttft = [item["ttft_ms"] for item in cell]
        e2e = [item["e2e_ms"] for item in cell]
        decode = [item["decode_tps"] for item in cell]
        assert all(value is not None for value in ttft)
        assert row["ttft_ms_p50"] == percentile(ttft, 50)
        assert row["ttft_ms_p95"] == percentile(ttft, 95)
        assert row["ttft_ms_mean"] == sum(ttft) / len(ttft)
        assert row["e2e_ms_p50"] == percentile(e2e, 50)
        assert row["e2e_ms_p95"] == percentile(e2e, 95)
        assert row["e2e_ms_mean"] == sum(e2e) / len(e2e)
        assert row["decode_tps_mean"] == sum(decode) / len(decode)
        total = sum(item["completion_tokens"] for item in cell)
        assert total == row["total_completion_tokens"]
        assert row["cell_wall_seconds"] > 0
        assert row["aggregate_tps"] == total / row["cell_wall_seconds"]
        for item in cell:
            assert item["e2e_ms"] >= item["ttft_ms"]
            assert item["decode_tps"] == compute_decode_tps(item["completion_tokens"], item["ttft_ms"], item["e2e_ms"])
    return {"metadata": metadata, "rows": rows, "records": records}


def test_model_presets_and_prompt_builder():
    assert QWEN_27B.weight_dir == r"D:\models\exl3\Qwen3.8-27B-Abliterated-EXL3-4.5bpw"
    assert QWEN_27B.quant_bpw == 4.5
    assert QWEN_27B.format == "EXL3"
    assert GEMMA_31B.weight_dir == r"D:\models\exl3\gemma-4-31B-it-uncensored-EXL3-4.0bpw"
    assert GEMMA_31B.quant_bpw == 4.0
    assert GEMMA_31B.format == "EXL3"
    assert DEFAULT_PROMPT_LENGTHS == (512, 2048, 8192)
    assert DEFAULT_OUTPUT_LENGTHS == (128, 512)
    assert DEFAULT_CONCURRENCIES == (1, 2, 4, 8)
    assert DEFAULT_MODES == ("single-gpu", "dual-gpu")
    assert DEFAULT_ENDPOINTS == ("http://127.0.0.1:5000/v1", "http://127.0.0.1:5001/v1")
    for target in (1, 32, 512, 2048, 8192):
        first = build_synthetic_prompt(target)
        second = build_synthetic_prompt(target)
        assert first == second
        assert estimate_prompt_tokens(first) == target
        assert len(first) == 4 * target - 3
    prose = build_synthetic_prompt(64)
    assert "RTX 3090" in prose
    assert "EXL3" in prose
    with pytest.raises(ValueError):
        build_synthetic_prompt(0)


def test_percentile_decode_and_joules_formulas():
    assert percentile([10, 20, 30, 40], 50) == 25
    assert percentile([10, 20, 30, 40], 95) == 30 * 0.15 + 40 * 0.85
    assert percentile([7.5], 95) == 7.5
    assert compute_decode_tps(8, 200.0, 1000.0) == 7 / 0.8
    assert compute_decode_tps(1, 200.0, 1000.0) == 1.0
    assert compute_decode_tps(5, 100.0, 100.0) == 50.0
    with pytest.raises(BenchmarkEndpointError):
        compute_decode_tps(4, 10.0, 0.0)
    assert joules_per_token(275.0, 50.0) == 275.0 / 50.0
    assert joules_per_token(None, 50.0) is None
    assert joules_per_token(0.0, 50.0) is None
    assert joules_per_token(10.0, 0.0) is None


def test_runtime_modules_are_stdlib_only():
    forbidden = {"httpx", "aiohttp", "matplotlib", "numpy", "pynvml", "requests", "pandas", "torch"}
    for path in (ROOT / "bench_exl3").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module.split(".")[0]]
            for name in modules:
                assert name not in forbidden
                if name != "bench_exl3":
                    assert name in sys.stdlib_module_names, f"{path.name} imports {name}"


def test_list_models_prints_weight_paths(capsys: pytest.CaptureFixture[str]):
    assert main(["list-models"]) == 0
    printed = capsys.readouterr().out
    assert r"D:\models\exl3\Qwen3.8-27B-Abliterated-EXL3-4.5bpw" in printed
    assert r"D:\models\exl3\gemma-4-31B-it-uncensored-EXL3-4.0bpw" in printed
    assert "4.5" in printed
    assert "4.0" in printed
    proc = subprocess.run(
        [sys.executable, "-m", "bench_exl3", "list-models"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert r"D:\models\exl3\Qwen3.8-27B-Abliterated-EXL3-4.5bpw" in proc.stdout


def test_parse_nvidia_smi_csv_dual_3090_and_missing_values():
    parsed = parse_nvidia_smi_csv(
        "0, NVIDIA GeForce RTX 3090, 18432, 24576, 320.55, 67, 98\n"
        "1, NVIDIA GeForce RTX 3090, 17654, 24576, 301.20, 64, 97\n"
    )
    assert len(parsed) == 2
    assert parsed[0].index == 0
    assert parsed[0].name == "NVIDIA GeForce RTX 3090"
    assert parsed[0].memory_used_mib == 18432
    assert parsed[0].memory_total_mib == 24576
    assert parsed[0].power_draw_w == 320.55
    assert parsed[0].temperature_c == 67
    assert parsed[0].utilization_gpu_pct == 98
    assert parsed[1].index == 1
    assert parsed[1].memory_used_mib == 17654
    assert parsed[1].power_draw_w == 301.20

    with_units = parse_nvidia_smi_csv(
        "index, name, memory.used [MiB], memory.total [MiB], power.draw [W], temperature.gpu, utilization.gpu [%]\r\n"
        "0, NVIDIA GeForce RTX 3090, 18432 MiB, 24576 MiB, 320.55 W, 67, 98 %\r\n"
        "1, NVIDIA GeForce RTX 3090, [N/A], 24576 MiB, [N/A], 41, 0 %\r\n"
    )
    assert len(with_units) == 2
    assert with_units[0].memory_used_mib == 18432
    assert with_units[0].power_draw_w == 320.55
    assert with_units[0].utilization_gpu_pct == 98
    assert with_units[1].memory_used_mib is None
    assert with_units[1].power_draw_w is None
    assert with_units[1].temperature_c == 41
    assert with_units[1].utilization_gpu_pct == 0
    partial = summarize_samples([with_units])
    assert partial["peak_vram_mib"] is None
    assert partial["mean_power_w"] is None
    assert partial["peak_power_w"] is None
    assert partial["peak_vram_mib_per_gpu"] == {"0": 18432.0}
    assert partial["peak_temp_c"] == 67
    assert partial["mean_gpu_util_pct"] == 49

    first = parse_nvidia_smi_csv(
        "0, NVIDIA GeForce RTX 3090, 1000, 24576, 100, 50, 10\n"
        "1, NVIDIA GeForce RTX 3090, 2000, 24576, 150, 60, 20\n"
    )
    second = parse_nvidia_smi_csv(
        "0, NVIDIA GeForce RTX 3090, 3000, 24576, 200, 70, 80\n"
        "1, NVIDIA GeForce RTX 3090, 2500, 24576, 100, 55, 40\n"
    )
    summary = summarize_samples([first, second])
    assert summary["samples_count"] == 2
    assert summary["peak_vram_mib_per_gpu"] == {"0": 3000.0, "1": 2500.0}
    assert summary["peak_vram_mib"] == 5500
    assert summary["mean_power_w"] == 275
    assert summary["peak_power_w"] == 300
    assert summary["peak_temp_c"] == 70
    assert summary["mean_gpu_util_pct"] == 37.5
    assert summary["gpu_names"] == {"0": "NVIDIA GeForce RTX 3090", "1": "NVIDIA GeForce RTX 3090"}

    blank = summarize_samples([])
    assert blank == empty_telemetry()


def test_missing_nvidia_smi_returns_none_fields(tmp_path: Path):
    missing = tmp_path / "nvidia-smi-not-installed"
    with GpuTelemetrySampler(nvidia_smi_bin=str(missing), interval_s=0.2) as sampler:
        pass
    summary = sampler.summary
    assert summary["available"] is False
    assert summary["samples_count"] == 0
    for key in (
        "peak_vram_mib",
        "peak_vram_mib_per_gpu",
        "mean_power_w",
        "peak_power_w",
        "peak_temp_c",
        "mean_gpu_util_pct",
        "gpu_names",
        "memory_total_mib_per_gpu",
    ):
        assert summary[key] is None
    assert "1500" not in json.dumps(summary)


def test_sampler_reads_nvidia_smi_csv(tmp_path: Path):
    script = tmp_path / "nvidia-smi"
    script.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' '0, NVIDIA GeForce RTX 3090, 1500, 24576, 180.5, 61, 77'\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    with GpuTelemetrySampler(nvidia_smi_bin=str(script), interval_s=30) as sampler:
        pass
    summary = sampler.summary
    assert summary["available"] is True
    assert summary["samples_count"] == 1
    assert summary["peak_vram_mib"] == 1500
    assert summary["peak_vram_mib_per_gpu"] == {"0": 1500.0}
    assert summary["mean_power_w"] == 180.5
    assert summary["peak_power_w"] == 180.5
    assert summary["peak_temp_c"] == 61
    assert summary["mean_gpu_util_pct"] == 77
    assert summary["gpu_names"]["0"] == "NVIDIA GeForce RTX 3090"
    assert summary["memory_total_mib_per_gpu"]["0"] == 24576


def test_stream_usage_overrides_chunk_count_and_failures():
    with sse_server(chunks=2, fixed_completion_tokens=9, fixed_prompt_tokens=70, first_delay=0.01, inter_delay=0.005) as server:
        metrics = stream_chat(server.base_url, model=QWEN, prompt="ping", output_tokens=2, timeout=5)
    assert metrics.usage_source == "server_usage"
    assert metrics.completion_tokens == 9
    assert metrics.chunk_count == 2
    assert metrics.prompt_tokens == 70
    assert metrics.ttft_ms is not None
    assert metrics.e2e_ms >= metrics.ttft_ms
    assert metrics.decode_tps == compute_decode_tps(9, metrics.ttft_ms, metrics.e2e_ms)
    body = server.bodies[0]
    assert body["stream"] is True
    assert body["temperature"] == 0
    assert body["stream_options"] == {"include_usage": True}
    assert body["max_tokens"] == 2
    assert body["model"] == QWEN

    with sse_server(usage="omit", chunks=3, first_delay=0.005, inter_delay=0.005) as server:
        fallback = stream_chat(server.base_url, model=QWEN, prompt="ping", output_tokens=3, timeout=5)
    assert fallback.usage_source == "chunk_count_fallback"
    assert fallback.completion_tokens == 3
    assert fallback.chunk_count == 3
    assert fallback.prompt_tokens is None

    with sse_server(http_status=500) as server:
        with pytest.raises(BenchmarkEndpointError, match="HTTP 500"):
            stream_chat(server.base_url, model=QWEN, prompt="ping", output_tokens=4, timeout=5)

    with sse_server(empty=True) as server:
        with pytest.raises(BenchmarkEndpointError, match="empty SSE"):
            stream_chat(server.base_url, model=QWEN, prompt="ping", output_tokens=4, timeout=5)

    with sse_server(malformed=True) as server:
        with pytest.raises(BenchmarkEndpointError, match="malformed"):
            stream_chat(server.base_url, model=QWEN, prompt="ping", output_tokens=4, timeout=5)


def test_single_endpoint_matrix_math_and_report(tmp_path: Path):
    out_dir = tmp_path / "single"
    with sse_server() as server:
        code = main(
            _run_args(
                server.base_url,
                out_dir,
                prompt_lengths="32",
                output_lengths="4",
                concurrencies="1,2",
                warmup="1",
                requests="4",
            )
        )
        posts = server.posts
        max_inflight = server.max_inflight
        request_body = server.bodies[-1]
    assert code == 0
    assert posts == 2 * (1 + 4)
    assert max_inflight >= 2
    assert request_body["messages"][0]["content"] == build_synthetic_prompt(32)
    assert request_body["stream_options"] == {"include_usage": True}
    measured = _assert_cell_math(out_dir)
    assert len(measured["records"]) == 8
    assert {row["concurrency"] for row in measured["rows"]} == {1, 2}
    for record in measured["records"]:
        assert record["endpoint"] == server.base_url
        assert record["usage_source"] == "server_usage"
        assert record["prompt_tokens"] == 70
        assert record["prompt_tokens_target"] == 32
        assert record["completion_tokens"] == 4
        assert record["chunk_count"] == 4
        assert record["model"] == QWEN
        assert record["quant_bpw"] == 4.5
    for row in measured["rows"]:
        assert row["prompt_tokens_mean"] == 70
        assert row["completion_tokens_mean"] == 4
        assert row["quant_bpw"] == 4.5
        assert row["format"] == "EXL3"
        assert row["weight_dir"] == QWEN_27B.weight_dir
        assert row["usage_source"] == "server_usage"
        if row["telemetry_available"]:
            assert isinstance(row["mean_power_w"], (int, float))
        else:
            assert row["mean_power_w"] is None
            assert row["peak_vram_mib"] is None
            assert row["peak_power_w"] is None
            assert row["peak_temp_c"] is None
            assert row["joules_per_token"] is None
            assert row["telemetry_samples"] == 0

    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    ttft_svg = (out_dir / "charts" / "ttft_by_concurrency.svg").read_text(encoding="utf-8")
    tps_svg = (out_dir / "charts" / "tps_by_concurrency.svg").read_text(encoding="utf-8")
    assert QWEN in summary
    assert "4.5" in summary
    assert "single-gpu" in summary
    assert "TTFT p50" in summary
    assert "TTFT p95" in summary
    assert "Decode TPS" in summary
    assert "Aggregate TPS" in summary
    assert "Peak VRAM" in summary
    assert "Mean Power" in summary
    assert "J/tok" in summary
    assert "Peak Temp" in summary
    assert "Concurrency" in ttft_svg
    assert "TTFT p50" in ttft_svg
    assert "Aggregate TPS" in tps_svg
    assert QWEN in tps_svg
    for row in measured["rows"]:
        assert format_metric(row["ttft_ms_p50"], 3) in summary
        assert format_metric(row["ttft_ms_p95"], 3) in summary
        assert format_metric(row["decode_tps_mean"], 3) in summary
        assert format_metric(row["aggregate_tps"], 3) in summary
        assert f'data-value="{row["ttft_ms_p50"]!r}"' in ttft_svg
        assert f'data-value="{row["aggregate_tps"]!r}"' in tps_svg
        if row["mean_power_w"] is None:
            assert "N/A" in summary

    with (out_dir / "matrix.csv").open(encoding="utf-8", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == len(measured["rows"])
    _, from_csv = load_matrix(out_dir / "matrix.csv")
    for original, loaded in zip(measured["rows"], from_csv):
        assert loaded["aggregate_tps"] == original["aggregate_tps"]
        assert loaded["ttft_ms_p50"] == original["ttft_ms_p50"]
        assert int(loaded["prompt_tokens_target"]) == original["prompt_tokens_target"]

    charts = out_dir / "charts"
    summary_path = out_dir / "summary.md"
    summary_path.unlink()
    for chart in charts.iterdir():
        chart.unlink()
    assert main(["report", "--input", str(out_dir / "matrix.json"), "--out-dir", str(out_dir)]) == 0
    assert summary_path.is_file()
    assert (charts / "ttft_by_concurrency.svg").is_file()
    assert (charts / "tps_by_concurrency.svg").is_file()


def test_dual_endpoint_round_robin(tmp_path: Path):
    out_dir = tmp_path / "dual"
    with sse_server(first_delay=0.01, inter_delay=0.004) as left, sse_server(first_delay=0.01, inter_delay=0.004) as right:
        code = main(
            _run_args(
                f"{left.base_url},{right.base_url}",
                out_dir,
                mode="dual-gpu",
                concurrencies="2",
                warmup="0",
                requests="4",
            )
        )
        left_posts = left.posts
        right_posts = right.posts
    assert code == 0
    assert left_posts == 2
    assert right_posts == 2
    measured = _assert_cell_math(out_dir)
    ordered = sorted(measured["records"], key=lambda item: item["request_index"])
    assert [item["endpoint"] for item in ordered] == [left.base_url, right.base_url, left.base_url, right.base_url]
    assert measured["rows"][0]["mode"] == "dual-gpu"
    assert left.base_url in measured["rows"][0]["endpoints"]
    assert right.base_url in measured["rows"][0]["endpoints"]


def test_chunk_fallback_is_labeled_in_the_matrix(tmp_path: Path):
    out_dir = tmp_path / "fallback"
    with sse_server(usage="omit", chunks=3, first_delay=0.005, inter_delay=0.004) as server:
        code = main(
            _run_args(
                server.base_url,
                out_dir,
                output_lengths="3",
                requests="2",
                warmup="0",
            )
        )
    assert code == 0
    measured = _assert_cell_math(out_dir)
    assert measured["rows"][0]["usage_source"] == "chunk_count_fallback"
    assert measured["rows"][0]["prompt_tokens_mean"] is None
    assert measured["rows"][0]["completion_tokens_mean"] == 3
    for record in measured["records"]:
        assert record["usage_source"] == "chunk_count_fallback"
        assert record["prompt_tokens"] is None
        assert record["completion_tokens"] == 3
        assert record["chunk_count"] == 3
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    assert "chunk_count_fallback" in summary
    assert "N/A" in summary


def test_unreachable_endpoint_writes_no_matrix(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    out_dir = tmp_path / "down"
    port = _closed_port()
    code = main(
        _run_args(
            f"http://127.0.0.1:{port}/v1",
            out_dir,
            timeout="2",
        )
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "ERROR:" in captured.err
    _assert_no_measurements(out_dir)
    blob = captured.out + captured.err
    assert "aggregate_tps" not in blob


def test_http_500_fails_closed(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    out_dir = tmp_path / "err"
    with sse_server(http_status=500) as server:
        code = main(_run_args(server.base_url, out_dir, warmup="0", requests="2", concurrencies="2"))
    captured = capsys.readouterr()
    assert code != 0
    assert "HTTP 500" in captured.err
    _assert_no_measurements(out_dir)


def test_unknown_model_and_dual_with_one_endpoint_do_not_write(tmp_path: Path):
    out_dir = tmp_path / "bad"
    assert main(_run_args("http://127.0.0.1:9/v1", out_dir, model="not-a-real-model")) == 2
    _assert_no_measurements(out_dir)
    assert main(_run_args("http://127.0.0.1:9/v1", out_dir, mode="dual-gpu")) == 2
    _assert_no_measurements(out_dir)


def test_empty_matrix_report_has_no_invented_series(tmp_path: Path):
    out_dir = tmp_path / "empty"
    write_report(
        out_dir,
        metadata={"intended_hardware": "Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)"},
        rows=[],
    )
    summary = (out_dir / "summary.md").read_text(encoding="utf-8")
    svg = (out_dir / "charts" / "ttft_by_concurrency.svg").read_text(encoding="utf-8")
    tps = (out_dir / "charts" / "tps_by_concurrency.svg").read_text(encoding="utf-8")
    assert "No measured rows" in summary
    assert "No measured values" in svg
    assert "No measured values" in tps
    assert "data-value" not in svg
    assert "data-value" not in tps


def test_requests_undersaturated_rejected_and_auto_scales(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    out_bad = tmp_path / "under"
    code = main(_run_args("http://127.0.0.1:9/v1", out_bad, concurrencies="1,4", requests="2"))
    assert code == 2
    assert "must be >= max concurrency" in capsys.readouterr().err
    _assert_no_measurements(out_bad)

    out_auto = tmp_path / "auto"
    with sse_server() as server:
        code = main(
            [
                "run",
                "--model",
                QWEN_27B.name,
                "--endpoints",
                server.base_url,
                "--mode",
                "single-gpu",
                "--prompt-lengths",
                "16",
                "--output-lengths",
                "8",
                "--concurrencies",
                "1,3",
                "--warmup",
                "0",
                "--out-dir",
                str(out_auto),
                "--timeout",
                "5",
            ]
        )
    assert code == 0
    matrix = json.loads((out_auto / "matrix.json").read_text(encoding="utf-8"))
    by_conc = {row["concurrency"]: row["measured_requests"] for row in matrix["rows"]}
    assert by_conc == {1: 2, 3: 6}
