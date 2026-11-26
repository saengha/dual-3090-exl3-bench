# EXL3 Dual RTX 3090 Benchmark Summary

Rows in this file are copied from the measured matrix. Missing telemetry is **N/A**. No benchmark number in this report is imputed.

## Hardware and environment

- Intended hardware: Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)
- Backend: TabbyAPI (ExLlamaV3)
- Host platform (this file): Windows-10-10.0.26100-SP0
- Python: 3.11.9
- Mode: single-gpu
- Endpoints: http://127.0.0.1:5000/v1
- Model preset: Qwen3.8-27B-Abliterated-EXL3-4.5bpw (EXL3, 4.5 bpw)
- Weight dir: `D:\models\exl3\Qwen3.8-27B-Abliterated-EXL3-4.5bpw`
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
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 128 | 1 | 225.418 | 225.823 | 37.538 | 35.468 | 36532.0 | 364.12 | 10.2663 | 44.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 128 | 2 | 373.195 | 479.604 | 33.638 | 61.693 | 36536.0 | 363.37 | 5.8899 | 45.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 128 | 4 | 573.615 | 780.492 | 30.604 | 107.213 | 36538.0 | 362.96 | 3.3854 | 45.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 128 | 8 | 4736.735 | 5400.934 | 28.266 | 108.703 | 36540.0 | 361.35 | 3.3242 | 45.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 512 | 1 | 243.107 | 246.446 | 37.041 | 36.470 | 36592.0 | 365.78 | 10.0295 | 46.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 512 | 2 | 380.056 | 380.200 | 33.993 | 66.437 | 36598.0 | 364.80 | 5.4910 | 46.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 512 | 4 | 570.385 | 794.443 | 30.875 | 119.147 | 36598.0 | 364.32 | 3.0577 | 46.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 512 | 512 | 8 | 17197.784 | 17836.148 | 30.140 | 119.367 | 36596.0 | 364.36 | 3.0524 | 47.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 128 | 1 | 432.491 | 433.903 | 37.337 | 33.383 | 36540.0 | 361.60 | 10.8318 | 47.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 128 | 2 | 787.269 | 787.299 | 34.302 | 57.015 | 36540.0 | 360.68 | 6.3261 | 47.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 128 | 4 | 1190.655 | 1607.495 | 29.167 | 90.386 | 36540.0 | 361.77 | 4.0025 | 48.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 128 | 8 | 5668.337 | 7082.591 | 24.303 | 90.029 | 36540.0 | 358.70 | 3.9842 | 48.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 512 | 1 | 432.388 | 433.008 | 36.872 | 35.826 | 36540.0 | 363.15 | 10.1366 | 47.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 512 | 2 | 699.064 | 899.002 | 33.223 | 63.673 | 36540.0 | 360.19 | 5.6570 | 47.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 512 | 4 | 1504.577 | 1522.708 | 30.786 | 113.117 | 36592.0 | 363.35 | 3.2121 | 48.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 2048 | 512 | 8 | 18172.404 | 19684.757 | 28.855 | 112.890 | 36596.0 | 363.80 | 3.2226 | 48.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 128 | 1 | 327.718 | 327.850 | 36.356 | 33.497 | 36538.0 | 363.68 | 10.8571 | 47.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 128 | 2 | 607.211 | 640.751 | 32.445 | 56.611 | 36540.0 | 361.01 | 6.3771 | 48.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 128 | 4 | 1081.360 | 1096.033 | 28.802 | 93.260 | 36540.0 | 356.64 | 3.8241 | 48.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 128 | 8 | 5526.831 | 6595.451 | 24.734 | 93.118 | 36604.0 | 359.81 | 3.8640 | 48.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 512 | 1 | 326.261 | 327.807 | 35.938 | 35.200 | 36536.0 | 365.78 | 10.3915 | 48.0 | 8792.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 512 | 2 | 603.827 | 638.719 | 32.205 | 62.168 | 36536.0 | 365.25 | 5.8753 | 48.0 | 8792.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 512 | 4 | 1086.502 | 1124.873 | 28.480 | 107.597 | 36776.0 | 363.81 | 3.3812 | 48.0 | 8792.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | single-gpu | 8192 | 512 | 8 | 19066.141 | 20069.980 | 27.332 | 107.663 | 36548.0 | 363.59 | 3.3771 | 48.0 | 8792.000 | 512.000 | server_usage |

