"""Dual RTX 3090 EXL3 local inference benchmark harness.

Runtime code in this package uses the Python 3.10+ standard library only.
Measurements come from live TabbyAPI streams and, when present, nvidia-smi.
Missing telemetry is reported as None. This package never invents benchmark numbers.
"""

from __future__ import annotations

__version__ = "1.0.0"
