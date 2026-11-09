"""Per-row verification: 4 live signals -> one verdict + evidence links."""

from __future__ import annotations

import re
import urllib.request
from datetime import datetime, timezone

from .client import TinyFishClient
from .states import Signals, decide_verdict

PARKED_MARKERS = (
    "domain is for sale",
    "parked domain",
    "buy this domain",
    "this domain is parked",
)
ARCHIVE_MARKERS = ("this repository was archived", "read-only", "archived by the owner")


def github_api_url(page_url: str) -> str | None:
    m = re.match(r"https://github\.com/([^/]+)/([^/#]+)", page_url.rstrip("/"))
    if not m:
        return None
    return f"https://api.github.com/repos/{m.group(1)}/{m.group(2)}"


def github_search_url(full_name: str) -> str:
    return f"https://github.com/search?q={urllib_name(full_name)}"


def urllib_name(full_name: str) -> str:
    import urllib.parse

    return urllib.parse.quote_plus(full_name)


def parse_github_api(payload: dict) -> tuple[bool, int | None]:
    """(archived, pushed_days_ago) from api.github.com repo JSON."""
    archived = bool(payload.get("archived"))
    pushed = payload.get("pushed_at") or payload.get("updated_at")
    days = None
    if pushed:
        dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - dt).days
    return archived, days


def check_row(client: TinyFishClient, name: str, url: str) -> dict:
    """Check one row. Never raises for dead pages - absence IS the signal."""
    evidence: list[str] = [url]
    api_url = github_api_url(url)
    text, final_url = "", url
    reachable = False
    try:
        text, final_url = client.fetch(url, f"Liveness check for {name}")
        reachable = bool(text) and len(text) > 100
    except Exception:
        reachable = False
    redirected = bool(final_url and final_url.rstrip("/") != url.rstrip("/"))
    if redirected:
        evidence.append(final_url)

    parked = any(m in text.lower() for m in PARKED_MARKERS) if reachable else False
    archived, pushed_days = False, None
    if api_url:
        evidence.append(api_url)
        try:
            payload = client.fetch_json(api_url)
            archived, pushed_days = parse_github_api(payload)
        except Exception:
            archived, pushed_days = False, None
    elif reachable:
        archived = any(m in text.lower() for m in ARCHIVE_MARKERS)

    try:
        search_hits = (
            client.search(f"{name} github")
            if (reachable and pushed_days is None)
            else None
        )
    except Exception:
        search_hits = None

    signals = Signals(
        reachable=reachable,
        redirected=redirected,
        parked=parked,
        archived=archived,
        pushed_days_ago=pushed_days,
        search_hits=search_hits or 0,
    )
    verdict = decide_verdict(
        reachable=reachable,
        parked=parked,
        archived=archived,
        pushed_days_ago=pushed_days,
        redirected=redirected,
    )
    return {
        "verdict": verdict,
        "latest_activity_date": _activity_date(pushed_days),
        "evidence_links": " | ".join(evidence),
        "signals": {
            "reachable": reachable,
            "redirected": redirected,
            "parked": parked,
            "archived": archived,
            "pushed_days_ago": pushed_days,
            "search_hits": search_hits,
        },
    }


def _activity_date(pushed_days: int | None) -> str:
    if pushed_days is None:
        return ""
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) - timedelta(days=pushed_days)).date().isoformat()
