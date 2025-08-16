from sqlalchemy.orm import declarative_base, mapped_column, Mapped
from sqlalchemy import String, JSON, TIMESTAMP, func, Integer
import enum
import uuid

Base = declarative_base()

class RunStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Run(Base):
    __tablename__ = "runs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"run_{uuid.uuid4().hex}")
    project_id: Mapped[str] = mapped_column(String, nullable=False)
    conv_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default=RunStatus.QUEUED.value)
    percent: Mapped[int] = mapped_column(Integer, default=0)
    run_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), onupdate=func.now(), server_default=func.now())

class Artifact(Base):
    __tablename__ = "artifacts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"artifact_{uuid.uuid4().hex}")
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # "pr", "file", "log"
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())