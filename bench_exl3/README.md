# Dual RTX 3090 EXL3 local inference benchmark

**Pending real execution on Dual RTX 3090.**

This directory is the measurement harness only. It does not ship placeholder TTFT, tokens/s, VRAM, power, temperature, or joules/token figures. Those cells stay empty until the commands below are run against live TabbyAPI on the water-cooled dual RTX 3090 machine. If an endpoint is down, the process exits non-zero and writes no matrix.

## Hardware and models

- GPUs: Dual NVIDIA RTX 3090 (2 x 24 GB), custom water-cooled, Windows.
- Backend: TabbyAPI (`ExLlamaV3`), matching `scripts/start_llm.ps1`.
- GPU 0: `http://127.0.0.1:5000/v1`
- GPU 1: `http://127.0.0.1:5001/v1`
- Weight root: `D:\models\exl3`

| Preset | Quant | Weight directory |
| --- | ---: | --- |
| `Qwen3.8-27B-Abliterated-EXL3-4.5bpw` | 4.5 bpw | `D:\models\exl3\Qwen3.8-27B-Abliterated-EXL3-4.5bpw` |
| `gemma-4-31B-it-uncensored-EXL3-4.0bpw` | 4.0 bpw | `D:\models\exl3\gemma-4-31B-it-uncensored-EXL3-4.0bpw` |

Load the preset under test in TabbyAPI before starting the matrix (`scripts/start_llm.ps1`, or the same ports and model names). The harness refuses to record rows when `GET /v1/models` does not list that preset.

Default matrix: prompt targets `512, 2048, 8192`; output caps `128, 512`; concurrency `1, 2, 4, 8`; modes `single-gpu` and `dual-gpu`.

## Measurement protocol

1. Preflight `GET /v1/models` on every endpoint the mode will use. Connection failure, timeout, non-200, or a model list that does not contain the preset aborts the run. No matrix file is written.
2. `single-gpu` sends every request to the first endpoint (port 5000 when using the launcher). `dual-gpu` round-robins request index across port 5000 and port 5001. Dual-gpu with fewer than two endpoints is an error.
3. Each cell builds one deterministic synthetic prompt (repeated technical paragraphs sized to the prompt target) and issues `--warmup` streaming requests that are discarded, then `--requests` measured requests at the cell concurrency (`ThreadPoolExecutor`).
4. Each measured call is `POST /v1/chat/completions` with `stream: true`, `stream_options.include_usage: true`, `temperature: 0.0`, and `max_tokens` set to the output length. Timing uses `time.perf_counter` from request dispatch.
5. TTFT is the delay until the first non-empty `delta.content` chunk. End-to-end latency runs until `data: [DONE]` or the stream closes.
6. Prompt and completion tokens come from the SSE `usage` object when the server sends it (`usage_source=server_usage`). If that object omits completion tokens, the completion count is the number of non-empty content deltas and `usage_source=chunk_count_fallback`. Prompt tokens are left null in that fallback. They are never replaced with the char/4 sizing estimate.
7. Per-request decode TPS is `(completion_tokens - 1) / ((e2e_ms - ttft_ms) / 1000)` when `completion_tokens > 1` and `e2e_ms > ttft_ms`, otherwise `completion_tokens / (e2e_ms / 1000)`.
8. Aggregate TPS is `total_completion_tokens / cell_wall_seconds` over the measured requests only. The wall clock is the concurrent cell, not the sum of per-request latencies.
9. p50 and p95 use Hyndman-Fan type 7 linear interpolation. Means are arithmetic means of the measured requests.
10. During the measured window a background thread polls `nvidia-smi` (default every 0.25 s) for `index,name,memory.used,memory.total,power.draw,temperature.gpu,utilization.gpu`. Peak VRAM is the max instantaneous sum across GPUs, and per-GPU peaks are stored separately. Mean/peak power use the sum of board power when every GPU in the sample reported power. J/tok is `mean_power_w / aggregate_tps` when both are present and greater than zero.
11. If `nvidia-smi` is not on `PATH`, or the explicit binary path does not exist, telemetry is unavailable. Peak VRAM, power, temperature, utilization, and J/tok are JSON `null`, CSV blank, and Markdown `N/A`. The harness does not invent those numbers and has no mock mode.
12. A non-200 response, timeout, empty stream, or malformed SSE event fails the cell. The process exits non-zero and does not publish a matrix for that attempt.

Runtime dependencies under `bench_exl3/` are the Python 3.10+ standard library (`http.client`, `subprocess`, and so on). No httpx, aiohttp, matplotlib, numpy, or pynvml package is required.

## One-line commands (Windows)

From the repository root, after both TabbyAPI ports are up for a full dual-GPU sweep:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bench_exl3\run_dual_3090_bench.ps1
```

List presets and the default `D:\models\exl3` paths:

```powershell
python -m bench_exl3 list-models
```

One live matrix (quote the comma-separated lists; PowerShell otherwise splits them):

```powershell
python -m bench_exl3 run --model Qwen3.8-27B-Abliterated-EXL3-4.5bpw --endpoints "http://127.0.0.1:5000/v1,http://127.0.0.1:5001/v1" --mode dual-gpu --prompt-lengths "512,2048,8192" --output-lengths "128,512" --concurrencies "1,2,4,8" --warmup 1 --timeout 600 --out-dir .\bench_results\Qwen3.8-27B-Abliterated-EXL3-4.5bpw\dual-gpu
```

Regenerate the Markdown summary and SVG charts from a matrix that run already wrote:

```powershell
python -m bench_exl3 report --input .\bench_results\Qwen3.8-27B-Abliterated-EXL3-4.5bpw\dual-gpu\matrix.json --out-dir .\bench_results\Qwen3.8-27B-Abliterated-EXL3-4.5bpw\dual-gpu
```

GPU 0 only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\bench_exl3\run_dual_3090_bench.ps1 -Mode single-gpu -Model Qwen3.8-27B-Abliterated-EXL3-4.5bpw
```

`--requests` is the number of measured calls per cell. Raise it on the 3090 host for tighter percentiles. Lowering it still executes real requests; it does not switch on a synthetic result path.

## Outputs

A successful cell writes:

- `requests.jsonl` — one object per measured request (warmup omitted), including `usage_source`.
- `matrix.csv` and `matrix.json` — per-cell p50/p95/mean TTFT and end-to-end latency, mean decode TPS, aggregate TPS, and telemetry. Null telemetry stays null.
- `summary.md` — one row per condition: model, quant, mode, prompt tokens, output tokens, concurrency, TTFT p50/p95, decode TPS, aggregate TPS, peak VRAM, mean power, J/tok, and peak temperature.
- `charts/ttft_by_concurrency.svg` and `charts/tps_by_concurrency.svg` — drawn from those rows with the standard library only.

Until the dual RTX 3090 host runs the launcher, there is no result table to publish. **Pending real execution on Dual RTX 3090.**
