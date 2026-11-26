# EXL3 Dual RTX 3090 Benchmark Summary

Rows in this file are copied from the measured matrix. Missing telemetry is **N/A**. No benchmark number in this report is imputed.

## Hardware and environment

- Intended hardware: Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)
- Backend: TabbyAPI (ExLlamaV3)
- Host platform (this file): Windows-10-10.0.26100-SP0
- Python: 3.11.9
- Mode: dual-gpu
- Endpoints: http://127.0.0.1:5000/v1, http://127.0.0.1:5001/v1
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
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 128 | 1 | 816.015 | 1303.285 | 33.425 | 27.731 | 46406.0 | 381.96 | 13.7739 | 49.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 128 | 2 | 284.496 | 516.213 | 33.511 | 60.863 | 46404.0 | 638.88 | 10.4970 | 49.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 128 | 4 | 462.537 | 631.467 | 28.792 | 103.116 | 46406.0 | 647.20 | 6.2764 | 50.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 128 | 8 | 808.842 | 1176.759 | 25.955 | 176.132 | 46406.0 | 636.84 | 3.6157 | 50.0 | 568.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 512 | 1 | 356.949 | 434.420 | 32.902 | 32.225 | 46408.0 | 368.78 | 11.4440 | 51.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 512 | 2 | 289.520 | 448.667 | 32.892 | 64.376 | 46410.0 | 676.63 | 10.5106 | 51.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 512 | 4 | 475.248 | 752.084 | 28.704 | 111.222 | 46410.0 | 672.35 | 6.0451 | 52.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 512 | 512 | 8 | 655.610 | 1081.451 | 25.756 | 197.952 | 46408.0 | 672.65 | 3.3980 | 53.0 | 568.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 128 | 1 | 1730.094 | 2723.061 | 32.623 | 22.762 | 46408.0 | 378.94 | 16.6475 | 51.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 128 | 2 | 610.833 | 798.987 | 32.658 | 55.562 | 46408.0 | 631.88 | 11.3724 | 52.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 128 | 4 | 1003.479 | 1385.882 | 26.632 | 87.235 | 46406.0 | 637.01 | 7.3022 | 53.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 128 | 8 | 2265.201 | 2395.705 | 23.804 | 137.124 | 46408.0 | 641.28 | 4.6767 | 53.0 | 2211.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 512 | 1 | 759.129 | 896.549 | 32.272 | 30.856 | 46410.0 | 366.95 | 11.8925 | 52.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 512 | 2 | 609.319 | 863.166 | 32.318 | 61.899 | 46408.0 | 666.36 | 10.7653 | 52.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 512 | 4 | 780.462 | 1318.501 | 27.398 | 103.986 | 46408.0 | 668.54 | 6.4291 | 54.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 2048 | 512 | 8 | 2305.353 | 2408.120 | 24.687 | 177.794 | 46582.0 | 667.06 | 3.7518 | 54.0 | 2211.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 128 | 1 | 5266.909 | 9615.953 | 31.927 | 13.845 | 46408.0 | 379.33 | 27.3975 | 54.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 128 | 2 | 459.791 | 652.048 | 32.004 | 56.589 | 46410.0 | 637.57 | 11.2668 | 53.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 128 | 4 | 823.628 | 979.492 | 26.700 | 91.257 | 46406.0 | 644.00 | 7.0570 | 53.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 128 | 8 | 1291.379 | 1855.473 | 22.039 | 141.793 | 46410.0 | 634.77 | 4.4768 | 53.0 | 8793.000 | 128.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 512 | 1 | 586.717 | 717.932 | 31.562 | 30.517 | 46410.0 | 371.45 | 12.1716 | 53.0 | 8793.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 512 | 2 | 449.676 | 564.041 | 31.580 | 61.334 | 46410.0 | 676.48 | 11.0294 | 53.0 | 8793.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 512 | 4 | 804.092 | 994.137 | 26.755 | 102.679 | 46410.0 | 675.02 | 6.5741 | 53.0 | 8793.000 | 512.000 | server_usage |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | 4.0 | dual-gpu | 8192 | 512 | 8 | 1616.718 | 1767.319 | 22.865 | 171.541 | 46410.0 | 670.37 | 3.9079 | 54.0 | 8793.000 | 512.000 | server_usage |

