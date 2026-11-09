"""TinyFish wrapper built for batch verification (Fetch up to 10 URLs per call).

Search/Fetch are free within the daily allowance - we batch to stay well inside it.
"""

from __future__ import annotations

import json
import sys
import time

FETCH_URL = "https://api.fetch.tinyfish.ai"


def _log(msg: str, verbose: bool) -> None:
    if verbose:
        print(f"[zombicheck] {msg}", file=sys.stderr)


class TinyFishClient:
    def __init__(self, sdk=None, retries: int = 3, verbose: bool = False):
        if sdk is None:
            from tinyfish import TinyFish

            sdk = TinyFish()
        self._sdk: TinyFish = sdk
        self.retries = max(1, retries)
        self.verbose = verbose
        self._cache: dict = {}

    def _retry(self, label, fn):
        delay = 1.0
        for attempt in range(1, self.retries + 1):
            try:
                return fn()
            except Exception as e:  # noqa: BLE001 - re-raised after retries
                if attempt == self.retries:
                    raise
                _log(
                    f"{label} attempt {attempt} failed ({e}); retry in {delay:g}s",
                    self.verbose,
                )
                time.sleep(delay)
                delay *= 2

    def fetch(self, url: str, purpose: str) -> str:
        """Single URL -> markdown (cached per process). Raises on error."""
        if url in self._cache:
            return self._cache[url]

        def _call():
            r = self._sdk.fetch.get_contents(
                urls=[url], format="markdown", ttl=0, purpose=purpose
            )
            if r.errors:
                raise RuntimeError(f"{url}: {r.errors[0].error}")
            return r.results[0].text, r.results[0].final_url

        text, final = self._retry("fetch", _call)
        self._cache[url] = (text, final)
        return text, final

    def fetch_json(self, url: str) -> dict:
        text, _ = self.fetch(url, "Structured GitHub API facts for liveness")
        text = text.strip().removeprefix("```json").removeprefix("```").strip().removesuffix("```").strip()
        return json.loads(text)

    def search(self, query: str) -> int:
        def _call():
            r = self._sdk.search.query(query, language="en")
            return len(r.results or [])

        try:
            return self._retry("search", _call)
        except Exception:
            return 0
