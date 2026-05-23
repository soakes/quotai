#!/usr/bin/env python3
"""QuotAI - Z.ai quota monitor with human-friendly, JSON, and raw output formats.

Copyright (c) 2026 Simon Oakes
MIT License - see https://github.com/soakes/quotai/blob/main/LICENSE
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

API_URL = "https://api.z.ai/api/monitor/usage/quota/limit"
DEFAULT_TIMEZONE = "Europe/London"
REQUEST_TIMEOUT_SECONDS = 20
VERSION = "1.1.1"

JsonDict = dict[str, Any]

BAR_WIDTH = 24
BAR_FILLED = "\u2588"
BAR_EMPTY = "\u2591"

ACCENT = "\u2502"
SEPARATOR = "\u2500"

COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_DIM = "\033[2m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def is_number(value: Any) -> bool:
    """Return True when value is an int or float, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def color(text: str, code: str, enabled: bool = True) -> str:
    """Wrap text in ANSI escape codes when enabled."""
    if not enabled:
        return str(text)
    return f"{code}{text}{COLOR_RESET}"


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Constrain a number to a closed range."""
    return max(minimum, min(value, maximum))


def format_duration(seconds: int) -> str:
    """Return a compact duration string, such as '56m' or '6d 19h 3m'."""
    if seconds <= 0:
        return "now"

    units = ((86_400, "d"), (3_600, "h"), (60, "m"), (1, "s"))
    remainder = seconds
    parts: list[str] = []

    for unit_seconds, suffix in units:
        value, remainder = divmod(remainder, unit_seconds)
        if value > 0:
            parts.append(f"{value}{suffix}")

    return " ".join(parts[:3])


def progress_bar(percentage: float, width: int = BAR_WIDTH, use_color: bool = True) -> str:
    """Render a Unicode progress bar, optionally colour-coded by threshold."""
    clamped_percentage = clamp(percentage, 0, 100)
    filled = int(width * clamped_percentage / 100)
    empty = width - filled
    rendered = BAR_FILLED * filled + BAR_EMPTY * empty

    if not use_color:
        return rendered

    if clamped_percentage >= 90:
        bar_color = COLOR_RED
    elif clamped_percentage >= 70:
        bar_color = COLOR_YELLOW
    else:
        bar_color = COLOR_GREEN
    return color(rendered, bar_color)


def get_timezone(timezone_name: str) -> ZoneInfo:
    """Return a ZoneInfo object, falling back to default when invalid."""
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        print(
            f"WARNING: unknown timezone {timezone_name!r}; using {DEFAULT_TIMEZONE}",
            file=sys.stderr,
        )
        return ZoneInfo(DEFAULT_TIMEZONE)


def describe_window(item: JsonDict) -> str:
    """Return a human-readable name for a quota bucket."""
    limit_kind = item.get("type")
    unit = item.get("unit")
    number = item.get("number")

    if limit_kind == "TOKENS_LIMIT" and unit == 3 and number == 5:
        return "5-Hour Rolling Token Quota"
    if limit_kind == "TOKENS_LIMIT" and unit == 6 and number == 1:
        return "Weekly Token Quota"
    if limit_kind == "TIME_LIMIT":
        return "Tool/Search Time Quota"

    return f"Unknown Quota (type={limit_kind}, unit={unit}, n={number})"


def describe_window_compact(item: JsonDict) -> str:
    """Return a short machine-friendly name for a quota bucket."""
    limit_kind = item.get("type")
    unit = item.get("unit")
    number = item.get("number")

    if limit_kind == "TOKENS_LIMIT" and unit == 3 and number == 5:
        return "5h-rolling"
    if limit_kind == "TOKENS_LIMIT" and unit == 6 and number == 1:
        return "weekly"
    if limit_kind == "TIME_LIMIT":
        return "tool/search"
    return "unknown"


def fetch_json(api_key: str, api_url: str) -> JsonDict:
    """Fetch quota data from the Z.ai monitor endpoint."""
    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"quotai/{VERSION}",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        raw_body = response.read().decode("utf-8")

    payload = json.loads(raw_body)
    if not isinstance(payload, dict):
        raise ValueError("API response was JSON, but not a JSON object")

    return payload


def parse_payload(payload: JsonDict) -> tuple[str, list[JsonDict]]:
    """Validate the API payload and return the plan level and quota list."""
    if not payload.get("success"):
        message = payload.get("msg", "API returned success=false")
        raise ValueError(str(message))

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("API response does not contain a valid data object")

    limits = data.get("limits")
    if not isinstance(limits, list):
        raise ValueError("API response does not contain a valid limits list")

    quota_limits = [item for item in limits if isinstance(item, dict)]
    return str(data.get("level", "unknown")), quota_limits


def format_reset(
    item: JsonDict, local_timezone: ZoneInfo, now_utc: datetime
) -> tuple[str | None, str | None, str | None, int | None]:
    """Format reset time and remaining duration for a quota bucket."""
    reset_ms = item.get("nextResetTime")
    if not is_number(reset_ms):
        return None, None, None, None

    reset_utc = datetime.fromtimestamp(reset_ms / 1000, tz=timezone.utc)
    reset_local = reset_utc.astimezone(local_timezone)
    seconds_until_reset = int((reset_utc - now_utc).total_seconds())
    reset_when = reset_local.strftime("%Y-%m-%d %H:%M:%S %Z")
    reset_when_utc = reset_utc.isoformat().replace("+00:00", "Z")
    reset_in = format_duration(seconds_until_reset)

    return reset_in, reset_when, reset_when_utc, int(reset_ms)


def _extract_details(item: JsonDict) -> list[dict[str, Any]]:
    """Pull per-tool/per-model usage details from a quota bucket."""
    usage_details = item.get("usageDetails")
    details: list[dict[str, Any]] = []
    if isinstance(usage_details, list):
        for d in usage_details:
            if isinstance(d, dict):
                details.append(
                    {
                        "model": d.get("modelCode", "unknown"),
                        "usage": d.get("usage", "unknown"),
                    }
                )
    return details


def build_quota_item(item: JsonDict, local_timezone: ZoneInfo, now_utc: datetime) -> dict[str, Any]:
    """Normalise a single quota bucket from the API into a structured dict."""
    percentage = item.get("percentage")
    if is_number(percentage):
        pct = float(percentage)
    else:
        pct = None

    remaining_pct = clamp(100 - pct, 0, 100) if pct is not None else None

    usage = item.get("usage")
    current_value = item.get("currentValue")
    remaining = item.get("remaining")

    reset_in, reset_at, reset_at_utc, reset_epoch_ms = format_reset(item, local_timezone, now_utc)

    return {
        "name": describe_window(item),
        "name_compact": describe_window_compact(item),
        "type": item.get("type"),
        "percentage_used": pct,
        "percentage_remaining": remaining_pct,
        "usage_limit": float(usage) if is_number(usage) else None,
        "current_value": float(current_value) if is_number(current_value) else None,
        "remaining_units": float(remaining) if is_number(remaining) else None,
        "resets_in": reset_in,
        "resets_at": reset_at,
        "resets_at_utc": reset_at_utc,
        "reset_epoch_ms": reset_epoch_ms,
        "timezone": getattr(local_timezone, "key", str(local_timezone)),
        "details": _extract_details(item),
    }


def format_number(n: float | None) -> str:
    """Format a number with k/M suffixes for human readability."""
    if n is None:
        return "-"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return f"{n:g}"


def _pct_color(pct: float) -> str:
    """Return the ANSI color code for a usage percentage."""
    if pct >= 90:
        return COLOR_RED
    if pct >= 70:
        return COLOR_YELLOW
    return COLOR_GREEN


def _print_pretty_item(item: dict[str, Any], use_color: bool) -> None:
    """Print a single quota bucket with a left accent bar."""
    accent = color(ACCENT, COLOR_DIM, use_color)
    name = item["name"]
    title = color(name, COLOR_BOLD, use_color)

    print(f"  {accent}  {title}")
    print(f"  {accent}")

    pct = item["percentage_used"]
    if pct is not None:
        pbar = progress_bar(pct, use_color=use_color)
        pct_label = color(f"{pct:g}%", _pct_color(pct), use_color)
        print(f"  {accent}  [{pbar}] {pct_label} used")
        remaining_pct = item["percentage_remaining"]
        if remaining_pct is not None:
            print(f"  {accent}  Remaining: {remaining_pct:g}%")

    for key, label_text in [
        ("usage_limit", "Limit"),
        ("current_value", "Used"),
        ("remaining_units", "Remaining"),
    ]:
        val = item[key]
        if val is not None:
            print(f"  {accent}  {label_text + ':':<12}{format_number(val)}")

    if item["resets_in"] is not None:
        reset_colored = color(item["resets_in"], COLOR_YELLOW, use_color)
        print(f"  {accent}  Resets in:   {reset_colored}")
    if item["resets_at"] is not None:
        print(f"  {accent}  Resets at:   {color(item['resets_at'], COLOR_DIM, use_color)}")

    if item["details"]:
        print(f"  {accent}  {color('Details:', COLOR_DIM, use_color)}")
        for detail in item["details"]:
            print(f"  {accent}    \u2022 {detail['model']}: {detail['usage']}")

    print(f"  {color(SEPARATOR * 34, COLOR_DIM, use_color)}")


def print_pretty(level: str, items: list[dict[str, Any]], use_color: bool) -> None:
    """Print all quota buckets in a clean, left-accented layout."""
    plan_label = color("Z.ai", COLOR_BOLD, use_color)
    plan_value = color(level, COLOR_CYAN, use_color)
    print(f"\n  {plan_label} plan: {plan_value}\n")

    for item in items:
        _print_pretty_item(item, use_color)


def print_compact(level: str, items: list[dict[str, Any]], use_color: bool) -> None:
    """Print a compact one-line-per-quota summary."""
    print(f"Plan: {level}")
    for item in items:
        pct = item["percentage_used"]
        pct_str = f"{pct:g}%" if pct is not None else "-"
        remaining = item["remaining_units"]
        rem_str = format_number(remaining) if remaining is not None else "-"
        reset = item["resets_in"] or "-"

        pbar = (
            progress_bar(pct or 0, width=10, use_color=use_color) if pct is not None else "-" * 10
        )
        name = item["name_compact"]
        line = f"  {name:<14} [{pbar}] {pct_str:>6}" f"  left: {rem_str:>7}  reset: {reset}"
        print(line)


def output_json(level: str, items: list[dict[str, Any]]) -> str:
    """Return a pretty-printed JSON string of all quota data."""
    output = {
        "plan": level,
        "quotas": items,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(output, indent=2)


def output_json_lines(level: str, items: list[dict[str, Any]]) -> str:
    """Return JSON Lines (one object per quota) for log/jq consumption."""
    lines: list[str] = []
    for item in items:
        line = {
            "plan": level,
            "quota": item["name_compact"],
            "pct_used": item["percentage_used"],
            "pct_remaining": item["percentage_remaining"],
            "remaining": item["remaining_units"],
            "resets_in": item["resets_in"],
            "resets_at": item["resets_at"],
            "resets_at_utc": item["resets_at_utc"],
            "reset_epoch_ms": item["reset_epoch_ms"],
        }
        lines.append(json.dumps(line))
    return "\n".join(lines)


def check_threshold(items: list[dict[str, Any]], threshold: float) -> bool:
    """Return True if any quota's usage percentage meets or exceeds threshold."""
    for item in items:
        pct = item["percentage_used"]
        if pct is not None and pct >= threshold:
            return True
    return False


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"ERROR: {message}", file=sys.stderr)


