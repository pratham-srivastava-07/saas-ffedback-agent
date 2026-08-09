"""Create a workspace and print its API key.

The key is shown once and never stored — only its SHA-256 goes in the
database, so a leaked database does not hand over working credentials. If it
is lost, create another workspace.

    python scripts/create_workspace.py "Acme Product Team"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.api.auth import generate_api_key, hash_api_key  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.store import repo  # noqa: E402
from app.store.migrate import upgrade  # noqa: E402


async def create(name: str, database_url: str) -> int:
    engine = create_async_engine(database_url)
    await upgrade(engine)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    api_key = generate_api_key()
    async with session_factory() as session:
        workspace = await repo.create_workspace(
            session, name=name, api_key_hash=hash_api_key(api_key)
        )

    await engine.dispose()

    print("\nWorkspace created.\n")
    print(f"  Name:  {workspace.name}")
    print(f"  ID:    {workspace.id}")
    print(f"  Key:   {api_key}")
    print(
        "\nThis key is shown once and cannot be recovered. Send it as the "
        "X-API-Key header:\n"
        f'  curl -H "X-API-Key: {api_key}" localhost:8000/themes\n'
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="human-readable workspace name")
    parser.add_argument(
        "--database-url",
        default=None,
        help="defaults to DATABASE_URL / the configured SQLite file",
    )
    args = parser.parse_args()

    database_url = args.database_url or get_settings().database_url
    return asyncio.run(create(args.name, database_url))


if __name__ == "__main__":
    raise SystemExit(main())
