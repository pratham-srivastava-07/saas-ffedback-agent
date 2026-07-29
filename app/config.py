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
    # A wildcard origin combined with allow_credentials is rejected by
    # browsers, so the allowed origins are named explicitly.
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
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