def print_http_error(http_error: urllib.error.HTTPError) -> None:
    """Print an HTTP error with the response body when available."""
    body = http_error.read().decode("utf-8", errors="replace").strip()
    print_error(f"HTTP {http_error.code}: {http_error.reason}")
    if body:
        print(body, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="quotai",
        description="Z.ai quota monitor - check your usage and limits",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"quotai {VERSION}",
    )

    fmt = parser.add_mutually_exclusive_group()
    fmt.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="output as JSON (pretty-printed)",
    )
    fmt.add_argument(
        "--jsonl",
        action="store_true",
        help="output as JSON Lines (one JSON object per quota, good for jq/journal)",
    )
    fmt.add_argument(
        "--raw",
        action="store_true",
        help="dump the raw API response",
    )
    fmt.add_argument(
        "-c",
        "--compact",
        action="store_true",
        help="compact one-line-per-quota output",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable colored output",
    )
    parser.add_argument(
        "--timezone",
        "-z",
        default=None,
        help=f"display timezone (default: {DEFAULT_TIMEZONE} or ZAI_TIMEZONE env)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Z.ai API key (default: ZAI_API_KEY env var)",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help=f"API endpoint (default: {API_URL})",
    )
    parser.add_argument(
        "--watch",
        "-w",
        type=int,
        metavar="SECONDS",
        default=None,
        help="auto-refresh every N seconds (Ctrl-C to stop)",
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        metavar="PERCENT",
        default=None,
        help="exit with code 2 if any quota usage >= PERCENT, from 0 to 100",
    )

    return parser


