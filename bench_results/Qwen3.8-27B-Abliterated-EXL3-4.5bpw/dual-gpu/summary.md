# EXL3 Dual RTX 3090 Benchmark Summary

Rows in this file are copied from the measured matrix. Missing telemetry is **N/A**. No benchmark number in this report is imputed.

## Hardware and environment

- Intended hardware: Dual NVIDIA RTX 3090 (2x 24 GB VRAM, custom water-cooled)
- Backend: TabbyAPI (ExLlamaV3)
- Host platform (this file): Windows-10-10.0.26100-SP0
- Python: 3.11.9
- Mode: dual-gpu
- Endpoints: http://127.0.0.1:5000/v1, http://127.0.0.1:5001/v1
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
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 128 | 1 | 401.069 | 556.336 | 37.311 | 33.638 | 36540.0 | 384.50 | 11.4307 | 47.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 128 | 2 | 228.265 | 447.537 | 37.046 | 67.684 | 36788.0 | 635.66 | 9.3916 | 47.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 128 | 4 | 382.967 | 558.181 | 33.316 | 118.934 | 36800.0 | 643.51 | 5.4106 | 48.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 128 | 8 | 645.066 | 917.676 | 30.099 | 206.305 | 36942.0 | 642.90 | 3.1163 | 49.0 | 567.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 512 | 1 | 404.163 | 544.642 | 36.610 | 35.648 | 36846.0 | 377.10 | 10.5784 | 49.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 512 | 2 | 227.550 | 415.467 | 36.856 | 71.901 | 36482.0 | 676.13 | 9.4037 | 50.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 512 | 4 | 379.512 | 611.100 | 33.627 | 130.003 | 36454.0 | 674.82 | 5.1908 | 51.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 512 | 512 | 8 | 542.762 | 853.680 | 30.412 | 233.764 | 36520.0 | 672.89 | 2.8785 | 51.0 | 567.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 128 | 1 | 599.855 | 753.792 | 37.296 | 31.958 | 36452.0 | 384.44 | 12.0298 | 49.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 128 | 2 | 441.250 | 639.135 | 37.307 | 64.624 | 36452.0 | 637.20 | 9.8601 | 51.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 128 | 4 | 607.042 | 1027.295 | 32.107 | 107.869 | 36452.0 | 642.70 | 5.9582 | 51.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 128 | 8 | 1238.652 | 1701.372 | 28.477 | 176.337 | 36452.0 | 650.55 | 3.6892 | 52.0 | 2210.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 512 | 1 | 603.739 | 741.945 | 36.880 | 35.408 | 36452.0 | 370.00 | 10.4495 | 51.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 512 | 2 | 448.386 | 607.088 | 36.802 | 71.032 | 36452.0 | 674.87 | 9.5010 | 51.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 512 | 4 | 684.956 | 989.227 | 33.332 | 127.122 | 36454.0 | 675.69 | 5.3153 | 52.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 2048 | 512 | 8 | 1231.090 | 1770.058 | 29.961 | 222.351 | 36454.0 | 668.09 | 3.0047 | 52.0 | 2210.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 128 | 1 | 4046.847 | 7394.157 | 36.413 | 16.988 | 36454.0 | 388.62 | 22.8765 | 52.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 128 | 2 | 345.533 | 535.360 | 36.319 | 64.698 | 36454.0 | 637.83 | 9.8585 | 52.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 128 | 4 | 533.462 | 813.020 | 31.499 | 109.207 | 36586.0 | 644.59 | 5.9025 | 52.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 128 | 8 | 913.759 | 1225.363 | 27.109 | 179.760 | 36450.0 | 647.05 | 3.5995 | 52.0 | 8792.000 | 128.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 512 | 1 | 411.533 | 492.016 | 35.867 | 34.928 | 36454.0 | 374.42 | 10.7198 | 52.0 | 8792.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 512 | 2 | 330.948 | 343.354 | 35.809 | 70.114 | 36450.0 | 680.19 | 9.7012 | 52.0 | 8792.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 512 | 4 | 531.613 | 818.364 | 31.874 | 122.698 | 36452.0 | 674.62 | 5.4982 | 52.0 | 8792.000 | 512.000 | server_usage |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | 4.5 | dual-gpu | 8192 | 512 | 8 | 917.080 | 1259.401 | 27.935 | 212.160 | 36452.0 | 668.82 | 3.1524 | 53.0 | 8792.000 | 512.000 | server_usage |

