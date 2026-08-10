"""App Store ingestion.

Every test monkeypatches ``_fetch_json``, so the suite still makes no network
call. The fixtures below reproduce the shapes Apple's feed actually returns,
including the two that break naive parsers.
"""

from __future__ import annotations

import pytest

from app import appstore
from app.appstore import AppStoreIngestError, fetch_app_store_reviews


def _review(review_id: str, title: str, content: str) -> dict:
    return {
        "id": {"label": review_id},
        "title": {"label": title},
        "content": {"label": content},
        "im:rating": {"label": "2"},
    }


# The feed's first entry describes the app itself and carries no rating.
_APP_METADATA = {
    "id": {"label": "https://itunes.apple.com/us/app/id123"},
    "title": {"label": "Some App"},
}


def _feed(entries) -> dict:
    return {"feed": {"entry": entries}}


@pytest.fixture
def fake_feed(monkeypatch):
    """Serve canned pages; returns the list of URLs that were requested."""
    requested: list[str] = []

    def install(pages: dict[int, dict]):
        def fake_fetch(url: str, **_kwargs) -> dict:
            requested.append(url)
            page = int(url.split("page=")[1].split("/")[0])
            return pages[page]

        monkeypatch.setattr(appstore, "_fetch_json", fake_fetch)
        return requested

    return install


def test_reviews_become_feedback_items(fake_feed):
    fake_feed(
        {
            1: _feed(
                [
                    _APP_METADATA,
                    _review("r1", "Crashes on launch", "Every single time."),
                    _review("r2", "Cannot sign in", "Stuck on the loading screen."),
                ]
            )
        }
    )

    items = fetch_app_store_reviews("123456")

    assert len(items) == 2
    assert items[0]["id"] == "r1"
    assert items[0]["source"] == "app_store"
    assert items[0]["user_type"] == "free"
    # Title and body are joined so the analyser sees the whole complaint.
    assert items[0]["text"] == "Crashes on launch — Every single time."


def test_app_metadata_entry_is_not_treated_as_a_review(fake_feed):
    """It is skipped by the absence of a rating, not by being first — a page
    with a single review omits it entirely."""
    fake_feed({1: _feed([_APP_METADATA, _review("r1", "Fine", "Works well.")])})

    items = fetch_app_store_reviews("123456")

    assert [item["id"] for item in items] == ["r1"]


def test_single_review_page_collapses_entry_to_an_object(fake_feed):
    """Apple returns `entry` as a dict, not a one-item list, in this case."""
    fake_feed({1: _feed(_review("solo", "Only review", "It is alright."))})

    items = fetch_app_store_reviews("123456")

    assert len(items) == 1
    assert items[0]["id"] == "solo"


def test_pages_are_fetched_in_order_and_accumulate(fake_feed):
    requested = fake_feed(
        {
            1: _feed([_review("a", "One", "First.")]),
            2: _feed([_review("b", "Two", "Second.")]),
        }
    )

    items = fetch_app_store_reviews("123456", pages=2)

    assert [item["id"] for item in items] == ["a", "b"]
    assert "page=1" in requested[0]
    assert "page=2" in requested[1]


def test_max_items_stops_early(fake_feed):
    fake_feed(
        {1: _feed([_review(f"r{n}", f"Title {n}", f"Body {n}") for n in range(10)])}
    )

    items = fetch_app_store_reviews("123456", max_items=3)

    assert len(items) == 3


def test_long_reviews_are_truncated_to_the_request_bound(fake_feed):
    fake_feed({1: _feed([_review("r1", "T", "x" * 9000)])})

    items = fetch_app_store_reviews("123456", max_chars=500)

    assert len(items[0]["text"]) == 500


def test_empty_reviews_are_dropped(fake_feed):
    fake_feed(
        {
            1: _feed(
                [
                    {"id": {"label": "blank"}, "im:rating": {"label": "5"}},
                    _review("r1", "Real", "Actual content."),
                ]
            )
        }
    )

    items = fetch_app_store_reviews("123456")

    assert [item["id"] for item in items] == ["r1"]


def test_missing_app_id_is_rejected():
    with pytest.raises(AppStoreIngestError):
        fetch_app_store_reviews("   ")


def test_a_feed_with_no_reviews_raises(fake_feed):
    fake_feed({1: _feed([_APP_METADATA])})

    with pytest.raises(AppStoreIngestError, match="No reviews"):
        fetch_app_store_reviews("123456")


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------


async def test_endpoint_analyses_fetched_reviews(client, monkeypatch):
    monkeypatch.setattr(
        appstore,
        "_fetch_json",
        lambda url, **_: _feed(
            [
                _APP_METADATA,
                _review("r1", "Signup is broken", "Cannot create an account."),
                _review("r2", "Signup fails", "It errors out every time."),
            ]
        ),
    )

    response = await client.post("/analyze/app-store", json={"app_id": "123456"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["analyzed"]) == 2
    assert all(item["source"] == "app_store" for item in body["analyzed"])


async def test_endpoint_surfaces_ingest_failure_as_422(client, monkeypatch):
    monkeypatch.setattr(appstore, "_fetch_json", lambda url, **_: _feed([]))

    response = await client.post("/analyze/app-store", json={"app_id": "123456"})

    assert response.status_code == 422


async def test_endpoint_rejects_an_out_of_range_page_count(client):
    response = await client.post(
        "/analyze/app-store", json={"app_id": "123456", "pages": 99}
    )

    assert response.status_code == 422
