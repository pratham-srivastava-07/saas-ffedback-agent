"""Pulling reviews from Apple's public customer-review RSS feed.

``https://itunes.apple.com/<country>/rss/customerreviews/id=<app_id>/
sortby=mostrecent/page=<page>/json`` is public JSON, needs no API key, and is
the only source-specific ingestion path beyond CSV this project has (see the
design spec's "Out of scope" note on Zendesk/Intercom/App Store connectors).

Network access is isolated in :func:`_fetch_json` — the only function that
touches ``urllib`` — precisely so tests can monkeypatch it and the suite makes
no real network call. Nothing here uses a new dependency; the stdlib is
enough for one GET per page.
"""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

_FEED_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/"
    "sortby=mostrecent/page={page}/json"
)


class AppStoreIngestError(ValueError):
    """Raised for input or transport failure the caller can react to."""


def _fetch_json(url: str, *, timeout: float = 10.0) -> dict:
    """The sole network call. Tests monkeypatch this, never the network."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise AppStoreIngestError(
            f"Could not reach the App Store feed: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise AppStoreIngestError("The App Store feed timed out.") from exc
    except json.JSONDecodeError as exc:
        raise AppStoreIngestError("The App Store feed returned invalid JSON.") from exc


def _review_text(entry: dict) -> str:
    title = ((entry.get("title") or {}).get("label") or "").strip()
    content = ((entry.get("content") or {}).get("label") or "").strip()
    if title and content:
        return f"{title} — {content}"
    return title or content


def fetch_app_store_reviews(
    app_id: str,
    *,
    country: str = "us",
    pages: int = 1,
    max_items: int = 200,
    max_chars: int = 5000,
) -> list[dict]:
    """Pull recent reviews for an app id into feedback items.

    One review = one feedback item, ``source="app_store"``. The feed's first
    entry is the app's own metadata, not a review — it has no ``im:rating``,
    which is what distinguishes it, so it is skipped rather than assumed to
    be entry zero (a single-review page omits it entirely).
    """
    app_id = (app_id or "").strip()
    if not app_id:
        raise AppStoreIngestError("An app id is required.")
    if pages < 1:
        raise AppStoreIngestError("pages must be at least 1.")

    items: list[dict] = []
    for page in range(1, pages + 1):
        url = _FEED_URL.format(country=country, app_id=app_id, page=page)
        payload = _fetch_json(url)
        entries = ((payload.get("feed") or {}).get("entry")) or []
        # A feed with exactly one review collapses "entry" to a dict instead
        # of a one-item list — the same shape Apple uses elsewhere in this API.
        if isinstance(entries, dict):
            entries = [entries]

        for entry in entries:
            if "im:rating" not in entry:
                continue  # the app metadata entry, not a review

            review_id = ((entry.get("id") or {}).get("label")) or (
                f"appstore-{app_id}-{page}-{len(items)}"
            )
            text = _review_text(entry)[:max_chars]
            if not text:
                continue

            items.append(
                {
                    "id": str(review_id),
                    "text": text,
                    "user_type": "free",
                    "source": "app_store",
                }
            )

            if len(items) >= max_items:
                return items

    if not items:
        raise AppStoreIngestError(
            f"No reviews found for app id {app_id!r} in {country!r}."
        )

    return items
