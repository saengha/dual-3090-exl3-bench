"""Markdown summary and pure-Python SVG charts from a measured matrix.

Numeric cells are formatted from the matrix values. Missing measurements are
rendered as N/A. This module does not synthesize benchmark rows.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROW_FIELDS = [
    "model",
    "quant_bpw",
    "format",
    "weight_dir",
    "mode",
    "endpoints",
    "prompt_tokens_target",
    "output_tokens_target",
    "concurrency",
    "warmup",
    "measured_requests",
    "prompt_tokens_mean",
    "completion_tokens_mean",
    "usage_source",
    "ttft_ms_p50",
    "ttft_ms_p95",
    "ttft_ms_mean",
    "e2e_ms_p50",
    "e2e_ms_p95",
    "e2e_ms_mean",
    "decode_tps_mean",
    "aggregate_tps",
    "cell_wall_seconds",
    "total_completion_tokens",
    "peak_vram_mib",
    "peak_vram_mib_per_gpu",
    "mean_power_w",
    "peak_power_w",
    "peak_temp_c",
    "mean_gpu_util_pct",
    "joules_per_token",
    "telemetry_samples",
    "telemetry_available",
    "gpu_names",
]

INT_FIELDS = {
    "prompt_tokens_target",
    "output_tokens_target",
    "concurrency",
    "warmup",
    "measured_requests",
    "total_completion_tokens",
    "telemetry_samples",
}
BOOL_FIELDS = {"telemetry_available"}
JSON_FIELDS = {"peak_vram_mib_per_gpu", "gpu_names"}
STRING_FIELDS = {"model", "format", "weight_dir", "mode", "endpoints", "usage_source"}

_PALETTE = (
    "#1f4e79",
    "#b85c38",
    "#2f6f4e",
    "#6b4c9a",
    "#c47b00",
    "#0f6f8a",
    "#8c3a4b",
    "#3d6b4f",
)


class ReportError(Exception):
    """The measured matrix could not be read or rendered."""


def format_metric(value: object, digits: int = 3) -> str:
    number = _as_float(value)
    if number is None:
        return "N/A"
    return f"{number:.{digits}f}"


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _as_int(value: object) -> int | None:
    number = _as_float(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def _md(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _xml(value: object) -> str:
    text = str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _parse_csv_cell(field: str, text: str) -> object:
    if text == "":
        return None
    if field in BOOL_FIELDS:
        return text.strip().lower() == "true"
    if field in JSON_FIELDS:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ReportError(f"malformed JSON in column {field}") from exc
    if field in INT_FIELDS:
        return int(float(text))
    if field in STRING_FIELDS:
        return text
    try:
        return float(text)
    except ValueError:
        return text


def _load_csv(path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ReportError(f"matrix csv has no header: {path}")
        rows = []
        for raw in reader:
            rows.append({field: _parse_csv_cell(field, raw.get(field, "") or "") for field in raw})
    return {}, rows


def load_matrix(path: str | Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    source = Path(path)
    if not source.is_file():
        raise ReportError(f"matrix file not found: {source}")
    if source.suffix.lower() == ".csv":
        return _load_csv(source)
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReportError(f"malformed matrix json {source}: {exc}") from exc
    if isinstance(document, list):
        return {}, document
    if not isinstance(document, dict) or not isinstance(document.get("rows"), list):
        raise ReportError(f"matrix json must contain a rows list: {source}")
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, list(document["rows"])


def _series(rows: list[dict[str, object]], value_key: str) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[tuple[float, float]]] = {}
    order: list[tuple[object, ...]] = []
    for row in rows:
        concurrency = _as_float(row.get("concurrency"))
        value = _as_float(row.get(value_key))
        if concurrency is None or value is None:
            continue
        key = (
            row.get("model"),
            row.get("mode"),
            row.get("prompt_tokens_target"),
            row.get("output_tokens_target"),
        )
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append((concurrency, value))
    series = []
    for key in order:
        points = sorted(grouped[key], key=lambda item: item[0])
        model, mode, prompt, output = key
        label = f"{model} | {mode} | prompt {prompt} | output {output}"
        series.append({"label": label, "points": points})
    return series


def render_chart(title: str, y_label: str, rows: list[dict[str, object]], value_key: str, digits: int) -> str:
    series = _series(rows, value_key)
    width = 1200
    height = 680
    if not series:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<rect width="100%" height="100%" fill="#ffffff"/>'
            f'<text x="48" y="64" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="22" fill="#1c1c1c">{_xml(title)}</text>'
            f'<text x="48" y="110" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="16" fill="#333333">No measured values</text>'
            "</svg>\n"
        )

    left, right, top, bottom = 84, 790, 64, 560
    plot_w = right - left
    plot_h = bottom - top
    values = [value for item in series for _, value in item["points"]]
    peak = max(values)
    y_max = peak * 1.12 if peak > 0 else 1.0
    concurrencies = sorted({point[0] for item in series for point in item["points"]})

    def x_of(concurrency: float) -> float:
        if len(concurrencies) == 1:
            return (left + right) / 2
        index = concurrencies.index(concurrency)
        return left + plot_w * index / (len(concurrencies) - 1)

    def y_of(value: float) -> float:
        return bottom - plot_h * (value / y_max)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; fill: #1c1c1c; }</style>',
        f"<title>{_xml(title)}</title>",
        f"<desc>Values are taken from measured matrix column { _xml(value_key) }.</desc>",
        f'<text x="{left}" y="36" font-size="20" font-weight="600">{_xml(title)}</text>',
    ]
    ticks = 5
    for step in range(ticks + 1):
        value = y_max * step / ticks
        y = y_of(value)
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{right}" y2="{y:.2f}" stroke="#e6e6e6" stroke-width="1"/>')
        parts.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" font-size="12" text-anchor="end" fill="#333333">{_xml(format_metric(value, digits))}</text>'
        )
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#222222" stroke-width="1.2"/>')
    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#222222" stroke-width="1.2"/>')
    for concurrency in concurrencies:
        x = x_of(concurrency)
        label = str(int(concurrency)) if float(concurrency).is_integer() else format_metric(concurrency, 3)
        parts.append(f'<line x1="{x:.2f}" y1="{bottom}" x2="{x:.2f}" y2="{bottom + 6}" stroke="#222222" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{bottom + 24}" font-size="12" text-anchor="middle">{_xml(label)}</text>')
    parts.append(f'<text x="{(left + right) / 2:.2f}" y="{bottom + 52}" font-size="14" text-anchor="middle">Concurrency</text>')
    parts.append(
        f'<text transform="translate(24 {(top + bottom) / 2:.2f}) rotate(-90)" font-size="14" text-anchor="middle">{_xml(y_label)}</text>'
    )
    for index, item in enumerate(series):
        color = _PALETTE[index % len(_PALETTE)]
        coords = []
        for concurrency, value in item["points"]:
            coords.append(f"{x_of(concurrency):.2f},{y_of(value):.2f}")
        if len(coords) >= 2:
            parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.2" points="{" ".join(coords)}"/>')
        for concurrency, value in item["points"]:
            x = x_of(concurrency)
            y = y_of(value)
            label_y = y - 10 - (index % 4) * 12
            if label_y < top + 12:
                label_y = y + 16 + (index % 3) * 12
            parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.2" fill="{color}" '
                f'data-series="{_xml(item["label"])}" data-concurrency="{_xml(concurrency)}" data-value="{_xml(repr(value))}"/>'
            )
            parts.append(
                f'<text x="{x:.2f}" y="{label_y:.2f}" font-size="11" text-anchor="middle" fill="#111111">{_xml(format_metric(value, digits))}</text>'
            )
        legend_y = top + 8 + index * 36
        parts.append(f'<line x1="820" y1="{legend_y}" x2="858" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>')
        parts.append(f'<circle cx="839" cy="{legend_y}" r="4" fill="{color}"/>')
        parts.append(f'<text x="868" y="{legend_y + 4}" font-size="12">{_xml(item["label"])}</text>')
    parts.append("</svg>\n")
    return "".join(parts)


def render_summary(metadata: dict[str, object], rows: list[dict[str, object]]) -> str:
    model = metadata.get("model") if isinstance(metadata.get("model"), dict) else {}
    lines = [
        "# EXL3 Dual RTX 3090 Benchmark Summary",
        "",
        "Rows in this file are copied from the measured matrix. Missing telemetry is **N/A**. No benchmark number in this report is imputed.",
        "",
        "## Hardware and environment",
        "",
        f"- Intended hardware: {_md(metadata.get('intended_hardware') or 'Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)')}",
        f"- Backend: {_md(metadata.get('backend') or 'TabbyAPI (ExLlamaV3)')}",
        f"- Host platform (this file): {_md(metadata.get('platform') or 'unknown')}",
        f"- Python: {_md(metadata.get('python') or 'unknown')}",
        f"- Mode: {_md(metadata.get('mode') or 'see rows')}",
        f"- Endpoints: {_md(', '.join(metadata.get('endpoints')) if isinstance(metadata.get('endpoints'), list) else metadata.get('endpoints') or 'see rows')}",
    ]
    if model:
        lines.append(
            f"- Model preset: {_md(model.get('name'))} ({_md(model.get('format'))}, {format_metric(model.get('quant_bpw'), 1)} bpw)"
        )
        lines.append(f"- Weight dir: `{_md(model.get('weight_dir'))}`")
    observed = metadata.get("observed_gpus")
    if isinstance(observed, dict) and observed:
        lines.append("- GPUs observed via nvidia-smi:")
        for index in sorted(observed, key=lambda item: int(item) if str(item).isdigit() else str(item)):
            lines.append(f"  - GPU {index}: {_md(observed[index])}")
    else:
        lines.append("- GPUs observed via nvidia-smi: N/A (no samples). VRAM, power, temperature, and J/tok stay N/A.")
    protocol = metadata.get("protocol") if isinstance(metadata.get("protocol"), dict) else {}
    if protocol:
        lines.extend(["", "## Measurement protocol", ""])
        for key in ("ttft", "e2e", "decode_tps", "aggregate_tps", "joules_per_token", "percentile", "usage"):
            if key in protocol:
                lines.append(f"- {key}: {_md(protocol[key])}")
    lines.extend(
        [
            "",
            "## Results",
            "",
            "| Model | Quant (bpw) | Mode | Prompt tokens | Output tokens | Concurrency | TTFT p50 (ms) | TTFT p95 (ms) | Decode TPS | Aggregate TPS | Peak VRAM (MiB) | Mean Power (W) | J/tok | Peak Temp (C) | Measured prompt tokens | Measured completion tokens | Usage source |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    if not rows:
        lines.append("| No measured rows | | | | | | | | | | | | | | | | |")
    for row in rows:
        quant = _as_float(row.get("quant_bpw"))
        prompt_target = _as_int(row.get("prompt_tokens_target"))
        output_target = _as_int(row.get("output_tokens_target"))
        concurrency = _as_int(row.get("concurrency"))
        cells = [
            _md(row.get("model")),
            format_metric(quant, 1) if quant is not None else "N/A",
            _md(row.get("mode")),
            str(prompt_target) if prompt_target is not None else "N/A",
            str(output_target) if output_target is not None else "N/A",
            str(concurrency) if concurrency is not None else "N/A",
            format_metric(row.get("ttft_ms_p50"), 3),
            format_metric(row.get("ttft_ms_p95"), 3),
            format_metric(row.get("decode_tps_mean"), 3),
            format_metric(row.get("aggregate_tps"), 3),
            format_metric(row.get("peak_vram_mib"), 1),
            format_metric(row.get("mean_power_w"), 2),
            format_metric(row.get("joules_per_token"), 4),
            format_metric(row.get("peak_temp_c"), 1),
            format_metric(row.get("prompt_tokens_mean"), 3),
            format_metric(row.get("completion_tokens_mean"), 3),
            _md(row.get("usage_source") or "N/A"),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## Latency detail",
            "",
            "| Model | Mode | Prompt tokens | Output tokens | Concurrency | TTFT mean (ms) | E2E p50 (ms) | E2E p95 (ms) | E2E mean (ms) | Measured requests | Total completion tokens | Cell wall (s) | Telemetry samples |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not rows:
        lines.append("| No measured rows | | | | | | | | | | | | |")
    for row in rows:
        prompt_target = _as_int(row.get("prompt_tokens_target"))
        output_target = _as_int(row.get("output_tokens_target"))
        concurrency = _as_int(row.get("concurrency"))
        measured = _as_int(row.get("measured_requests"))
        total = _as_int(row.get("total_completion_tokens"))
        samples = _as_int(row.get("telemetry_samples"))
        detail = [
            _md(row.get("model")),
            _md(row.get("mode")),
            str(prompt_target) if prompt_target is not None else "N/A",
            str(output_target) if output_target is not None else "N/A",
            str(concurrency) if concurrency is not None else "N/A",
            format_metric(row.get("ttft_ms_mean"), 3),
            format_metric(row.get("e2e_ms_p50"), 3),
            format_metric(row.get("e2e_ms_p95"), 3),
            format_metric(row.get("e2e_ms_mean"), 3),
            str(measured) if measured is not None else "N/A",
            str(total) if total is not None else "N/A",
            format_metric(row.get("cell_wall_seconds"), 6),
            str(samples) if samples is not None else "N/A",
        ]
        lines.append("| " + " | ".join(detail) + " |")
    lines.extend(
        [
            "",
            "Decode TPS is the mean of per-request decode rates. Aggregate TPS is total completion tokens divided by the measured cell wall clock, excluding warmup. J/tok is mean GPU power (W) divided by aggregate TPS when nvidia-smi reported power and the rate is positive.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    out_dir: str | Path,
    source: str | Path | None = None,
    *,
    metadata: dict[str, object] | None = None,
    rows: list[dict[str, object]] | None = None,
) -> None:
    destination = Path(out_dir)
    if rows is None:
        metadata, rows = load_matrix(source if source is not None else destination / "matrix.json")
    elif metadata is None:
        metadata = {}
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "summary.md").write_text(render_summary(metadata, rows), encoding="utf-8")
    charts = destination / "charts"
    charts.mkdir(parents=True, exist_ok=True)
    (charts / "ttft_by_concurrency.svg").write_text(
        render_chart("TTFT p50 by concurrency", "TTFT p50 (ms)", rows, "ttft_ms_p50", 3),
        encoding="utf-8",
    )
    (charts / "tps_by_concurrency.svg").write_text(
        render_chart("Aggregate TPS by concurrency", "Aggregate TPS (tok/s)", rows, "aggregate_tps", 3),
        encoding="utf-8",
    )
