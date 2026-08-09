"""Name the themes that turned out to be genuinely new, and persist them.

Runs *after* taxonomy resolution rather than before, so we spend LLM calls only
on clusters we have never seen. A recurring theme keeps the name it already
has, which is the whole point of a stable taxonomy.
"""

from __future__ import annotations

import logging

from app.graph.nodes._common import call_structured
from app.graph.state import AnalysisState
from app.graph.vectors import cosine_similarity
from app.llm import get_runtime
from app.schemas import ThemeNaming
from app.store import repo
from app.store.models import DEFAULT_WORKSPACE_ID

logger = logging.getLogger(__name__)

SYSTEM = """You name clusters of related SaaS customer feedback.

The name is read by a product manager scanning a ranked list, so it must say \
what is actually wrong or wanted. Name the specific problem, not the emotion.

Good: "OAuth signup fails for Google accounts", "Export missing CSV format"
Bad: "Negative feedback", "User complaints", "Issues"

Under six words."""

_MAX_SAMPLES = 4


def _representative_texts(
    theme: dict, embeddings: dict[str, list[float]], texts: dict[str, str]
) -> list[str]:
    """Pick the items sitting closest to the cluster centre.

    Those are the most typical of the cluster, so the name describes the bulk
    of it rather than an outlier that happened to be first.
    """
    centroid = theme.get("centroid") or []
    ranked = sorted(
        theme.get("item_ids", []),
        key=lambda item_id: -cosine_similarity(centroid, embeddings.get(item_id, [])),
    )
    return [texts[item_id] for item_id in ranked[:_MAX_SAMPLES] if item_id in texts]


async def name_themes(state: AnalysisState, config=None) -> dict:
    runtime = get_runtime(config)
    themes = state.get("themes", [])

    if not themes:
        return {"themes": []}

    embeddings = state.get("embeddings", {})
    texts = {item["id"]: item["text"] for item in state.get("analyzed", [])}

    named: list[dict] = []
    for theme in themes:
        if not theme.get("is_new"):
            named.append(theme)
            continue

        samples = _representative_texts(theme, embeddings, texts)
        joined = "\n".join(f"- {sample}" for sample in samples)

        try:
            naming = await call_structured(
                runtime,
                ThemeNaming,
                SYSTEM,
                f"{len(theme.get('item_ids', []))} users said things like:\n{joined}",
            )
            name, description = naming.name, naming.description
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to name a cluster: %s", exc)
            name = samples[0][:60] if samples else "Unnamed theme"
            description = "Automatic naming failed for this cluster."

        theme = {**theme, "name": name, "description": description}

        if runtime.session_factory is not None:
            async with runtime.session_factory() as session:
                created = await repo.create_theme(
                    session,
                    name=name,
                    description=description,
                    centroid=theme.get("centroid") or [],
                    run_id=state.get("run_id", ""),
                    mentions=theme.get("count", 0),
                    workspace_id=state.get("workspace_id", DEFAULT_WORKSPACE_ID),
                )
                theme["id"] = created.id

        named.append(theme)

    return {"themes": named}
