"""SQLAlchemy models.

The taxonomy lives here. ``Theme.centroid`` is what makes themes stable across
runs: a new cluster is compared against stored centroids rather than being
re-named from scratch, which is the direct fix for the old behaviour where
"Signup bug" and "Bug in Signup Flow" were different themes every run.

Everything is scoped to a :class:`Workspace`. Without that, two tenants of one
deployment share a taxonomy — company A's "Billing issues" absorbs company B's
— which makes themes and trends meaningless the moment a second user appears.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Single-user installs, the demo seeder and every pre-tenancy row land here.
DEFAULT_WORKSPACE_ID = "default"
DEFAULT_WORKSPACE_NAME = "Default workspace"


def _utcnow() -> datetime:
    """Naive UTC.

    The columns are plain ``DateTime``, so SQLite hands back naive values on
    reload. Storing aware ones meant a freshly-created object and the same row
    re-read compared as different types, which blows up any datetime
    comparison against them.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

    # Only ever the SHA-256 of the key. The key itself is shown once, at
    # creation, and is not recoverable afterwards.
    api_key_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class User(Base):
    """An email/password login that owns exactly one workspace.

    Login returns that workspace's API key rather than minting a session, so
    the key auth built earlier stays the single source of truth and there is
    no second credential system to keep consistent.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

    # scrypt digest and its per-user random salt, both hex. stdlib only —
    # no bcrypt/argon2 dependency for this.
    password_hash: Mapped[str] = mapped_column(String(256))
    salt: Mapped[str] = mapped_column(String(64))

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"), index=True, default=DEFAULT_WORKSPACE_ID
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(16), default="running")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    theme_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Trends are stored rather than recomputed from snapshots because the
    # "emerging" verdict depends on whether the theme was new *at the time*,
    # which no snapshot records. Reconstruction would silently relabel every
    # first appearance.
    trends: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[list | None] = mapped_column(JSON, nullable=True)

    items: Mapped[list[FeedbackItem]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"), index=True, default=DEFAULT_WORKSPACE_ID
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")

    # Running mean of the cluster centroids that have matched this theme.
    centroid: Mapped[list] = mapped_column(JSON)

    first_seen_run: Mapped[str] = mapped_column(String(36))
    run_count: Mapped[int] = mapped_column(Integer, default=1)
    total_mentions: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"), index=True, default=DEFAULT_WORKSPACE_ID
    )
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text)
    user_type: Mapped[str] = mapped_column(String(16))
    source: Mapped[str] = mapped_column(String(32))

    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(16), nullable=True)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feature_area: Mapped[str | None] = mapped_column(String(120), nullable=True)
    churn_risk: Mapped[bool] = mapped_column(Boolean, default=False)

    theme_id: Mapped[str | None] = mapped_column(
        ForeignKey("themes.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="ok")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PCA projection of this item's embedding, for the 3D cluster explorer.
    # Only the projection is stored, not the 768-dim vector: the scatter plot
    # is its only consumer and SQLite is not a vector store. The trade is that
    # PCA is fit per run, so coordinates from two runs are in different bases
    # and must never be plotted on shared axes.
    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    z: Mapped[float | None] = mapped_column(Float, nullable=True)

    run: Mapped[Run] = relationship(back_populates="items")


class ThemeSnapshot(Base):
    """One theme's standing in one run. Scoped via its theme."""

    __tablename__ = "theme_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    theme_id: Mapped[str] = mapped_column(ForeignKey("themes.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    count: Mapped[int] = mapped_column(Integer, default=0)

    # Share of the run, not raw count. Comparing raw counts across runs of
    # different sizes would report a spike whenever someone uploads a bigger
    # file, which is not a trend.
    share: Mapped[float] = mapped_column(Float, default=0.0)

    avg_severity: Mapped[float] = mapped_column(Float, default=0.0)
    positive: Mapped[int] = mapped_column(Integer, default=0)
    neutral: Mapped[int] = mapped_column(Integer, default=0)
    negative: Mapped[int] = mapped_column(Integer, default=0)
    churn_risk_count: Mapped[int] = mapped_column(Integer, default=0)

    # Kept so a past run's ranked view can be rebuilt exactly as it was shown.
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
