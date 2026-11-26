# Dual RTX 3090 EXL3 local inference benchmark

**Measured on Dual RTX 3090 (2026-11-26/27 KST); results below and in `bench_results/`.**

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

Until the dual RTX 3090 host runs the launcher, there is no result table to publish. **Measured on Dual RTX 3090 (2026-11-26/27 KST); results below and in `bench_results/`.**

<!-- BENCH_RESULTS_START -->
## Measured results (Dual RTX 3090, live TabbyAPI, 2026-11-26/27 KST)

All numbers below are copied from `bench_results/<model>/<mode>/matrix.csv` produced by live runs on the dual RTX 3090 host (i9-12900KS, 128 GB RAM, Windows 11, no NVLink; each GPU runs its own full copy of the model). No value is estimated or mocked; a missing cell would be shown as FAIL.

Server config (`scripts/start_llm.ps1` in us-revenue-llm-harness, identical to `scripts/start_tabby_exl3.ps1` in dual-3090-exl3-bench): TabbyAPI ExLlamaV3, `max_seq_len`/`cache_size` 16384, `cache_mode: Q4`, TabbyAPI default `max_batch_size` 4 per instance. `single-gpu` = all requests to :5000 (GPU 0); `dual-gpu` = round-robin over :5000 (GPU 0) and :5001 (GPU 1). Measured requests per cell = 2 x concurrency, 1 warmup. Requests use `min_tokens = max_tokens` so every request decodes exactly the target output length.

Caveats: (1) each cell reuses one identical prompt and the warmup goes to :5000, so TabbyAPI prefix caching makes most TTFT values reflect cached prefill; the dual-gpu concurrency-1 rows show cold prefill on GPU 1. (2) Peak VRAM / power are sums over both GPUs even in single-gpu mode (the idle GPU still holds its copy of the model); see `peak_vram_mib_per_gpu` in matrix.csv. (3) Concurrency 8 exceeds `max_batch_size` 4 per instance, so single-gpu c=8 queues requests (large TTFT).

### Qwen3.8-27B-Abliterated-EXL3-4.5bpw

| Prompt | Output | Conc. | TTFT p50 single (ms) | TTFT p50 dual (ms) | Decode TPS single | Decode TPS dual | Aggregate TPS single | Aggregate TPS dual | Dual/Single agg. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 128 | 1 | 225 | 401 | 37.5 | 37.3 | 35.5 | 33.6 | 0.95x |
| 512 | 128 | 2 | 373 | 228 | 33.6 | 37.0 | 61.7 | 67.7 | 1.10x |
| 512 | 128 | 4 | 574 | 383 | 30.6 | 33.3 | 107.2 | 118.9 | 1.11x |
| 512 | 128 | 8 | 4737 | 645 | 28.3 | 30.1 | 108.7 | 206.3 | 1.90x |
| 512 | 512 | 1 | 243 | 404 | 37.0 | 36.6 | 36.5 | 35.6 | 0.98x |
| 512 | 512 | 2 | 380 | 228 | 34.0 | 36.9 | 66.4 | 71.9 | 1.08x |
| 512 | 512 | 4 | 570 | 380 | 30.9 | 33.6 | 119.1 | 130.0 | 1.09x |
| 512 | 512 | 8 | 17198 | 543 | 30.1 | 30.4 | 119.4 | 233.8 | 1.96x |
| 2048 | 128 | 1 | 432 | 600 | 37.3 | 37.3 | 33.4 | 32.0 | 0.96x |
| 2048 | 128 | 2 | 787 | 441 | 34.3 | 37.3 | 57.0 | 64.6 | 1.13x |
| 2048 | 128 | 4 | 1191 | 607 | 29.2 | 32.1 | 90.4 | 107.9 | 1.19x |
| 2048 | 128 | 8 | 5668 | 1239 | 24.3 | 28.5 | 90.0 | 176.3 | 1.96x |
| 2048 | 512 | 1 | 432 | 604 | 36.9 | 36.9 | 35.8 | 35.4 | 0.99x |
| 2048 | 512 | 2 | 699 | 448 | 33.2 | 36.8 | 63.7 | 71.0 | 1.12x |
| 2048 | 512 | 4 | 1505 | 685 | 30.8 | 33.3 | 113.1 | 127.1 | 1.12x |
| 2048 | 512 | 8 | 18172 | 1231 | 28.9 | 30.0 | 112.9 | 222.4 | 1.97x |
| 8192 | 128 | 1 | 328 | 4047 | 36.4 | 36.4 | 33.5 | 17.0 | 0.51x |
| 8192 | 128 | 2 | 607 | 346 | 32.4 | 36.3 | 56.6 | 64.7 | 1.14x |
| 8192 | 128 | 4 | 1081 | 533 | 28.8 | 31.5 | 93.3 | 109.2 | 1.17x |
| 8192 | 128 | 8 | 5527 | 914 | 24.7 | 27.1 | 93.1 | 179.8 | 1.93x |
| 8192 | 512 | 1 | 326 | 412 | 35.9 | 35.9 | 35.2 | 34.9 | 0.99x |
| 8192 | 512 | 2 | 604 | 331 | 32.2 | 35.8 | 62.2 | 70.1 | 1.13x |
| 8192 | 512 | 4 | 1087 | 532 | 28.5 | 31.9 | 107.6 | 122.7 | 1.14x |
| 8192 | 512 | 8 | 19066 | 917 | 27.3 | 27.9 | 107.7 | 212.2 | 1.97x |