## Latency detail

| Model | Mode | Prompt tokens | Output tokens | Concurrency | TTFT mean (ms) | E2E p50 (ms) | E2E p95 (ms) | E2E mean (ms) | Measured requests | Total completion tokens | Cell wall (s) | Telemetry samples |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 128 | 1 | 816.015 | 4615.571 | 5100.591 | 4615.571 | 2 | 256 | 9.231577 | 30 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 128 | 2 | 349.765 | 4077.944 | 4299.918 | 4139.564 | 4 | 512 | 8.412318 | 28 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 128 | 4 | 473.807 | 4782.619 | 5181.382 | 4888.396 | 8 | 1024 | 9.930536 | 33 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 128 | 8 | 823.464 | 5552.364 | 6286.962 | 5727.524 | 16 | 2048 | 11.627646 | 38 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 512 | 1 | 356.949 | 15888.140 | 15954.170 | 15888.140 | 2 | 1024 | 31.776699 | 103 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 512 | 2 | 331.469 | 15827.784 | 15977.801 | 15866.961 | 4 | 2048 | 31.813172 | 103 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 512 | 4 | 508.298 | 18164.315 | 18694.138 | 18311.390 | 8 | 4096 | 36.827132 | 119 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 512 | 512 | 8 | 750.389 | 20502.721 | 21100.425 | 20591.778 | 16 | 8192 | 41.383682 | 134 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 128 | 1 | 1730.094 | 5623.051 | 6610.616 | 5623.051 | 2 | 256 | 11.246595 | 37 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 128 | 2 | 662.969 | 4498.385 | 4682.337 | 4551.737 | 4 | 512 | 9.214883 | 30 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 128 | 4 | 1041.307 | 5773.858 | 6465.266 | 5827.701 | 8 | 1024 | 11.738347 | 38 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 128 | 8 | 2035.043 | 7406.172 | 7473.365 | 7408.393 | 16 | 2048 | 14.935346 | 49 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 512 | 1 | 759.129 | 16593.153 | 16735.090 | 16593.153 | 2 | 1024 | 33.186789 | 107 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 512 | 2 | 683.191 | 16446.654 | 16658.296 | 16494.681 | 4 | 2048 | 33.086321 | 107 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 512 | 4 | 926.777 | 19477.258 | 20250.299 | 19585.430 | 8 | 4096 | 39.389771 | 127 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 2048 | 512 | 8 | 2302.918 | 22994.202 | 23136.410 | 23003.127 | 16 | 8192 | 46.075683 | 149 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 128 | 1 | 5266.909 | 9244.768 | 13584.040 | 9244.768 | 2 | 256 | 18.490064 | 60 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 128 | 2 | 508.752 | 4430.567 | 4615.577 | 4477.020 | 4 | 512 | 9.047699 | 30 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 128 | 4 | 796.119 | 5539.304 | 5660.380 | 5558.258 | 8 | 1024 | 11.221099 | 37 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 128 | 8 | 1334.519 | 7018.801 | 8021.648 | 7121.421 | 16 | 2048 | 14.443627 | 47 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 512 | 1 | 586.717 | 16777.004 | 16884.254 | 16777.004 | 2 | 1024 | 33.554535 | 109 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 512 | 2 | 481.989 | 16641.024 | 16733.590 | 16663.186 | 4 | 2048 | 33.390678 | 108 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 512 | 4 | 794.710 | 19889.831 | 19984.817 | 19895.575 | 8 | 4096 | 39.891491 | 129 |
| gemma-4-31B-it-uncensored-EXL3-4.0bpw | dual-gpu | 8192 | 512 | 8 | 1499.230 | 23862.774 | 23929.376 | 23853.009 | 16 | 8192 | 47.755314 | 154 |

Decode TPS is the mean of per-request decode rates. Aggregate TPS is total completion tokens divided by the measured cell wall clock, excluding warmup. J/tok is mean GPU power (W) divided by aggregate TPS when nvidia-smi reported power and the rate is positive.
