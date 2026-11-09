"""Batch runner: CSV in -> CSV out with verdict columns. Crash-safe, resumable.

Output adds: verdict, latest_activity_date, evidence_links (the bounty asks for
verdict + date + evidence links). Rows done are appended as they finish, so a
kill mid-run keeps every finished row - rerun skips them via the checkpoint.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from .check import check_row
from .client import TinyFishClient

OUT_FIELDS = [
    "name",
    "url",
    "verdict",
    "latest_activity_date",
    "evidence_links",
    "signals_json",
]


def run_rows(
    client: TinyFishClient,
    rows: list[dict],
    out_path: Path,
    checkpoint: Path,
    limit: int | None = None,
    verbose: bool = False,
) -> list[dict]:
    """Verify rows; returns all results (resuming past checkpoint)."""
    done: dict[int, dict] = {}
    if checkpoint.exists():
        done = json.loads(checkpoint.read_text())
    out = Path(out_path)
    results: list[dict] = []
    with out.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        if out.stat().st_size == 0:
            w.writeheader()
            f.flush()
        for i, row in enumerate(rows):
            if limit is not None and len(results) >= limit:
                break
            if str(i) in done:
                continue  # resume: already verified this row
            try:
                r = check_row(client, row["name"], row["url"])
            except Exception as e:  # noqa: BLE001 - row failure is data, not crash
                r = {
                    "verdict": "zombie",
                    "latest_activity_date": "",
                    "evidence_links": row["url"],
                    "signals": {"error": str(e)[:200]},
                }
            done[str(i)] = r
            checkpoint.write_text(json.dumps(done))
            rec = {
                **row,
                **{k: v for k, v in r.items() if k != "signals"},
                "signals_json": json.dumps(r["signals"], ensure_ascii=False),
            }
            results.append(rec)
            w.writerow(rec)
            f.flush()
            if verbose or (len(results) % 10 == 0):
                print(
                    f"[{i + 1}/{len(rows)}] {row['name']}: {r['verdict']}",
                    file=sys.stderr,
                )
    return results


def read_input(path: str) -> list[dict]:
    rows = list(csv.DictReader(Path(path).read_text().splitlines()))
    for r in rows:
        r["name"] = (r.get("name") or r.get("repository_name") or "").strip()
        r["url"] = (r.get("url") or r.get("github_url") or "").strip()
    return [r for r in rows if r["url"]]