## Latency detail

| Model | Mode | Prompt tokens | Output tokens | Concurrency | TTFT mean (ms) | E2E p50 (ms) | E2E p95 (ms) | E2E mean (ms) | Measured requests | Total completion tokens | Cell wall (s) | Telemetry samples |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 128 | 1 | 225.418 | 3608.637 | 3609.386 | 3608.637 | 2 | 256 | 7.217842 | 24 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 128 | 2 | 363.957 | 4148.575 | 4164.545 | 4142.099 | 4 | 512 | 8.299129 | 27 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 128 | 4 | 611.469 | 4760.240 | 4792.066 | 4763.115 | 8 | 1024 | 9.551053 | 31 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 128 | 8 | 3889.743 | 9102.713 | 10072.104 | 8400.093 | 16 | 2048 | 18.840264 | 61 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 512 | 1 | 243.107 | 14038.558 | 14040.381 | 14038.558 | 2 | 1024 | 28.077559 | 91 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 512 | 2 | 380.076 | 15412.756 | 15422.771 | 15412.710 | 4 | 2048 | 30.826277 | 100 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 512 | 4 | 614.529 | 17169.574 | 17194.634 | 17165.774 | 8 | 4096 | 34.377774 | 111 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 512 | 512 | 8 | 13227.868 | 34010.939 | 34968.329 | 30186.675 | 16 | 8192 | 68.628695 | 221 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 128 | 1 | 432.491 | 3833.951 | 3835.118 | 3833.951 | 2 | 256 | 7.668463 | 25 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 128 | 2 | 787.224 | 4489.735 | 4491.411 | 4489.682 | 4 | 512 | 8.980079 | 30 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 128 | 4 | 1279.971 | 5653.257 | 5673.000 | 5641.603 | 8 | 1024 | 11.329209 | 37 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 128 | 8 | 4982.920 | 10714.341 | 12620.301 | 10263.082 | 16 | 2048 | 22.748139 | 74 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 512 | 1 | 432.388 | 14291.062 | 14299.168 | 14291.062 | 2 | 1024 | 28.582572 | 93 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 512 | 2 | 683.609 | 16073.785 | 16089.703 | 16067.290 | 4 | 2048 | 32.164507 | 104 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 512 | 4 | 1505.743 | 18104.175 | 18130.160 | 18104.297 | 8 | 4096 | 36.210175 | 117 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 2048 | 512 | 8 | 14390.392 | 35526.047 | 37801.363 | 32124.719 | 16 | 8192 | 72.566082 | 234 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 128 | 1 | 327.718 | 3820.972 | 3822.966 | 3820.972 | 2 | 256 | 7.642472 | 25 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 128 | 2 | 607.133 | 4521.874 | 4525.131 | 4521.705 | 4 | 512 | 9.044220 | 30 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 128 | 4 | 1079.836 | 5489.385 | 5502.715 | 5489.369 | 8 | 1024 | 10.980063 | 36 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 128 | 8 | 4704.979 | 10480.771 | 12047.798 | 9879.451 | 16 | 2048 | 21.993544 | 71 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 512 | 1 | 326.261 | 14545.197 | 14550.172 | 14545.197 | 2 | 1024 | 29.090935 | 94 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 512 | 2 | 603.777 | 16471.078 | 16479.662 | 16471.076 | 4 | 2048 | 32.943256 | 107 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 512 | 4 | 1090.927 | 19033.114 | 19035.386 | 19033.339 | 8 | 4096 | 38.068048 | 123 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | single-gpu | 8192 | 512 | 8 | 14839.434 | 37548.530 | 39060.502 | 33546.037 | 16 | 8192 | 76.088977 | 245 |

Decode TPS is the mean of per-request decode rates. Aggregate TPS is total completion tokens divided by the measured cell wall clock, excluding warmup. J/tok is mean GPU power (W) divided by aggregate TPS when nvidia-smi reported power and the rate is positive.