## Latency detail

| Model | Mode | Prompt tokens | Output tokens | Concurrency | TTFT mean (ms) | E2E p50 (ms) | E2E p95 (ms) | E2E mean (ms) | Measured requests | Total completion tokens | Cell wall (s) | Telemetry samples |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 128 | 1 | 401.069 | 3804.920 | 3951.375 | 3804.920 | 2 | 256 | 7.610463 | 25 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 128 | 2 | 292.435 | 3679.646 | 3860.712 | 3720.764 | 4 | 512 | 7.564575 | 25 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 128 | 4 | 405.363 | 4103.998 | 4524.411 | 4221.087 | 8 | 1024 | 8.609845 | 28 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 128 | 8 | 656.025 | 4755.330 | 5333.664 | 4882.942 | 16 | 2048 | 9.927049 | 32 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 512 | 1 | 404.163 | 14362.277 | 14455.669 | 14362.277 | 2 | 1024 | 28.724990 | 93 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 512 | 2 | 282.518 | 14102.697 | 14305.376 | 14147.258 | 4 | 2048 | 28.483767 | 92 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 512 | 4 | 409.974 | 15469.592 | 15981.303 | 15607.495 | 8 | 4096 | 31.506981 | 102 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 512 | 512 | 8 | 614.979 | 17324.176 | 17768.192 | 17419.676 | 16 | 8192 | 35.043881 | 113 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 128 | 1 | 599.855 | 4005.032 | 4154.733 | 4005.032 | 2 | 256 | 8.010564 | 26 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 128 | 2 | 497.161 | 3851.001 | 4036.116 | 3901.404 | 4 | 512 | 7.922709 | 26 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 128 | 4 | 686.482 | 4615.272 | 5051.890 | 4651.967 | 8 | 1024 | 9.493017 | 31 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 128 | 8 | 1241.784 | 5611.661 | 6572.021 | 5738.280 | 16 | 2048 | 11.614112 | 38 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 512 | 1 | 603.739 | 14459.595 | 14583.593 | 14459.595 | 2 | 1024 | 28.919658 | 94 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 512 | 2 | 491.015 | 14340.507 | 14471.903 | 14375.967 | 4 | 2048 | 28.832225 | 93 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 512 | 4 | 712.743 | 15958.022 | 16533.555 | 16046.052 | 8 | 4096 | 32.221125 | 104 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 2048 | 512 | 8 | 1275.251 | 18238.455 | 19192.109 | 18338.526 | 16 | 8192 | 36.842687 | 119 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 128 | 1 | 4046.847 | 7534.620 | 10878.166 | 7534.620 | 2 | 256 | 15.069817 | 49 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 128 | 2 | 396.690 | 3847.458 | 4032.301 | 3893.509 | 4 | 512 | 7.913658 | 26 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 128 | 4 | 572.099 | 4510.514 | 5013.057 | 4609.511 | 8 | 1024 | 9.376727 | 31 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 128 | 8 | 922.356 | 5525.329 | 6220.394 | 5623.317 | 16 | 2048 | 11.392973 | 37 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 512 | 1 | 411.533 | 14658.516 | 14727.102 | 14658.516 | 2 | 1024 | 29.317575 | 95 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 512 | 2 | 333.706 | 14604.039 | 14623.699 | 14603.800 | 4 | 2048 | 29.209584 | 95 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 512 | 4 | 567.893 | 16498.664 | 16994.907 | 16601.065 | 8 | 4096 | 33.382716 | 108 |
| Qwen3.8-27B-Abliterated-EXL3-4.5bpw | dual-gpu | 8192 | 512 | 8 | 936.713 | 19130.711 | 19817.497 | 19233.478 | 16 | 8192 | 38.612324 | 125 |

Decode TPS is the mean of per-request decode rates. Aggregate TPS is total completion tokens divided by the measured cell wall clock, excluding warmup. J/tok is mean GPU power (W) divided by aggregate TPS when nvidia-smi reported power and the rate is positive.
