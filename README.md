# Dual RTX 3090 EXL3 Local Inference Benchmark

Reproducible, Python standard-library-only inference benchmark harness measuring **TTFT**, **Decode TPS**, **Aggregate Throughput TPS**, **Peak VRAM**, **Board Power (W)**, **GPU Temperature (°C)**, and **Joules/token** on a custom water-cooled Dual NVIDIA RTX 3090 (2 × 24 GB) workstation running **TabbyAPI (`ExLlamaV3`)**.

> **Status: Pending real execution on Dual RTX 3090.**
> This repository intentionally ships **zero placeholder or mock benchmark numbers**. If a TabbyAPI endpoint is unreachable, returns a non-200 status, or emits an empty/malformed SSE stream, the runner fails closed (non-zero exit, zero matrix rows written).

## Hardware & Models Under Test

- **GPUs**: 2 × NVIDIA RTX 3090 (24 GB VRAM each, custom water-cooled), Windows
- **Serving Stack**: TabbyAPI (`ExLlamaV3`) — GPU 0 on `http://127.0.0.1:5000/v1`, GPU 1 on `http://127.0.0.1:5001/v1` (see [`scripts/start_tabby_exl3.ps1`](scripts/start_tabby_exl3.ps1))
- **Model Weights Root**: `D:\models\exl3`

| Model Preset | Format | Quantization | Weight Path |
| --- | --- | ---: | --- |
| `Qwen3.8-27B-Abliterated-EXL3-4.5bpw` | EXL3 | 4.5 bpw | `D:\models\exl3\Qwen3.8-27B-Abliterated-EXL3-4.5bpw` |
| `gemma-4-31B-it-uncensored-EXL3-4.0bpw` | EXL3 | 4.0 bpw | `D:\models\exl3\gemma-4-31B-it-uncensored-EXL3-4.0bpw` |

## Measurement Matrix & Protocol

Numbers without measurement conditions are meaningless. Every row in `matrix.csv`, `matrix.json`, and `summary.md` explicitly records all experimental conditions:

- **Prompt Lengths (target tokens)**: `512`, `2048`, `8192` (plus exact server-reported `usage.prompt_tokens`)
- **Output Lengths (`max_tokens`)**: `128`, `512` (plus exact server-reported `usage.completion_tokens`)
- **Concurrency Levels**: `1`, `2`, `4`, `8` (`measured_requests` defaults to `concurrency × 2`; under-saturated explicit `--requests < max(concurrencies)` is rejected)
- **GPU Modes**: `single-gpu` (`:5000`) and `dual-gpu` (`:5000` + `:5001` round-robin concurrent dispatch)
- **Warmup**: `1` request per cell (discarded from metrics)
- **Telemetry**: Background `nvidia-smi` polling every `0.25 s` for per-GPU & total Peak VRAM (MiB), Mean/Peak Power (W), Peak Temp (°C), GPU utilization (%), and `Joules / token = mean_power_w / aggregate_tps` (`null` / `N/A` if `nvidia-smi` is unavailable)
- **Runtime Dependencies**: Python 3.10+ standard library only (zero pip installs required to run benchmarks or render SVG charts)

## Quick Start (Windows / PowerShell)

```powershell
# 1. Launch TabbyAPI on GPU 0 (:5000) and GPU 1 (:5001)
$env:EXL_MODEL_NAME_A = "Qwen3.8-27B-Abliterated-EXL3-4.5bpw"
$env:EXL_MODEL_NAME_B = "Qwen3.8-27B-Abliterated-EXL3-4.5bpw"
.\scripts\start_tabby_exl3.ps1

# 2. Run the full single-gpu + dual-gpu sweep (auto-detects the loaded preset on :5000)
powershell -NoProfile -ExecutionPolicy Bypass -File .\bench_exl3\run_dual_3090_bench.ps1
```

Outputs are written under `bench_results/<model>/<mode>/`:
- `requests.jsonl` — per-request raw timings & token counts
- `matrix.csv` & `matrix.json` — aggregated p50/p95/mean TTFT, E2E, decode TPS, aggregate TPS, VRAM, power, J/tok, temp
- `summary.md` — README-ready Markdown table
- `charts/ttft_by_concurrency.svg` & `charts/tps_by_concurrency.svg` — pure-Python SVG charts

## Running Unit Tests

```bash
pip install pytest
pytest tests/ -v
```

See [`bench_exl3/README.md`](bench_exl3/README.md) for full protocol equations and CLI flags.