def _handle_fetch_error(
    err: Exception,
) -> tuple[int, str | None, list[dict[str, Any]] | None, JsonDict | None]:
    """Print an appropriate error message and return a failure tuple."""
    if isinstance(err, urllib.error.HTTPError):
        print_http_error(err)
    elif isinstance(err, urllib.error.URLError):
        print_error(f"request failed: {err.reason}")
    elif isinstance(err, json.JSONDecodeError):
        print_error(f"response was not valid JSON: {err}")
    elif isinstance(err, ValueError):
        print_error(str(err))
    return 1, None, None, None


def run_once(
    args: argparse.Namespace,
) -> tuple[int, str | None, list[dict[str, Any]] | None, JsonDict | None]:
    """Fetch and parse quota data once; return (code, level, items, raw)."""
    api_key = args.api_key or os.getenv("ZAI_API_KEY")
    if not api_key:
        print_error("ZAI_API_KEY is not set")
        print("Set it with: export ZAI_API_KEY='your-api-key'", file=sys.stderr)
        return 1, None, None, None

    api_url = args.api_url or os.getenv("ZAI_API_URL", API_URL)
    tz_name = args.timezone or os.getenv("ZAI_TIMEZONE", DEFAULT_TIMEZONE)
    local_tz = get_timezone(tz_name)

    try:
        payload = fetch_json(api_key, api_url)
        if args.raw:
            return 0, None, None, payload
        level, limits = parse_payload(payload)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        json.JSONDecodeError,
        ValueError,
    ) as err:
        return _handle_fetch_error(err)

    now_utc = datetime.now(timezone.utc)
    items = [build_quota_item(item, local_tz, now_utc) for item in limits]
    return 0, level, items, None


