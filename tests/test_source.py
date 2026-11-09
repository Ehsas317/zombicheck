"""Source parsing - no network."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zombicheck.source import parse_awesome_go  # noqa: E402

MD = """# List

- [gin](https://github.com/gin-gonic/gin) - Gin is a web framework.
- [cobra](https://github.com/spf13/cobra) - Commander for CLIs.
- [bad](https://github.com/x/y/badge.svg) - badge link
- [dupe](https://github.com/gin-gonic/gin) - dup, dropped
- [tree](https://github.com/a/b/tree/main/pkg) - subpath normalized
"""


def test_parse_awesome_go():
    rows = parse_awesome_go(MD)
    assert rows == [
        {"name": "gin", "url": "https://github.com/gin-gonic/gin"},
        {"name": "cobra", "url": "https://github.com/spf13/cobra"},
        {"name": "tree", "url": "https://github.com/a/b"},
    ]


def test_parse_awesome_go_empty():
    assert parse_awesome_go("no links here") == []
