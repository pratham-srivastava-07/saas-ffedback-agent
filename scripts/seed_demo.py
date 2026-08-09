"""Replay the demo corpus so the taxonomy and trend history are populated.

Every week goes through the real graph — clustering, taxonomy reconciliation
and trend detection all run for real. Nothing is inserted directly into the
tables, so what you see afterwards is what the pipeline actually produces.

    python scripts/seed_demo.py --offline --reset     # no API key needed
    python scripts/seed_demo.py --reset               # real models

``--offline`` swaps in the deterministic providers the test suite uses, which
means the whole demo runs in seconds with no key, no network and no spend.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app import service  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.llm import Runtime, build_runtime  # noqa: E402
from app.store.migrate import upgrade  # noqa: E402
from scripts.demo_data import weeks_with_ids  # noqa: E402

DEFAULT_DB = REPO_ROOT / "sentilytics.db"

_DIRECTION_MARK = {
    "spiking": "^^",
    "emerging": "**",
    "declining": "vv",
    "steady": "--",
    "insufficient_history": "??",
}


def _offline_runtime(session_factory) -> Runtime:
    """Deterministic providers, borrowed from the test suite.

    Importing test helpers from a script is a deliberate trade: duplicating
    the fakes would let the demo and the tests drift apart.
    """
    try:
        from tests.fakes import FakeChat, FakeEmbeddings
    except ModuleNotFoundError as exc:  # pragma: no cover - container path
        raise SystemExit(
            "--offline needs the test helpers, which are not shipped in the "
            "Docker image. Run it from a clone, or drop --offline and set "
            "GROQ_API_KEY and GOOGLE_API_KEY."
        ) from exc

    return Runtime(
        chat=FakeChat(overrides={}, fail_on=set(), calls=[]),
        embeddings=FakeEmbeddings(),
        settings=get_settings(),
        session_factory=session_factory,
    )


async def seed(database: Path, offline: bool, reset: bool) -> int:
    if reset and database.exists():
        database.unlink()
        print(f"Removed existing database at {database}")

    engine = create_async_engine(f"sqlite+aiosqlite:///{database}")
    # Goes through the real startup path so the default workspace exists;
    # the demo seeds into it.
    await upgrade(engine)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    runtime = (
        _offline_runtime(session_factory)
        if offline
        else build_runtime(get_settings(), session_factory)
    )

    weeks = weeks_with_ids()
    print(f"\nReplaying {len(weeks)} weeks through the pipeline"
          f"{' (offline providers)' if offline else ''}...\n")

    result = {}
    for label, items in weeks:
        result = await service.analyze(runtime, items)
        rejected = len(result["rejected"])
        print(
            f"  {label:<34} {len(result['analyzed']):>2} analysed, "
            f"{rejected} rejected, {len(result['themes'])} themes"
        )

    _report(result)
    await engine.dispose()
    return 0


def _report(final: dict) -> None:
    trends = {trend["theme_id"]: trend for trend in final.get("trends", [])}

    print("\n" + "=" * 72)
    print("FINAL RUN — themes ranked by impact")
    print("=" * 72)

    for theme in final.get("themes", []):
        trend = trends.get(theme["id"], {})
        direction = trend.get("direction", "unknown")
        mark = _DIRECTION_MARK.get(direction, "  ")
        print(
            f"\n{mark} {theme['name']}  "
            f"[impact {theme['impact_score']}, {theme['count']} mentions, "
            f"severity {theme['avg_severity']}/5]"
        )
        print(f"     {direction}: {trend.get('detail', '')}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(final.get("summary", ""))

    recommendations = final.get("recommendations", [])
    if recommendations:
        print("\nRECOMMENDED ACTIONS")
        for index, rec in enumerate(recommendations, start=1):
            print(f"  {index}. [{rec.get('effort')}] {rec.get('title')}")
            print(f"     {rec.get('rationale')}")

    print(
        "\nStart the API and the history is already there:"
        "\n  uvicorn app.main:app --reload"
        "\n  curl localhost:8000/themes/trends\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use deterministic fake providers (no API key, no network)",
    )
    parser.add_argument(
        "--reset", action="store_true", help="delete the database first"
    )
    parser.add_argument(
        "--database", type=Path, default=DEFAULT_DB, help="SQLite file to write"
    )
    args = parser.parse_args()

    return asyncio.run(seed(args.database, args.offline, args.reset))


if __name__ == "__main__":
    raise SystemExit(main())
