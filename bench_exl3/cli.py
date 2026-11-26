"""Command line for the Dual RTX 3090 EXL3 benchmark."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bench_exl3.models import (
    DEFAULT_CONCURRENCIES,
    DEFAULT_OUTPUT_LENGTHS,
    DEFAULT_PROMPT_LENGTHS,
    describe_models,
)
from bench_exl3.report import ReportError, write_report
from bench_exl3.runner import run_benchmark


def parse_int_list(text: str) -> list[int]:
    parts = [part for part in text.replace(",", " ").split() if part]
    if not parts:
        raise ValueError("expected one or more positive integers")
    values: list[int] = []
    for part in parts:
        try:
            value = int(part)
        except ValueError as exc:
            raise ValueError(f"not an integer: {part}") from exc
        if value < 1:
            raise ValueError(f"must be >= 1: {part}")
        values.append(value)
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench_exl3", description="Dual RTX 3090 EXL3 local inference benchmark")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a live matrix against TabbyAPI")
    run.add_argument("--model", required=True, help="EXL3 preset name")
    run.add_argument("--endpoints", required=True, help="comma-separated OpenAI base URLs, including /v1")
    run.add_argument("--mode", required=True, choices=("single-gpu", "dual-gpu"))
    run.add_argument("--prompt-lengths", default=None, help="comma-separated prompt token targets")
    run.add_argument("--output-lengths", default=None, help="comma-separated max_tokens values")
    run.add_argument("--concurrencies", default=None, help="comma-separated concurrency levels")
    run.add_argument("--warmup", type=int, default=1, help="warmup requests per cell, discarded")
    run.add_argument(
        "--requests",
        type=int,
        default=None,
        help="measured requests per cell (default: concurrency * 2; if set, must be >= max concurrency)",
    )
    run.add_argument("--out-dir", required=True, help="directory for jsonl, csv, json, markdown, and svg")
    run.add_argument("--timeout", type=float, default=600.0, help="per-request socket timeout in seconds")

    report = sub.add_parser("report", help="regenerate summary.md and SVG charts from a measured matrix")
    report.add_argument("--input", required=True, dest="input_path", help="path to matrix.json or matrix.csv")
    report.add_argument("--out-dir", required=True, help="directory for summary.md and charts/")

    sub.add_parser("list-models", help="print configured EXL3 presets and default weight paths")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2

    if args.command == "list-models":
        print(describe_models())
        return 0

    if args.command == "report":
        try:
            write_report(args.out_dir, args.input_path)
        except (ReportError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {Path(args.out_dir) / 'summary.md'}")
        return 0

    try:
        prompt_lengths = parse_int_list(args.prompt_lengths) if args.prompt_lengths else list(DEFAULT_PROMPT_LENGTHS)
        output_lengths = parse_int_list(args.output_lengths) if args.output_lengths else list(DEFAULT_OUTPUT_LENGTHS)
        concurrencies = parse_int_list(args.concurrencies) if args.concurrencies else list(DEFAULT_CONCURRENCIES)
        endpoints = [part.strip() for part in str(args.endpoints).split(",") if part.strip()]
        if not endpoints:
            raise ValueError("at least one endpoint is required")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return run_benchmark(
        model=args.model,
        endpoints=endpoints,
        mode=args.mode,
        prompt_lengths=prompt_lengths,
        output_lengths=output_lengths,
        concurrencies=concurrencies,
        warmup=args.warmup,
        requests=args.requests,
        out_dir=args.out_dir,
        timeout=args.timeout,
    )