def _render_output(
    args: argparse.Namespace,
    level: str | None,
    items: list[dict[str, Any]] | None,
    raw_payload: JsonDict | None,
    use_color: bool,
) -> None:
    """Dispatch to the correct output format based on CLI flags."""
    if raw_payload is not None:
        print(json.dumps(raw_payload, indent=2))
        return

    if level is None or items is None:
        raise ValueError("formatted output requires parsed quota data")

    if args.json:
        print(output_json(level, items))
    elif args.jsonl:
        print(output_json_lines(level, items))
    elif args.compact:
        print_compact(level, items, use_color)
    else:
        print_pretty(level, items, use_color)


def _validate_args(args: argparse.Namespace) -> int | None:
    """Validate parsed CLI arguments and return an exit code on failure."""
    if args.watch is not None and args.watch < 1:
        print_error("--watch interval must be >= 1 second")
        return 1
    if args.threshold is not None and not 0 <= args.threshold <= 100:
        print_error("--threshold must be between 0 and 100")
        return 1
    if args.raw and args.threshold is not None:
        print_error("--threshold cannot be used with --raw")
        return 1
    return None


def _run_loop(args: argparse.Namespace, use_color: bool) -> int:
    """Fetch and render quota data once or repeatedly in watch mode."""
    watch_mode = args.watch is not None

    while True:
        if watch_mode:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.write(
                color(
                    f"  quotai - refreshing every {args.watch}s  (Ctrl-C to stop)\n\n",
                    COLOR_DIM,
                    use_color,
                )
            )
            sys.stdout.flush()

        code, level, items, raw_payload = run_once(args)

        if code != 0:
            return code

        _render_output(args, level, items, raw_payload, use_color)

        if args.threshold is not None and items is not None:
            if check_threshold(items, args.threshold):
                return 2

        if not watch_mode:
            return 0

        try:
            time.sleep(args.watch)
        except KeyboardInterrupt:
            print()
            return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse args, fetch, render, optionally loop."""
    parser = build_parser()
    args = parser.parse_args(argv)
    use_color = not args.no_color and sys.stdout.isatty()

    validation_code = _validate_args(args)
    if validation_code is not None:
        return validation_code

    return _run_loop(args, use_color)


if __name__ == "__main__":
    raise SystemExit(main())
