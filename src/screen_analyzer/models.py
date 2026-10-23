"""Auditable machine-readable report schema."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Finding(StrictModel):
    kind: Literal["observed", "inferred", "uncertain"]
    text: str = Field(min_length=1, max_length=600)
    evidence_frames: list[int] = Field(default_factory=list)


class WorkflowStep(StrictModel):
    order: int = Field(ge=1)
    action: str = Field(min_length=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    evidence_frames: list[int] = Field(min_length=1)


class Segment(StrictModel):
    title: str = Field(min_length=1)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    evidence_frames: list[int] = Field(min_length=1)


class MarketingMoment(StrictModel):
    hook: str = Field(min_length=1)
    timestamp_ms: int = Field(ge=0)
    evidence_frames: list[int] = Field(min_length=1)
    rationale_kind: Literal["observed", "inferred"] = "inferred"


class Analysis(StrictModel):
    app_summary: str = Field(min_length=1)
    workflow_steps: list[WorkflowStep]
    segments: list[Segment]
    marketing_moments: list[MarketingMoment] = Field(max_length=3)
    findings: list[Finding]

    @model_validator(mode="after")
    def check_integrity(self):
        if any(s.end_ms < s.start_ms for s in self.workflow_steps):
            raise ValueError("workflow end precedes start")
        if any(s.end_ms < s.start_ms for s in self.segments):
            raise ValueError("segment end precedes start")
        return self
