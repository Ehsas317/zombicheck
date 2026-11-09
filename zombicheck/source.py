"""Input sources: build the 500+ row list from the real GitHub awesome-list.

Two real sources (either feeds the same verifier):
  - awesome-go README (2,902 parseable link rows) -> CSV with name,url
  - TinySet dataset rows (dataset rows export)     -> CSV with name,url
"""

from __future__ import annotations

import csv
import io
import re
import urllib.request

AWESOME_GO_README = (
    "https://raw.githubusercontent.com/avelino/awesome-go/main/README.md"
)
_LINK = re.compile(r"^- \[([^\]]+)\]\((https://github\.com/[^)]+)\)", re.M)


def parse_awesome_go(markdown: str) -> list[dict]:
    """Parse README lines: '- [name](url) - desc' -> [{name, url}] (badge links skipped)."""
    rows = []
    for name, url in _LINK.findall(markdown):
        name, url = name.strip(), url.strip().rstrip("/")
        if name.startswith("!") or "badge" in url.lower():
            continue
        m = re.match(r"https://github\.com/([^/]+)/([^/#]+)", url)
        if m:
            rows.append(
                {"name": name, "url": f"https://github.com/{m.group(1)}/{m.group(2)}"}
            )
    # dedupe, keep order
    seen, out = set(), []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append(r)
    return out


def fetch_awesome_go() -> list[dict]:
    text = (
        urllib.request.urlopen(AWESOME_GO_README, timeout=60)
        .read()
        .decode("utf-8", "ignore")
    )
    return parse_awesome_go(text)


def rows_to_csv(rows: list[dict]) -> str:
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=["name", "url"])
    w.writeheader()
    for r in rows:
        w.writerow({"name": r["name"], "url": r["url"]})
    return out.getvalue()
