"""check_row with a fake client - no network."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zombicheck.check import check_row, github_api_url, parse_github_api  # noqa: E402


class FakeClient:
    def __init__(self, page="", final=None, api=None, hits=0, fail=False):
        self.page, self.final, self.api, self.hits, self.fail = (
            page,
            final,
            api,
            hits,
            fail,
        )

    def fetch(self, url, purpose):
        if self.fail:
            raise RuntimeError("target_unreachable")
        if url.startswith("https://api.github.com"):
            return self.api, url
        return self.page, self.final or url

    def fetch_json(self, url):
        if self.api is None:
            raise RuntimeError("404")
        return self.api

    def search(self, query):
        return self.hits


def test_github_api_url():
    assert (
        github_api_url("https://github.com/gin-gonic/gin")
        == "https://api.github.com/repos/gin-gonic/gin"
    )
    assert github_api_url("https://example.com/page") is None


def test_parse_github_api_archived_and_days():
    archived, days = parse_github_api(
        {"archived": False, "pushed_at": "2026-11-01T00:00:00Z"}
    )
    assert archived is False and days == 8
    archived, days = parse_github_api(
        {"archived": True, "pushed_at": "2020-01-01T00:00:00Z"}
    )
    assert archived is True and days > 2000


def test_alive_row():
    cli = FakeClient(
        page="# Repo\nGin is a framework " * 10,
        api={"archived": False, "pushed_at": "2026-11-01T00:00:00Z"},
    )
    out = check_row(cli, "gin-gonic/gin", "https://github.com/gin-gonic/gin")
    assert out["verdict"] == "alive"
    assert out["latest_activity_date"] == "2026-11-01"
    assert "api.github.com/repos/gin-gonic/gin" in out["evidence_links"]


def test_unreachable_row_is_zombie():
    out = check_row(FakeClient(fail=True), "dead/repo", "https://github.com/dead/repo")
    assert out["verdict"] == "zombie" and out["signals"]["reachable"] is False


def test_parked_row_is_zombie():
    cli = FakeClient(
        page="# For sale\nThis domain is for sale. Buy this domain now. " * 5, api=None
    )
    out = check_row(cli, "parked/proj", "https://parked.example.com/proj")
    assert out["verdict"] == "zombie" and out["signals"]["parked"] is True


def test_stale_row_is_zombie():
    cli = FakeClient(
        page="# Old\n" * 200,
        api={"archived": False, "pushed_at": "2020-01-01T00:00:00Z"},
    )
    out = check_row(cli, "old/lib", "https://github.com/old/lib")
    assert out["verdict"] == "zombie"
