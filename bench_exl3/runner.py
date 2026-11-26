"""Benchmark matrix runner.

Warmup requests are issued and discarded. Measured requests run concurrently
and are the only samples written to requests.jsonl and the matrix files.
Any endpoint or stream failure aborts before those files are written.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bench_exl3.client import BenchmarkEndpointError, StreamMetrics, preflight, stream_chat
from bench_exl3.models import Exl3Model, build_synthetic_prompt, get_model
from bench_exl3.report import BOOL_FIELDS, INT_FIELDS, JSON_FIELDS, ROW_FIELDS, write_report
from bench_exl3.telemetry import GpuTelemetrySampler


def percentile(values: list[float], percent: float) -> float:
    """Linear-interpolation percentile (Hyndman-Fan type 7)."""

    if not values:
        raise ValueError("percentile of an empty sample")
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (percent / 100.0) * (len(ordered) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[low])
    weight = rank - low
    return float(ordered[low] * (1.0 - weight) + ordered[high] * weight)


def mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean of an empty sample")
    return sum(values) / len(values)


def endpoints_for_mode(mode: str, endpoints: list[str]) -> list[str]:
    cleaned = [item.strip() for item in endpoints if item.strip()]
    if mode == "single-gpu":
        if not cleaned:
            raise ValueError("single-gpu mode requires one endpoint")
        return [cleaned[0]]
    if mode == "dual-gpu":
        if len(cleaned) < 2:
            raise ValueError("dual-gpu mode requires two endpoints (GPU 0 and GPU 1)")
        return cleaned
    raise ValueError(f"unknown mode {mode!r}; expected single-gpu or dual-gpu")


def joules_per_token(mean_power_w: object, aggregate_tps: object) -> float | None:
    if not isinstance(mean_power_w, (int, float)) or isinstance(mean_power_w, bool):
        return None
    if not isinstance(aggregate_tps, (int, float)) or isinstance(aggregate_tps, bool):
        return None
    if mean_power_w <= 0 or aggregate_tps <= 0:
        return None
    return float(mean_power_w) / float(aggregate_tps)


def _optional_mean(values: list[float | None]) -> float | None:
    if any(value is None for value in values):
        return None
    return mean([float(value) for value in values if value is not None])


def _usage_source(records: list[StreamMetrics]) -> str:
    sources = {record.usage_source for record in records}
    if len(sources) == 1:
        return next(iter(sources))
    return "mixed"


def _run_requests(
    *,
    endpoints: list[str],
    model_name: str,
    prompt: str,
    output_tokens: int,
    count: int,
    concurrency: int,
    timeout: float,
) -> list[StreamMetrics]:
    if count < 1:
        return []
    workers = max(1, min(concurrency, count))
    results: dict[int, StreamMetrics] = {}
    errors: list[BenchmarkEndpointError] = []

    def one(index: int) -> StreamMetrics:
        endpoint = endpoints[index % len(endpoints)]
        return stream_chat(
            endpoint,
            model=model_name,
            prompt=prompt,
            output_tokens=output_tokens,
            timeout=timeout,
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, index): index for index in range(count)}
        for future, index in futures.items():
            try:
                results[index] = future.result()
            except BenchmarkEndpointError as exc:
                errors.append(exc)
    if errors:
        detail = "; ".join(str(exc) for exc in errors)
        raise BenchmarkEndpointError(detail)
    return [results[index] for index in range(count)]


def _cell_row(
    *,
    model: Exl3Model,
    mode: str,
    endpoints: list[str],
    prompt_tokens_target: int,
    output_tokens_target: int,
    concurrency: int,
    warmup: int,
    records: list[StreamMetrics],
    cell_wall_seconds: float,
    telemetry: dict[str, object],
) -> dict[str, object]:
    if cell_wall_seconds <= 0:
        raise BenchmarkEndpointError("cell wall clock was non-positive")
    ttft_values = [record.ttft_ms for record in records]
    e2e_values = [record.e2e_ms for record in records]
    decode_values = [record.decode_tps for record in records]
    prompt_values = [record.prompt_tokens for record in records]
    completion_values = [record.completion_tokens for record in records]
    total_completion = sum(completion_values)
    aggregate = total_completion / cell_wall_seconds
    ttft_ready = all(value is not None for value in ttft_values)
    ttft_numbers = [float(value) for value in ttft_values if value is not None]
    mean_power = telemetry.get("mean_power_w")
    return {
        "model": model.name,
        "quant_bpw": model.quant_bpw,
        "format": model.format,
        "weight_dir": model.weight_dir,
        "mode": mode,
        "endpoints": ",".join(endpoints),
        "prompt_tokens_target": prompt_tokens_target,
        "output_tokens_target": output_tokens_target,
        "concurrency": concurrency,
        "warmup": warmup,
        "measured_requests": len(records),
        "prompt_tokens_mean": _optional_mean(prompt_values),
        "completion_tokens_mean": mean([float(value) for value in completion_values]),
        "usage_source": _usage_source(records),
        "ttft_ms_p50": percentile(ttft_numbers, 50) if ttft_ready else None,
        "ttft_ms_p95": percentile(ttft_numbers, 95) if ttft_ready else None,
        "ttft_ms_mean": mean(ttft_numbers) if ttft_ready else None,
        "e2e_ms_p50": percentile(e2e_values, 50),
        "e2e_ms_p95": percentile(e2e_values, 95),
        "e2e_ms_mean": mean(e2e_values),
        "decode_tps_mean": mean(decode_values),
        "aggregate_tps": aggregate,
        "cell_wall_seconds": cell_wall_seconds,
        "total_completion_tokens": total_completion,
        "peak_vram_mib": telemetry.get("peak_vram_mib"),
        "peak_vram_mib_per_gpu": telemetry.get("peak_vram_mib_per_gpu"),
        "mean_power_w": mean_power,
        "peak_power_w": telemetry.get("peak_power_w"),
        "peak_temp_c": telemetry.get("peak_temp_c"),
        "mean_gpu_util_pct": telemetry.get("mean_gpu_util_pct"),
        "joules_per_token": joules_per_token(mean_power, aggregate),
        "telemetry_samples": int(telemetry.get("telemetry_samples") or telemetry.get("samples_count") or 0),
        "telemetry_available": bool(telemetry.get("available")),
        "gpu_names": telemetry.get("gpu_names"),
    }


def _record_dict(
    *,
    model: Exl3Model,
    mode: str,
    prompt_tokens_target: int,
    output_tokens_target: int,
    concurrency: int,
    index: int,
    metrics: StreamMetrics,
) -> dict[str, object]:
    return {
        "model": model.name,
        "quant_bpw": model.quant_bpw,
        "format": model.format,
        "mode": mode,
        "endpoint": metrics.endpoint,
        "prompt_tokens_target": prompt_tokens_target,
        "output_tokens_target": output_tokens_target,
        "concurrency": concurrency,
        "request_index": index,
        "ttft_ms": metrics.ttft_ms,
        "e2e_ms": metrics.e2e_ms,
        "prompt_tokens": metrics.prompt_tokens,
        "completion_tokens": metrics.completion_tokens,
        "usage_source": metrics.usage_source,
        "decode_tps": metrics.decode_tps,
        "chunk_count": metrics.chunk_count,
    }


def _csv_cell(field: str, value: object) -> str:
    if value is None:
        return ""
    if field in BOOL_FIELDS:
        return "true" if value else "false"
    if field in JSON_FIELDS:
        return json.dumps(value, separators=(",", ":"), allow_nan=False)
    if field in INT_FIELDS:
        return str(int(value))  # type: ignore[arg-type]
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_matrix(out_dir: Path, metadata: dict[str, object], rows: list[dict[str, object]], requests: list[dict[str, object]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = out_dir / "matrix.json"
    csv_path = out_dir / "matrix.csv"
    jsonl_path = out_dir / "requests.jsonl"
    document = {"metadata": metadata, "rows": rows}
    matrix_path.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_cell(field, row.get(field)) for field in ROW_FIELDS})
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in requests:
            handle.write(json.dumps(record, allow_nan=False) + "\n")


def _metadata(model: Exl3Model, mode: str, endpoints: list[str], observed_gpus: object) -> dict[str, object]:
    import platform

    return {
        "intended_hardware": "Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)",
        "backend": "TabbyAPI (ExLlamaV3)",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "endpoints": list(endpoints),
        "mode": mode,
        "model": model.as_dict(),
        "observed_gpus": observed_gpus,
        "protocol": {
            "temperature": 0.0,
            "stream": True,
            "stream_options": {"include_usage": True},
            "ttft": "perf_counter from request dispatch to the first non-empty content delta",
            "e2e": "perf_counter from request dispatch until [DONE] or stream close",
            "decode_tps": "(completion_tokens - 1) / ((e2e_ms - ttft_ms) / 1000) when completion_tokens > 1 and e2e_ms > ttft_ms, else completion_tokens / (e2e_ms / 1000)",
            "aggregate_tps": "total_completion_tokens / cell_wall_seconds",
            "joules_per_token": "mean_power_w / aggregate_tps when both are present and > 0",
            "percentile": "Hyndman-Fan type 7 linear interpolation",
            "usage": "server usage.prompt_tokens and usage.completion_tokens; completion falls back to non-empty content-delta chunks only when usage is omitted",
        },
    }


def run_benchmark(
    *,
    model: str,
    endpoints: list[str],
    mode: str,
    prompt_lengths: list[int],
    output_lengths: list[int],
    concurrencies: list[int],
    warmup: int,
    requests: int | None,
    out_dir: str | Path,
    timeout: float,
    telemetry_interval_s: float = 0.25,
) -> int:
    """Run the matrix. Returns 0 on success and non-zero on failure.

    Matrix files are written only after every cell completes. A failed preflight
    or a failed request leaves no requests.jsonl, matrix.csv, or matrix.json.
    """

    try:
        preset = get_model(model)
        selected = endpoints_for_mode(mode, endpoints)
        if warmup < 0:
            raise ValueError("warmup must be >= 0")
        if requests is not None and requests < 1:
            raise ValueError("requests must be >= 1")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        for label, values in (
            ("prompt length", prompt_lengths),
            ("output length", output_lengths),
            ("concurrency", concurrencies),
        ):
            if not values:
                raise ValueError(f"at least one {label} is required")
            for value in values:
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    raise ValueError(f"{label} must be a positive integer")
        if requests is not None and requests < max(concurrencies):
            raise ValueError(
                f"requests ({requests}) must be >= max concurrency ({max(concurrencies)}) "
                "so every concurrency cell is genuinely saturated (or omit --requests for auto 2x concurrency)"
            )
        for endpoint in selected:
            preflight(endpoint, timeout, preset.name)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 2
    except BenchmarkEndpointError as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1

    rows: list[dict[str, object]] = []
    request_rows: list[dict[str, object]] = []
    observed_gpus: object = None
    try:
        for prompt_len in prompt_lengths:
            prompt = build_synthetic_prompt(prompt_len)
            for output_len in output_lengths:
                for concurrency in concurrencies:
                    if warmup:
                        _run_requests(
                            endpoints=selected,
                            model_name=preset.name,
                            prompt=prompt,
                            output_tokens=output_len,
                            count=warmup,
                            concurrency=concurrency,
                            timeout=timeout,
                        )
                    cell_requests = requests if requests is not None else concurrency * 2
                    with GpuTelemetrySampler(interval_s=telemetry_interval_s) as sampler:
                        started = time.perf_counter()
                        measured = _run_requests(
                            endpoints=selected,
                            model_name=preset.name,
                            prompt=prompt,
                            output_tokens=output_len,
                            count=cell_requests,
                            concurrency=concurrency,
                            timeout=timeout,
                        )
                        wall = time.perf_counter() - started
                    telemetry = dict(sampler.summary)
                    if observed_gpus is None and telemetry.get("gpu_names"):
                        observed_gpus = telemetry.get("gpu_names")
                    row = _cell_row(
                        model=preset,
                        mode=mode,
                        endpoints=selected,
                        prompt_tokens_target=prompt_len,
                        output_tokens_target=output_len,
                        concurrency=concurrency,
                        warmup=warmup,
                        records=measured,
                        cell_wall_seconds=wall,
                        telemetry=telemetry,
                    )
                    rows.append(row)
                    for index, metrics in enumerate(measured):
                        request_rows.append(
                            _record_dict(
                                model=preset,
                                mode=mode,
                                prompt_tokens_target=prompt_len,
                                output_tokens_target=output_len,
                                concurrency=concurrency,
                                index=index,
                                metrics=metrics,
                            )
                        )
                    print(
                        "cell "
                        f"model={preset.name} mode={mode} prompt_tokens_target={prompt_len} "
                        f"output_tokens_target={output_len} concurrency={concurrency} "
                        f"aggregate_tps={row['aggregate_tps']} ttft_ms_p50={row['ttft_ms_p50']} "
                        f"decode_tps_mean={row['decode_tps_mean']}",
                        flush=True,
                    )
    except BenchmarkEndpointError as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1

    destination = Path(out_dir)
    metadata = _metadata(preset, mode, selected, observed_gpus)
    write_matrix(destination, metadata, rows, request_rows)
    write_report(destination, destination / "matrix.json")
    print(f"wrote {destination / 'matrix.json'}", flush=True)
    print(f"wrote {destination / 'matrix.csv'}", flush=True)
    print(f"wrote {destination / 'requests.jsonl'}", flush=True)
    print(f"wrote {destination / 'summary.md'}", flush=True)
    return 0
