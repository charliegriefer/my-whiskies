import re
import time

import requests

_cache: dict = {"data": None, "fetched_at": 0.0}
_CACHE_TTL = 86400  # 24 hours — resets on server restart (i.e. every deploy)
_GITHUB_RELEASES_URL = "https://api.github.com/repos/charliegriefer/my-whiskies/releases"
_GITHUB_PR_URL = "https://github.com/charliegriefer/my-whiskies/pull/{pr}"

_PR_PARENS = re.compile(r"\s*\(#(\d+)\)\s*$")
_PR_LINK = re.compile(r"\s*\[#(\d+)\]\([^)]+\)\s*$")


def _parse_body(body: str) -> list[dict]:
    sections: list[dict] = []
    current: dict | None = None

    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("## ") or line.startswith("### "):
            current = {"label": line.lstrip("#").strip(), "items": []}
            sections.append(current)
        elif line.startswith("- ") or line.startswith("* "):
            if current is None:
                current = {"label": "", "items": []}
                sections.append(current)
            text = line[2:].strip()
            pr = None
            for pattern in (_PR_PARENS, _PR_LINK):
                m = pattern.search(text)
                if m:
                    pr = m.group(1)
                    text = text[: m.start()].strip()
                    break
            current["items"].append(
                {
                    "text": text,
                    "pr": pr,
                    "pr_url": _GITHUB_PR_URL.format(pr=pr) if pr else None,
                }
            )

    return [s for s in sections if s["items"]]


def get_releases() -> list[dict]:
    if _cache["data"] is not None and time.time() - _cache["fetched_at"] < _CACHE_TTL:
        return _cache["data"]

    try:
        resp = requests.get(
            _GITHUB_RELEASES_URL,
            timeout=5,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        releases = [
            {
                "version": r["tag_name"],
                "sections": _parse_body(r["body"] or ""),
                "published_at": r["published_at"][:10],
                "url": r["html_url"],
            }
            for r in resp.json()
            if not r.get("draft")
        ]
    except Exception:
        return _cache["data"] or []

    _cache["data"] = releases
    _cache["fetched_at"] = time.time()
    return releases
