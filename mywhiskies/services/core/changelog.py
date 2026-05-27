import time

import markdown
import requests

_cache: dict = {"data": None, "fetched_at": 0.0}
_CACHE_TTL = 86400  # 24 hours — resets on server restart (i.e. every deploy)
_GITHUB_RELEASES_URL = "https://api.github.com/repos/charliegriefer/my-whiskies/releases"


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
                "name": r["name"] or r["tag_name"],
                "body_html": markdown.markdown(r["body"] or "_No release notes._"),
                "published_at": r["published_at"][:10],  # YYYY-MM-DD
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
