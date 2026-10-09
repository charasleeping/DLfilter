"""Salvage complete top-level records from a truncated DLfilter works_table.json.

Run from the DLfilter repository root:
    python recover_works_table.py

The source file is never modified. Output is written to
    database/works_table.recovered.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path("database/works_table.json")
DEST = Path("database/works_table.recovered.json")


def skip_ws(text: str, pos: int) -> int:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def main() -> int:
    if not SOURCE.is_file():
        print(f"ERROR: source file not found: {SOURCE}")
        print("Run this script from the DLfilter repository root.")
        return 2
    if DEST.exists():
        print(f"ERROR: destination already exists: {DEST}")
        print("Rename or remove that recovery output before trying again.")
        return 2

    print(f"Reading {SOURCE} ({SOURCE.stat().st_size:,} bytes)...")
    try:
        text = SOURCE.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: could not read source: {exc}")
        return 2

    decoder = json.JSONDecoder()
    pos = skip_ws(text, 0)
    if pos >= len(text) or text[pos] != "{":
        print("ERROR: source does not begin with a JSON object; nothing recovered.")
        return 2
    pos += 1
    count = 0
    last_key = None
    last_regist_date = None
    stopped_reason = "input ended before the outer object closed"

    try:
        with DEST.open("x", encoding="utf-8", newline="") as out:
            out.write("{")
            while True:
                pos = skip_ws(text, pos)
                if pos < len(text) and text[pos] == "}":
                    stopped_reason = "input JSON appears complete"
                    break
                if pos >= len(text):
                    break

                try:
                    key, end_key = decoder.raw_decode(text, pos)
                    if not isinstance(key, str):
                        stopped_reason = f"top-level key at character {pos} is not a string"
                        break
                    value_pos = skip_ws(text, end_key)
                    if value_pos >= len(text) or text[value_pos] != ":":
                        stopped_reason = f"missing colon after key near character {value_pos}"
                        break
                    value_pos = skip_ws(text, value_pos + 1)
                    value, end_value = decoder.raw_decode(text, value_pos)
                except json.JSONDecodeError as exc:
                    stopped_reason = (
                        f"stopped at malformed/incomplete record near character {exc.pos}: "
                        f"{exc.msg}"
                    )
                    break

                # Only write an entry once its entire value has parsed successfully.
                if count:
                    out.write(",")
                out.write(json.dumps(key, ensure_ascii=True, separators=(",", ":")))
                out.write(":")
                out.write(json.dumps(value, ensure_ascii=True, separators=(",", ":")))
                count += 1
                last_key = key
                if isinstance(value, dict):
                    last_regist_date = value.get("registDate")
                pos = skip_ws(text, end_value)

                if pos < len(text) and text[pos] == ",":
                    pos += 1
                    continue
                if pos < len(text) and text[pos] == "}":
                    stopped_reason = "input JSON appears complete"
                    break
                if pos >= len(text):
                    stopped_reason = "input ended immediately after a complete record"
                    break
                stopped_reason = f"unexpected character after record near character {pos}"
                break
            out.write("}")
    except OSError as exc:
        print(f"ERROR: could not write recovery file: {exc}")
        return 2

    print(f"Recovered complete records: {count:,}")
    print(f"Last complete work ID: {last_key!r}")
    if isinstance(last_regist_date, (int, float)):
        try:
            dt = datetime.fromtimestamp(last_regist_date, tz=timezone.utc)
            print(f"Last complete work registDate (UTC): {dt.isoformat()}")
        except (OverflowError, OSError, ValueError):
            print(f"Last complete work registDate value: {last_regist_date!r}")
    elif last_regist_date is not None:
        print(f"Last complete work registDate value: {last_regist_date!r}")
    print(f"Recovery output: {DEST}")
    print(f"Result: {stopped_reason}")
    print("The original works_table.json has NOT been changed.")
    print("Do not replace the original file until the recovered output has been reviewed.")
    if count == 0:
        print("WARNING: no complete entries were recovered; do not use this output as a catalogue.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
