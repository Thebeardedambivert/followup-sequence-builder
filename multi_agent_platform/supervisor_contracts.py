"""
supervisor_contracts.py - Typed Boundary Envelopes for the Supervisor Coordinator.
Week 5: Multi-Agent Systems Engineering (Build 3)
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# Import our existing envelopes from Build 1 and Build 2
from contracts import ExtractedLead, FinalSequence
from evaluator_contracts import DealClearanceVerdict


class RouteDecision(str, Enum):
    """
    Strict allowable routing destinations.
    Deterministic enforcement: any value outside this enum raises immediate ValidationError.
    """
    FAST_TRACK = "fast_track"             # Standard leads: bypass squad, draft directly
    DEEP_AUDIT = "deep_audit"             # Enterprise leads: require 3-agent parallel clearance
    OPT_OUT_ESCALATE = "opt_out_escalate" # Angry/Unsubscribe leads: halt all marketing
    COMPLETE = "complete"                 # Terminal state


class SupervisorDecision(BaseModel):
    """
    The structured output emitted by the Supervisor Agent.
    """
    route: RouteDecision = Field(
        ..., 
        description="The target specialist station determined by lead classification"
    )
    reasoning: str = Field(
        ..., 
        min_length=10, 
        description="Auditable explanation of why this routing decision was made"
    )
    requires_human_gate: bool = Field(
        default=False, 
        description="Flag indicating if a human must approve before executing this route"
    )


class CoordinatorResult(BaseModel):
    """
    The immutable end-to-end outcome envelope returned by the Coordinator host harness.
    Provides complete evidence (Rule 28): what happened, who was called, and why.
    """
    lead_company: str
    final_route: RouteDecision
    iterations: int = Field(..., ge=1, le=10, description="Total coordinator cycles executed")
    execution_trace: List[str] = Field(default_factory=list, description="Ordered trail of stations visited")
    clearance_verdict: Optional[DealClearanceVerdict] = None
    final_sequence: Optional[FinalSequence] = None
    success: bool
    error_message: Optional[str] = None
    total_latency_ms: float
