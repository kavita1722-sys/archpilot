"""SQLAlchemy ORM models for runs, steps, and tool execution events."""

import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RunModel(Base):
    """Represents an overall ArchPilot engineering run."""

    __tablename__ = "runs"

    id = Column(String(64), primary_key=True, index=True)
    task = Column(Text, nullable=False)
    constraints_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="PENDING", index=True)

    normalized_task_json = Column(Text, nullable=True)
    plan_json = Column(Text, nullable=True)
    validation_json = Column(Text, nullable=True)
    final_result_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    steps = relationship(
        "StepModel", back_populates="run", cascade="all, delete-orphan", order_by="StepModel.step_index"
    )
    tool_events = relationship(
        "ToolEventModel", back_populates="run", cascade="all, delete-orphan", order_by="ToolEventModel.timestamp"
    )
    events = relationship(
        "ExecutionEventModel", back_populates="run", cascade="all, delete-orphan", order_by="ExecutionEventModel.timestamp"
    )


class StepModel(Base):
    """Represents a discrete plan step inside a run."""

    __tablename__ = "steps"

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    objective = Column(Text, nullable=False)
    tool_name = Column(String(64), nullable=False)
    inputs_json = Column(Text, nullable=False, default="{}")
    status = Column(String(32), nullable=False, default="PENDING")
    success_criteria = Column(Text, nullable=False)

    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    run = relationship("RunModel", back_populates="steps")


class ToolEventModel(Base):
    """Records individual tool execution telemetry, inputs, and results."""

    __tablename__ = "tool_events"

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    step_id = Column(Integer, nullable=True)
    tool_name = Column(String(64), nullable=False)
    inputs_json = Column(Text, nullable=False)
    output_json = Column(Text, nullable=True)
    status = Column(String(32), nullable=False)  # "success" or "error"
    duration_ms = Column(Float, nullable=False, default=0.0)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    run = relationship("RunModel", back_populates="tool_events")


class ExecutionEventModel(Base):
    """Audit log of high-level workflow state transitions and events."""

    __tablename__ = "execution_events"

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    step_id = Column(Integer, nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    run = relationship("RunModel", back_populates="events")
