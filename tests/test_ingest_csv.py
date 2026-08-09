"""CSV ingestion — the path a real user's data actually arrives on."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.ratelimit import RateLimiter
from app.ingest import ColumnMapping, CsvIngestError, parse_csv
from app.main import app as fastapi_app

SIMPLE_CSV = b"""text,user_type,source
Signup is broken for our whole team,enterprise,support
Billing charged us twice,paid,support
The dashboard is very slow,free,review
"""


@pytest_asyncio.fixture
async def client(runtime, session_factory, settings, workspace):
    fastapi_app.state.runtime = runtime
    fastapi_app.state.session_factory = session_factory
    fastapi_app.state.settings = settings
    fastapi_app.state.rate_limiter = RateLimiter(
        capacity=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
        headers={"X-API-Key": workspace.api_key},
    ) as async_client:
        yield async_client


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def test_parses_a_well_formed_export():
    items = parse_csv(SIMPLE_CSV)

    assert len(items) == 3
    assert items[0]["text"] == "Signup is broken for our whole team"
    assert items[0]["user_type"] == "enterprise"
    assert items[0]["source"] == "support"


def test_text_column_alone_is_enough():
    """The minimum viable upload is one column; everything else defaults."""
    items = parse_csv(b"text\nSignup is broken\n")

    assert items[0]["user_type"] == "free"
    assert items[0]["source"] == "other"
    assert items[0]["id"] == "csv-1"


def test_custom_column_mapping():
    csv_bytes = b"ticket_id,body,plan\n42,Export is missing,paid\n"
    items = parse_csv(
        csv_bytes, ColumnMapping(text="body", user_type="plan", id="ticket_id")
    )

    assert items[0]["text"] == "Export is missing"
    assert items[0]["user_type"] == "paid"
    assert items[0]["id"] == "42"


def test_unrecognised_tier_falls_back_rather_than_failing_the_upload():
    """A stray value in one cell should not cost the user their whole file."""
    items = parse_csv(b"text,user_type\nSignup broken,Platinum\n")
    assert items[0]["user_type"] == "free"


def test_blank_rows_are_skipped_not_errors():
    items = parse_csv(b"text\nSignup broken\n\n   \nBilling wrong\n")
    assert len(items) == 2


def test_utf8_bom_is_handled():
    """Excel writes a BOM; without stripping it the first header is mangled."""
    items = parse_csv("﻿text\nSignup is broken\n".encode("utf-8"))
    assert items[0]["text"] == "Signup is broken"


def test_missing_text_column_names_the_columns_it_did_find():
    with pytest.raises(CsvIngestError) as excinfo:
        parse_csv(b"comment,plan\nSignup broken,paid\n")

    message = str(excinfo.value)
    assert "text" in message
    assert "comment" in message, "error should list the columns actually present"


def test_empty_file_is_rejected():
    with pytest.raises(CsvIngestError, match="empty"):
        parse_csv(b"")


def test_header_only_file_is_rejected():
    with pytest.raises(CsvIngestError, match="No usable rows"):
        parse_csv(b"text,user_type\n")


def test_non_utf8_is_rejected_with_an_actionable_message():
    with pytest.raises(CsvIngestError, match="UTF-8"):
        parse_csv(b"text\n\xff\xfeSignup\n")


def test_row_limit_is_enforced():
    rows = b"text\n" + b"".join(
        f"Signup broken number {n}\n".encode() for n in range(250)
    )
    with pytest.raises(CsvIngestError, match="more than 200 rows"):
        parse_csv(rows, max_items=200)


def test_oversized_cell_is_rejected():
    rows = "text\n" + ("x" * 6000) + "\n"
    with pytest.raises(CsvIngestError, match="character limit"):
        parse_csv(rows.encode(), max_chars=5000)


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------


async def test_csv_upload_runs_the_pipeline(client):
    response = await client.post(
        "/analyze/csv", files={"file": ("export.csv", SIMPLE_CSV, "text/csv")}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["analyzed"]) == 3
    assert body["themes"]
    assert body["run_id"]


async def test_csv_upload_accepts_a_column_mapping(client):
    csv_bytes = b"ticket,body\n7,Signup is broken for everyone\n"
    response = await client.post(
        "/analyze/csv",
        files={"file": ("zendesk.csv", csv_bytes, "text/csv")},
        data={"text_column": "body", "id_column": "ticket"},
    )

    assert response.status_code == 200
    assert response.json()["analyzed"][0]["id"] == "7"


async def test_malformed_csv_returns_422_with_a_useful_message(client):
    response = await client.post(
        "/analyze/csv",
        files={"file": ("bad.csv", b"comment\nSignup broken\n", "text/csv")},
    )

    assert response.status_code == 422
    assert "text" in response.json()["detail"]


async def test_csv_upload_requires_auth(runtime, session_factory, settings):
    settings.allow_anonymous_access = False
    fastapi_app.state.runtime = runtime
    fastapi_app.state.session_factory = session_factory
    fastapi_app.state.settings = settings
    fastapi_app.state.rate_limiter = RateLimiter(capacity=100, window_seconds=60)

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as anon:
        response = await anon.post(
            "/analyze/csv", files={"file": ("x.csv", SIMPLE_CSV, "text/csv")}
        )

    assert response.status_code == 401
