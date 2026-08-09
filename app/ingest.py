"""Turning real-world exports into feedback items.

A prospective user's feedback lives in a Zendesk or Intercom CSV export, not
in a hand-assembled JSON array. Requiring them to write the JSON is the
difference between trying the product and closing the tab.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from app.schemas import Source, UserType

_VALID_USER_TYPES = set(UserType.__args__)  # type: ignore[attr-defined]
_VALID_SOURCES = set(Source.__args__)  # type: ignore[attr-defined]


class CsvIngestError(ValueError):
    """Raised for input the caller can fix by editing their file."""


@dataclass
class ColumnMapping:
    text: str = "text"
    user_type: str = "user_type"
    source: str = "source"
    id: str = "id"


def parse_csv(
    content: bytes,
    mapping: ColumnMapping | None = None,
    *,
    max_items: int = 200,
    max_chars: int = 5000,
    default_source: str = "other",
    default_user_type: str = "free",
) -> list[dict]:
    """Parse an uploaded CSV into feedback items.

    Only the text column is mandatory. Everything else falls back to a
    default, so the minimum viable upload is a one-column file.
    """
    mapping = mapping or ColumnMapping()

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvIngestError(
            "File is not valid UTF-8. Re-export it as UTF-8 encoded CSV."
        ) from exc

    if not decoded.strip():
        raise CsvIngestError("The uploaded file is empty.")

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise CsvIngestError("Could not read a header row from the file.")

    headers = {name.strip(): name for name in reader.fieldnames if name}
    if mapping.text not in headers:
        raise CsvIngestError(
            f"No column named {mapping.text!r}. Columns found: "
            f"{sorted(headers) or 'none'}. Pass text_column to map a different one."
        )

    items: list[dict] = []
    for position, row in enumerate(reader, start=1):
        raw_text = (row.get(headers[mapping.text]) or "").strip()
        if not raw_text:
            continue  # Blank rows are padding, not an error.

        if len(raw_text) > max_chars:
            raise CsvIngestError(
                f"Row {position} exceeds the {max_chars}-character limit "
                f"({len(raw_text)} characters)."
            )

        if len(items) >= max_items:
            raise CsvIngestError(
                f"File contains more than {max_items} rows. Split it and "
                "upload in batches."
            )

        user_type = (row.get(headers.get(mapping.user_type, "")) or "").strip()
        source = (row.get(headers.get(mapping.source, "")) or "").strip()
        external_id = (row.get(headers.get(mapping.id, "")) or "").strip()

        items.append(
            {
                "id": external_id or f"csv-{position}",
                "text": raw_text,
                # Unrecognised values fall back rather than 422 the whole
                # upload: a stray "Pro" in a tier column should not cost the
                # user their entire file.
                "user_type": user_type if user_type in _VALID_USER_TYPES else default_user_type,
                "source": source if source in _VALID_SOURCES else default_source,
            }
        )

    if not items:
        raise CsvIngestError(
            f"No usable rows found. Every {mapping.text!r} value was empty."
        )

    return items
