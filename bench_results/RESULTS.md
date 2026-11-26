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

Full tables: [`single-gpu/summary.md`](Qwen3.8-27B-Abliterated-EXL3-4.5bpw/single-gpu/summary.md), [`dual-gpu/summary.md`](Qwen3.8-27B-Abliterated-EXL3-4.5bpw/dual-gpu/summary.md). Charts: `bench_results/Qwen3.8-27B-Abliterated-EXL3-4.5bpw/<mode>/charts/*.svg`.

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

Full tables: [`single-gpu/summary.md`](gemma-4-31B-it-uncensored-EXL3-4.0bpw/single-gpu/summary.md), [`dual-gpu/summary.md`](gemma-4-31B-it-uncensored-EXL3-4.0bpw/dual-gpu/summary.md). Charts: `bench_results/gemma-4-31B-it-uncensored-EXL3-4.0bpw/<mode>/charts/*.svg`.

<!-- BENCH_RESULTS_END -->
