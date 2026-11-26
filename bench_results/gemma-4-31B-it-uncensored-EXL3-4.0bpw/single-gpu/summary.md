# EXL3 Dual RTX 3090 Benchmark Summary

Rows in this file are copied from the measured matrix. Missing telemetry is **N/A**. No benchmark number in this report is imputed.

## Hardware and environment

- Intended hardware: Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)
- Backend: TabbyAPI (ExLlamaV3)
- Host platform (this file): Windows-10-10.0.26100-SP0
- Python: 3.11.9
- Mode: single-gpu
- Endpoints: http://127.0.0.1:5000/v1
- Model preset: gemma-4-31B-it-uncensored-EXL3-4.0bpw (EXL3, 4.0 bpw)
- Weight dir: `D:\models\exl3\gemma-4-31B-it-uncensored-EXL3-4.0bpw`
- GPUs observed via nvidia-smi:
  - GPU 0: NVIDIA GeForce RTX 3090
  - GPU 1: NVIDIA GeForce RTX 3090

## Measurement protocol

- ttft: perf_counter from request dispatch to the first non-empty content delta
- e2e: perf_counter from request dispatch until [DONE] or stream close
- decode_tps: (completion_tokens - 1) / ((e2e_ms - ttft_ms) / 1000) when completion_tokens > 1 and e2e_ms > ttft_ms, else completion_tokens / (e2e_ms / 1000)
- aggregate_tps: total_completion_tokens / cell_wall_seconds
- joules_per_token: mean_power_w / aggregate_tps when both are present and > 0
- percentile: Hyndman-Fan type 7 linear interpolation
- usage: server usage.prompt_tokens and usage.completion_tokens; completion falls back to non-empty content-delta chunks only when usage is omitted

## Results

| Model | Quant (bpw) | Mode | Prompt tokens | Output tokens | Concurrency | TTFT p50 (ms) | TTFT p95 (ms) | Decode TPS | Aggregate TPS | Peak VRAM (MiB) | Mean Power (W) | J/tok | Peak Temp (C) | Measured prompt tokens | Measured completion tokens | Usage source |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 128 | 1 | 288.001 | 296.453 | 33.497 | 31.376 | 45764.0 | 360.20 | 11.4804 | 48.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 128 | 2 | 470.229 | 610.331 | 28.734 | 52.267 | 45790.0 | 360.82 | 6.9034 | 48.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 128 | 4 | 722.805 | 1032.573 | 26.265 | 90.498 | 45952.0 | 356.31 | 3.9372 | 48.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 128 | 8 | 5533.345 | 6312.165 | 24.261 | 93.151 | 45954.0 | 357.81 | 3.8412 | 48.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 512 | 1 | 285.102 | 293.421 | 32.917 | 32.386 | 45954.0 | 365.82 | 11.2957 | 49.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 512 | 2 | 466.180 | 594.226 | 28.726 | 56.087 | 45954.0 | 362.48 | 6.4628 | 49.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 512 | 4 | 836.357 | 852.810 | 26.201 | 100.692 | 46004.0 | 363.69 | 3.6119 | 49.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 512 | 512 | 8 | 20450.403 | 21215.348 | 25.377 | 100.474 | 46004.0 | 361.83 | 3.6013 | 49.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 128 | 1 | 610.832 | 614.936 | 32.625 | 28.420 | 46398.0 | 355.79 | 12.5188 | 49.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 128 | 2 | 1136.044 | 1138.444 | 28.207 | 45.400 | 46398.0 | 352.18 | 7.7571 | 49.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 128 | 4 | 2197.944 | 2229.178 | 24.906 | 70.159 | 46398.0 | 349.96 | 4.9880 | 49.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 128 | 8 | 7324.473 | 9485.405 | 19.360 | 70.218 | 46398.0 | 348.76 | 4.9669 | 49.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 512 | 1 | 607.616 | 608.600 | 32.241 | 31.111 | 46398.0 | 357.28 | 11.4843 | 49.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 512 | 2 | 1137.412 | 1143.548 | 27.925 | 52.685 | 46398.0 | 355.95 | 6.7562 | 49.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 512 | 4 | 2166.269 | 2191.428 | 24.708 | 89.617 | 46398.0 | 356.53 | 3.9784 | 49.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 2048 | 512 | 8 | 22862.091 | 25213.881 | 22.976 | 89.551 | 46398.0 | 359.19 | 4.0110 | 49.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 128 | 1 | 448.041 | 458.269 | 31.870 | 28.873 | 46402.0 | 361.48 | 12.5195 | 49.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 128 | 2 | 794.330 | 825.868 | 27.173 | 46.736 | 46398.0 | 357.73 | 7.6543 | 49.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 128 | 4 | 1485.751 | 1518.342 | 23.367 | 73.916 | 46402.0 | 355.05 | 4.8034 | 49.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 128 | 8 | 6973.799 | 8421.010 | 19.714 | 73.888 | 46456.0 | 354.05 | 4.7917 | 49.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 512 | 1 | 436.611 | 438.492 | 31.526 | 30.759 | 46406.0 | 364.49 | 11.8498 | 49.0 | 8793.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 512 | 2 | 798.366 | 802.425 | 26.874 | 51.683 | 46460.0 | 362.57 | 7.0154 | 49.0 | 8793.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 512 | 4 | 1489.823 | 1494.918 | 23.115 | 86.791 | 46456.0 | 361.18 | 4.1615 | 49.0 | 8793.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | single-gpu | 8192 | 512 | 8 | 23711.113 | 25152.789 | 22.013 | 86.574 | 46754.0 | 361.52 | 4.1759 | 49.0 | 8793.000 | 512.000 | server_usage |

