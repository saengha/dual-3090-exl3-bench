"""nvidia-smi polling for VRAM, power, temperature, and utilization.

If the nvidia-smi binary is missing or returns no parseable samples, every
measured field is None. This module does not substitute zeros or sample data.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

NVIDIA_SMI_QUERY = "index,name,memory.used,memory.total,power.draw,temperature.gpu,utilization.gpu"
_NA_TOKENS = {
    "",
    "n/a",
    "[n/a]",
    "[not supported]",
    "not supported",
    "[insufficient permissions]",
    "insufficient permissions",
    "[unknown error]",
}
_UNIT_SUFFIXES = ("mib", "mb", "w", "c", "%")


@dataclass(frozen=True)
class GpuSample:
    index: int
    name: str
    memory_used_mib: float | None
    memory_total_mib: float | None
    power_draw_w: float | None
    temperature_c: float | None
    utilization_gpu_pct: float | None


def _parse_number(token: str) -> float | None:
    text = token.strip()
    lowered = text.lower()
    if lowered in _NA_TOKENS:
        return None
    for suffix in _UNIT_SUFFIXES:
        if lowered.endswith(suffix):
            text = text[: -len(suffix)].strip()
            lowered = text.lower()
            break
    if lowered in _NA_TOKENS:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_index(token: str) -> int | None:
    number = _parse_number(token)
    if number is None or not number.is_integer():
        return None
    return int(number)


def parse_nvidia_smi_csv(output: str) -> list[GpuSample]:
    """Parse nvidia-smi CSV rows for the benchmark query fields.

    Header rows are ignored. `[N/A]` and blank numeric fields stay None.
    A GPU name that itself contains commas is preserved when the row has
    more than seven CSV fields: the last five fields are the numeric columns.
    """

    samples: list[GpuSample] = []
    text = output.replace("\r\n", "\n").replace("\r", "\n")
    for line in text.split("\n"):
        if not line.strip():
            continue
        parts = next(csv.reader([line]))
        if len(parts) < 7:
            continue
        if len(parts) == 7:
            raw = parts
            name = raw[1].strip()
            numeric = raw[2:]
        else:
            name = ",".join(part.strip() for part in parts[1:-5]).strip()
            numeric = parts[-5:]
        index = _parse_index(parts[0])
        if index is None:
            continue
        memory_used, memory_total, power, temp, util = (_parse_number(item) for item in numeric)
        samples.append(
            GpuSample(
                index=index,
                name=name,
                memory_used_mib=memory_used,
                memory_total_mib=memory_total,
                power_draw_w=power,
                temperature_c=temp,
                utilization_gpu_pct=util,
            )
        )
    return samples


def empty_telemetry() -> dict[str, object]:
    return {
        "samples_count": 0,
        "peak_vram_mib": None,
        "peak_vram_mib_per_gpu": None,
        "mean_power_w": None,
        "peak_power_w": None,
        "peak_temp_c": None,
        "mean_gpu_util_pct": None,
        "gpu_names": None,
        "memory_total_mib_per_gpu": None,
    }


def summarize_samples(samples: list[list[GpuSample]]) -> dict[str, object]:
    """Aggregate polled GPU samples.

    `peak_vram_mib` is the maximum instantaneous sum of `memory.used` across
    GPUs. A sample contributes to that sum, and to power, only when every GPU
    in the sample reported that field. Missing readings are not treated as zero.
    Per-GPU VRAM peaks still use the readings that were actually present.
    """

    per_gpu_peak: dict[str, float] = {}
    per_gpu_name: dict[str, str] = {}
    per_gpu_total: dict[str, float] = {}
    vram_sums: list[float] = []
    power_sums: list[float] = []
    temps: list[float] = []
    utils: list[float] = []

    for sample in samples:
        if not sample:
            continue
        memory_values: list[float] = []
        power_values: list[float] = []
        memory_complete = True
        power_complete = True
        for gpu in sample:
            key = str(gpu.index)
            per_gpu_name[key] = gpu.name
            if gpu.memory_total_mib is not None:
                per_gpu_total[key] = gpu.memory_total_mib
            if gpu.memory_used_mib is None:
                memory_complete = False
            else:
                memory_values.append(gpu.memory_used_mib)
                previous = per_gpu_peak.get(key)
                if previous is None or gpu.memory_used_mib > previous:
                    per_gpu_peak[key] = gpu.memory_used_mib
            if gpu.power_draw_w is None:
                power_complete = False
            else:
                power_values.append(gpu.power_draw_w)
            if gpu.temperature_c is not None:
                temps.append(gpu.temperature_c)
            if gpu.utilization_gpu_pct is not None:
                utils.append(gpu.utilization_gpu_pct)
        if memory_complete and memory_values:
            vram_sums.append(sum(memory_values))
        if power_complete and power_values:
            power_sums.append(sum(power_values))

    def mean(values: list[float]) -> float | None:
        if not values:
            return None
        return sum(values) / len(values)

    return {
        "samples_count": len(samples),
        "peak_vram_mib": max(vram_sums) if vram_sums else None,
        "peak_vram_mib_per_gpu": per_gpu_peak or None,
        "mean_power_w": mean(power_sums),
        "peak_power_w": max(power_sums) if power_sums else None,
        "peak_temp_c": max(temps) if temps else None,
        "mean_gpu_util_pct": mean(utils),
        "gpu_names": per_gpu_name or None,
        "memory_total_mib_per_gpu": per_gpu_total or None,
    }


class GpuTelemetrySampler:
    """Poll nvidia-smi on a daemon thread for the duration of one benchmark cell."""

    def __init__(self, interval_s: float = 0.25, nvidia_smi_bin: str | None = None) -> None:
        if interval_s <= 0:
            raise ValueError("interval_s must be positive")
        self.interval_s = interval_s
        self.nvidia_smi_bin = nvidia_smi_bin
        self.available = False
        self.error: str | None = None
        self.summary: dict[str, object] = {"available": False, "error": None, **empty_telemetry()}
        self._binary: str | None = None
        self._samples: list[list[GpuSample]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _resolve_binary(self) -> str | None:
        if self.nvidia_smi_bin is not None:
            candidate = Path(self.nvidia_smi_bin)
            if candidate.is_file():
                return str(candidate)
            return None
        found = shutil.which("nvidia-smi")
        if not found:
            return None
        return found

    def _command(self) -> list[str]:
        assert self._binary is not None
        return [
            self._binary,
            f"--query-gpu={NVIDIA_SMI_QUERY}",
            "--format=csv,noheader,nounits",
        ]

    def _poll_once(self) -> None:
        if self._binary is None:
            self.available = False
            self.error = "nvidia-smi not found"
            return
        try:
            proc = subprocess.run(
                self._command(),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except FileNotFoundError:
            self.available = False
            self.error = "nvidia-smi not found"
            return
        except subprocess.TimeoutExpired:
            self.error = "nvidia-smi timed out"
            if not self._samples:
                self.available = False
            return
        except OSError as exc:
            self.available = False
            self.error = f"nvidia-smi failed to start: {exc}"
            return
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "nvidia-smi failed").strip()
            self.error = detail[:500] or "nvidia-smi failed"
            if not self._samples:
                self.available = False
            return
        parsed = parse_nvidia_smi_csv(proc.stdout)
        if not parsed:
            self.error = "nvidia-smi returned no GPU rows"
            if not self._samples:
                self.available = False
            return
        self._samples.append(parsed)
        self.available = True
        self.error = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self._stop.wait(self.interval_s):
                return
            self._poll_once()
            if not self.available and self.error == "nvidia-smi not found":
                return

    def start(self) -> GpuTelemetrySampler:
        if self._thread is not None and self._thread.is_alive():
            return self
        self._stop.clear()
        self._samples.clear()
        self._binary = self._resolve_binary()
        if self._binary is None:
            self.available = False
            self.error = "nvidia-smi not found"
            return self
        self._poll_once()
        if not self.available:
            return self
        self._thread = threading.Thread(target=self._loop, name="bench-exl3-gpu-telemetry", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> dict[str, object]:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=max(5.0, self.interval_s + 6.0))
        self._thread = None
        self.summary = self.snapshot()
        return self.summary

    def snapshot(self) -> dict[str, object]:
        if not self.available or not self._samples:
            metrics = empty_telemetry()
            available = False
        else:
            metrics = summarize_samples(self._samples)
            available = True
        return {"available": available, "error": self.error, **metrics}

    def __enter__(self) -> GpuTelemetrySampler:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.stop()
        return False
