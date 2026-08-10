"""Application settings, loaded from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- providers -------------------------------------------------------
    groq_api_key: str | None = None
    google_api_key: str | None = None

    chat_model: str = "llama-3.3-70b-versatile"
    # text-embedding-004 was retired and now 404s on v1beta. Ask the API for
    # the current list with ModelService.ListModels if this one goes the same
    # way. Changing it after data exists invalidates every stored centroid —
    # see the dimension guard in app/graph/vectors.py.
    embedding_model: str = "models/gemini-embedding-001"

    # --- storage ---------------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./sentilytics.db"

    # --- http ------------------------------------------------------------
    # Comma-separated rather than a JSON list so it can be set from a plain
    # environment variable without shell-quoting a JSON array. A wildcard
    # origin combined with allow_credentials is rejected by browsers, so
    # origins are always named explicitly.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- auth ------------------------------------------------------------
    # Off by default: a deployed instance must not accept anonymous requests,
    # because /analyze spends real money on every call. Turn this on only for
    # local single-user work, where it maps unkeyed requests to the default
    # workspace.
    allow_anonymous_access: bool = False

    # --- rate limiting ---------------------------------------------------
    # In-process token bucket, per workspace. Deliberately no Redis: this is
    # per-process, so N workers means N times the limit. Documented, not
    # hidden — it is a real limitation of the simple approach.
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    # --- run hygiene -----------------------------------------------------
    # A crash leaves a run stuck at "running" forever; startup fails anything
    # older than this.
    stale_run_minutes: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    # --- request bounds --------------------------------------------------
    max_items_per_request: int = 200
    max_chars_per_item: int = 5000

    # A large batch fans out one LLM call per item. Without a cap we would
    # open 200 concurrent connections and trip provider rate limits.
    max_concurrent_llm_calls: int = 8

    # Unbounded cycles are how a LangGraph demo hangs in front of an audience.
    max_critique_revisions: int = 2

    # --- clustering ------------------------------------------------------
    # Cosine distance below which two items join the same cluster.
    #
    # Measured against gemini-embedding-001 on a labelled sample: same-topic
    # pairs fall in 0.070-0.217, different-topic pairs in 0.224-0.309. 0.22
    # sits in the gap. The previous 0.35 was fitted to nothing but the test
    # suite's fake embedder, whose vectors are orthogonal — at that value
    # every unrelated pair in the sample merged, collapsing a whole batch
    # into one theme.
    #
    # When in doubt, err low. An over-split shows two themes that should be
    # one, which is visible and annoying. An over-merge silently files praise
    # under a churn-risk bug, which is a lie the UI has no way to catch.
    cluster_distance_threshold: float = 0.22

    # Cosine *similarity* above which a new cluster is considered the same
    # theme as one we have already seen and stored. This is the number most
    # likely to need tuning against real feedback: too low and unrelated
    # themes merge, too high and the taxonomy churns every run.
    #
    # This is the same number as cluster_distance_threshold seen from the
    # other side: similarity 0.78 == distance 0.22. They must move together.
    # At the old 0.82 (distance 0.18) genuinely recurring themes measured up
    # to 0.217 apart would fail to match and be recreated every run — the
    # taxonomy churn this project exists to prevent.
    theme_merge_threshold: float = 0.78

    # --- trends ----------------------------------------------------------
    # Below this many prior snapshots we report insufficient history rather
    # than inventing a percentage from two data points.
    min_snapshots_for_trend: int = 3
    spike_ratio: float = 2.0
    decline_ratio: float = 0.5

    # --- prioritisation --------------------------------------------------
    # Blast radius: a paying customer's complaint outranks a free user's.
    user_tier_weights: dict[str, float] = {
        "enterprise": 3.0,
        "paid": 2.0,
        "free": 1.0,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
