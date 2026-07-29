"""SQLAlchemy models.

The taxonomy lives here. ``Theme.centroid`` is what makes themes stable across
runs: a new cluster is compared against stored centroids rather than being
re-named from scratch, which is the direct fix for the old behaviour where
"Signup bug" and "Bug in Signup Flow" were different themes every run.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(16), default="running")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    theme_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list[FeedbackItem]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
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

    run: Mapped[Run] = relationship(back_populates="items")


class ThemeSnapshot(Base):
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