Full tables: [`single-gpu/summary.md`](../bench_results/Qwen3.8-27B-Abliterated-EXL3-4.5bpw/single-gpu/summary.md), [`dual-gpu/summary.md`](../bench_results/Qwen3.8-27B-Abliterated-EXL3-4.5bpw/dual-gpu/summary.md). Charts: `bench_results/Qwen3.8-27B-Abliterated-EXL3-4.5bpw/<mode>/charts/*.svg`.

### gemma-4-31B-it-uncensored-EXL3-4.0bpw

| Prompt | Output | Conc. | TTFT p50 single (ms) | TTFT p50 dual (ms) | Decode TPS single | Decode TPS dual | Aggregate TPS single | Aggregate TPS dual | Dual/Single agg. |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 128 | 1 | 288 | 816 | 33.5 | 33.4 | 31.4 | 27.7 | 0.88x |
| 512 | 128 | 2 | 470 | 284 | 28.7 | 33.5 | 52.3 | 60.9 | 1.16x |
| 512 | 128 | 4 | 723 | 463 | 26.3 | 28.8 | 90.5 | 103.1 | 1.14x |
| 512 | 128 | 8 | 5533 | 809 | 24.3 | 26.0 | 93.2 | 176.1 | 1.89x |
| 512 | 512 | 1 | 285 | 357 | 32.9 | 32.9 | 32.4 | 32.2 | 1.00x |
| 512 | 512 | 2 | 466 | 290 | 28.7 | 32.9 | 56.1 | 64.4 | 1.15x |
| 512 | 512 | 4 | 836 | 475 | 26.2 | 28.7 | 100.7 | 111.2 | 1.10x |
| 512 | 512 | 8 | 20450 | 656 | 25.4 | 25.8 | 100.5 | 198.0 | 1.97x |
| 2048 | 128 | 1 | 611 | 1730 | 32.6 | 32.6 | 28.4 | 22.8 | 0.80x |
| 2048 | 128 | 2 | 1136 | 611 | 28.2 | 32.7 | 45.4 | 55.6 | 1.22x |
| 2048 | 128 | 4 | 2198 | 1003 | 24.9 | 26.6 | 70.2 | 87.2 | 1.24x |
| 2048 | 128 | 8 | 7324 | 2265 | 19.4 | 23.8 | 70.2 | 137.1 | 1.95x |
| 2048 | 512 | 1 | 608 | 759 | 32.2 | 32.3 | 31.1 | 30.9 | 0.99x |
| 2048 | 512 | 2 | 1137 | 609 | 27.9 | 32.3 | 52.7 | 61.9 | 1.17x |
| 2048 | 512 | 4 | 2166 | 780 | 24.7 | 27.4 | 89.6 | 104.0 | 1.16x |
| 2048 | 512 | 8 | 22862 | 2305 | 23.0 | 24.7 | 89.6 | 177.8 | 1.99x |
| 8192 | 128 | 1 | 448 | 5267 | 31.9 | 31.9 | 28.9 | 13.8 | 0.48x |
| 8192 | 128 | 2 | 794 | 460 | 27.2 | 32.0 | 46.7 | 56.6 | 1.21x |
| 8192 | 128 | 4 | 1486 | 824 | 23.4 | 26.7 | 73.9 | 91.3 | 1.23x |
| 8192 | 128 | 8 | 6974 | 1291 | 19.7 | 22.0 | 73.9 | 141.8 | 1.92x |
| 8192 | 512 | 1 | 437 | 587 | 31.5 | 31.6 | 30.8 | 30.5 | 0.99x |
| 8192 | 512 | 2 | 798 | 450 | 26.9 | 31.6 | 51.7 | 61.3 | 1.19x |
| 8192 | 512 | 4 | 1490 | 804 | 23.1 | 26.8 | 86.8 | 102.7 | 1.18x |
| 8192 | 512 | 8 | 23711 | 1617 | 22.0 | 22.9 | 86.6 | 171.5 | 1.98x |

Full tables: [`single-gpu/summary.md`](../bench_results/gemma-4-31B-it-uncensored-EXL3-4.0bpw/single-gpu/summary.md), [`dual-gpu/summary.md`](../bench_results/gemma-4-31B-it-uncensored-EXL3-4.0bpw/dual-gpu/summary.md). Charts: `bench_results/gemma-4-31B-it-uncensored-EXL3-4.0bpw/<mode>/charts/*.svg`.

<!-- BENCH_RESULTS_END -->
