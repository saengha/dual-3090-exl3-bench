"""EXL3 model presets and the deterministic synthetic prompt builder.

Prompt text is sized with a reproducible character estimator so a requested
length always yields the same string. Recorded prompt and completion tokens
always come from the endpoint `usage` payload when the server sends one.
The estimator is not a measured token count.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Exl3Model:
    name: str
    weight_dir: str
    quant_bpw: float
    format: str = "EXL3"

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "weight_dir": self.weight_dir,
            "quant_bpw": self.quant_bpw,
            "format": self.format,
        }


EXL3_ROOT = r"D:\models\exl3"

QWEN_27B = Exl3Model(
    name="Qwen3.8-27B-Abliterated-EXL3-4.5bpw",
    weight_dir=EXL3_ROOT + r"\Qwen3.8-27B-Abliterated-EXL3-4.5bpw",
    quant_bpw=4.5,
)
GEMMA_31B = Exl3Model(
    name="gemma-4-31B-it-uncensored-EXL3-4.0bpw",
    weight_dir=EXL3_ROOT + r"\gemma-4-31B-it-uncensored-EXL3-4.0bpw",
    quant_bpw=4.0,
)

MODEL_PRESETS: dict[str, Exl3Model] = {
    QWEN_27B.name: QWEN_27B,
    GEMMA_31B.name: GEMMA_31B,
}
MODEL_ORDER: tuple[str, ...] = (QWEN_27B.name, GEMMA_31B.name)

DEFAULT_PROMPT_LENGTHS: tuple[int, ...] = (512, 2048, 8192)
DEFAULT_OUTPUT_LENGTHS: tuple[int, ...] = (128, 512)
DEFAULT_CONCURRENCIES: tuple[int, ...] = (1, 2, 4, 8)
DEFAULT_MODES: tuple[str, ...] = ("single-gpu", "dual-gpu")
DEFAULT_ENDPOINTS: tuple[str, ...] = (
    "http://127.0.0.1:5000/v1",
    "http://127.0.0.1:5001/v1",
)

# One structured technical paragraph. Repeated, then cut to the exact
# character length whose char/4 estimate equals the requested token target.
_PARAGRAPH = (
    "Paragraph. Dual RTX 3090 water-cooled EXL3 inference on TabbyAPI ExLlamaV3. "
    "This cell records time to first token, decode throughput, peak VRAM, board power, and GPU temperature. "
    "Requests are scheduled across GPU 0 at port 5000 and GPU 1 at port 5001. "
    "The quantised weights stay resident so prefill and decode are measured without reload.\n\n"
)


def estimate_prompt_tokens(text: str) -> int:
    """Return the deterministic char/4 size of `text`.

    This is only the sizing function used by `build_synthetic_prompt`.
    It is not a tokenizer and must not be stored as a measured prompt-token count.
    """

    if not text:
        return 0
    return (len(text) + 3) // 4


def build_synthetic_prompt(target_tokens: int) -> str:
    """Build a reproducible prompt whose char/4 estimate equals `target_tokens`."""

    if isinstance(target_tokens, bool) or not isinstance(target_tokens, int) or target_tokens < 1:
        raise ValueError("target_tokens must be a positive integer")
    desired_len = 4 * target_tokens - 3
    header = f"TARGET {target_tokens:08d}.\n\n"
    chunks = [header]
    while sum(len(chunk) for chunk in chunks) < desired_len:
        chunks.append(_PARAGRAPH)
    text = "".join(chunks)[:desired_len]
    sized = estimate_prompt_tokens(text)
    if sized != target_tokens:
        raise RuntimeError(f"synthetic prompt estimator produced {sized} tokens for target {target_tokens}")
    return text


def get_model(name: str) -> Exl3Model:
    try:
        return MODEL_PRESETS[name]
    except KeyError as exc:
        known = ", ".join(MODEL_ORDER)
        raise ValueError(f"unknown EXL3 model {name!r}. Configured presets: {known}") from exc


def describe_models() -> str:
    lines = ["EXL3 model presets", f"Default weight root: {EXL3_ROOT}", ""]
    for name in MODEL_ORDER:
        model = MODEL_PRESETS[name]
        lines.append(model.name)
        lines.append(f"  format: {model.format}")
        lines.append(f"  quant_bpw: {model.quant_bpw:.1f}")
        lines.append(f"  weight_dir: {model.weight_dir}")
        lines.append("")
    lines.append("Default endpoints")
    lines.append(f"  GPU 0: {DEFAULT_ENDPOINTS[0]}")
    lines.append(f"  GPU 1: {DEFAULT_ENDPOINTS[1]}")
    lines.append("")
    lines.append("Default matrix")
    lines.append("  prompt_lengths: " + ", ".join(str(n) for n in DEFAULT_PROMPT_LENGTHS))
    lines.append("  output_lengths: " + ", ".join(str(n) for n in DEFAULT_OUTPUT_LENGTHS))
    lines.append("  concurrencies: " + ", ".join(str(n) for n in DEFAULT_CONCURRENCIES))
    lines.append("  modes: " + ", ".join(DEFAULT_MODES))
    return "\n".join(lines)
