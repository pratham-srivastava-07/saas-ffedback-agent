"""Application settings, loaded from the environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- providers -------------------------------------------------------
    groq_api_key: str | None = None
    google_api_key: str | None = None

    chat_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "models/text-embedding-004"

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
    cluster_distance_threshold: float = 0.35

    # Cosine *similarity* above which a new cluster is considered the same
    # theme as one we have already seen and stored. This is the number most
    # likely to need tuning against real feedback: too low and unrelated
    # themes merge, too high and the taxonomy churns every run.
    theme_merge_threshold: float = 0.82

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