## Latency detail

| Model | Mode | Prompt tokens | Output tokens | Concurrency | TTFT mean (ms) | E2E p50 (ms) | E2E p95 (ms) | E2E mean (ms) | Measured requests | Total completion tokens | Cell wall (s) | Telemetry samples |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 128 | 1 | 288.001 | 4079.370 | 4096.598 | 4079.370 | 2 | 256 | 8.159229 | 27 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 128 | 2 | 458.239 | 4877.811 | 4913.198 | 4882.036 | 4 | 512 | 9.795838 | 32 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 128 | 4 | 794.743 | 5624.874 | 5677.504 | 5632.915 | 8 | 1024 | 11.315151 | 37 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 128 | 8 | 4555.697 | 10599.290 | 11779.124 | 9813.472 | 16 | 2048 | 21.985796 | 71 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 512 | 1 | 285.102 | 15809.208 | 15824.190 | 15809.208 | 2 | 1024 | 31.618814 | 102 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 512 | 2 | 451.332 | 18256.056 | 18259.324 | 18241.260 | 4 | 2048 | 36.514528 | 118 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 512 | 4 | 835.370 | 20338.637 | 20343.526 | 20338.746 | 8 | 4096 | 40.678466 | 131 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 512 | 512 | 8 | 15741.208 | 40382.065 | 41594.702 | 35884.547 | 16 | 8192 | 81.533142 | 263 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 128 | 1 | 610.832 | 4503.579 | 4505.057 | 4503.579 | 2 | 256 | 9.007588 | 30 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 128 | 2 | 1136.054 | 5638.418 | 5644.049 | 5638.412 | 4 | 512 | 11.277421 | 37 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 128 | 4 | 2197.778 | 7297.186 | 7313.822 | 7297.189 | 8 | 1024 | 14.595443 | 47 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 128 | 8 | 6582.722 | 13515.614 | 16740.529 | 13288.233 | 16 | 2048 | 29.166430 | 94 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 512 | 1 | 607.616 | 16457.185 | 16465.943 | 16457.185 | 2 | 1024 | 32.914850 | 107 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 512 | 2 | 1137.400 | 19436.139 | 19448.180 | 19436.125 | 4 | 2048 | 38.872875 | 125 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 512 | 4 | 2170.634 | 22852.236 | 22954.714 | 22852.276 | 8 | 4096 | 45.705574 | 148 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 2048 | 512 | 8 | 18285.454 | 44576.832 | 48005.903 | 40568.785 | 16 | 8192 | 91.478283 | 295 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 128 | 1 | 448.041 | 4432.944 | 4437.600 | 4432.944 | 2 | 256 | 8.866354 | 29 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 128 | 2 | 803.388 | 5477.193 | 5491.404 | 5477.158 | 4 | 512 | 10.955088 | 36 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 128 | 4 | 1491.051 | 6926.150 | 6957.615 | 6926.186 | 8 | 1024 | 13.853485 | 45 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 128 | 8 | 5977.504 | 13148.592 | 15321.694 | 12483.455 | 16 | 2048 | 27.717505 | 90 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 512 | 1 | 436.611 | 16645.337 | 16649.422 | 16645.337 | 2 | 1024 | 33.291243 | 108 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 512 | 2 | 798.355 | 19812.771 | 19813.625 | 19812.800 | 4 | 2048 | 39.626384 | 128 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 512 | 4 | 1489.749 | 23596.539 | 23617.574 | 23596.321 | 8 | 4096 | 47.193740 | 153 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | single-gpu | 8192 | 512 | 8 | 18535.731 | 46587.224 | 48785.461 | 41767.659 | 16 | 8192 | 94.624777 | 305 |

Decode TPS is the mean of per-request decode rates. Aggregate TPS is total completion tokens divided by the measured cell wall clock, excluding warmup. J/tok is mean GPU power (W) divided by aggregate TPS when nvidia-smi reported power and the rate is positive.
