"""
debate_contracts.py - Strongly-typed contracts for Build 4: Debate & Consensus.
Week 5: Multi-Agent Systems Engineering
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from enum import Enum
from contracts import EmailDraft



# ---------------------------------------------------------------------------
# 1. ENUMS FOR STRICT INVARIANTS
# ---------------------------------------------------------------------------

class CritiqueSeverity(str, Enum):
    """
    Categorizes how dangerous a mistake is.
    BLOCKER = Legally hazardous or technically impossible (deal cannot send).
    WARNING = Minor wording polish or soft tone issue.
    """
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


class CritiqueCategory(str, Enum):
    """
    The exact domain boundary that was violated.
    """
    UNREALISTIC_TIMELINE = "UNREALISTIC_TIMELINE"   # e.g. Promising 1 week when tech said 4 weeks
    UNVERIFIED_CLAIM = "UNVERIFIED_CLAIM"           # e.g. Claiming 100% zero downtime
    PRICING_MISMATCH = "PRICING_MISMATCH"           # e.g. Quoting under company minimums


# ---------------------------------------------------------------------------
# 2. THE INDIVIDUAL CRITIQUE ATOM
# ---------------------------------------------------------------------------

class CritiquePoint(BaseModel):
    """
    A single specific objection raised by the Critic against the Copywriter's draft.
    """
    category: CritiqueCategory
    severity: CritiqueSeverity
    offending_text: str = Field(..., description="The exact sentence or phrase in the draft that broke policy")
    feedback: str = Field(..., description="Why this claim is dangerous or incorrect")
    suggested_fix: str = Field(..., description="Guidance on how the copywriter should rewrite it")



# ---------------------------------------------------------------------------
# 3. THE CRITIC'S AUDIT REPORT
# ---------------------------------------------------------------------------

class CritiqueReport(BaseModel):
    """
    Emitted by the Critic after reviewing a draft.
    Can contain multiple critique points.
    """
    round_number: int = Field(..., ge=1)
    is_approved: bool
    critique_points: List[CritiquePoint] = Field(default_factory=list)
    summary: str = Field(..., description="High-level feedback for the copywriter")

    @model_validator(mode="after")
    def reject_approved_with_blockers(self) -> "CritiqueReport":
        """
        Deterministic Invariant: You cannot mark a draft as approved 
        if there is still an unresolved BLOCKER!
        """
        has_blocker = any(p.severity == CritiqueSeverity.BLOCKER for p in self.critique_points)
        if self.is_approved and has_blocker:
            raise ValueError(
                "Integrity Violation: Critic marked report as approved, "
                "but BLOCKER severity critiques are still present!"
            )
        return self


# ---------------------------------------------------------------------------
# 4. THE COPYWRITER'S DRAFT ENVELOPE
# ---------------------------------------------------------------------------

class DebateDraft(BaseModel):
    """
    The deliverable submitted by the Copywriter on each round of debate.
    """
    round_number: int = Field(..., ge=1)
    emails: List[EmailDraft] = Field(..., min_length=3, max_length=3)
    revision_notes: Optional[str] = Field(
        default=None, 
        description="Explains what changes the copywriter made in response to earlier feedback"
    )


# ---------------------------------------------------------------------------
# 5. THE FINAL CONSENSUS DELIVERABLE
# ---------------------------------------------------------------------------

class ConsensusVerdict(BaseModel):
    """
    The final output of the Debate Orchestrator.
    Tells the company whether the agents agreed, or if they argued until timeout.
    """
    converged: bool = Field(..., description="True if Critic and Copywriter reached agreement")
    total_rounds: int
    final_draft: Optional[DebateDraft] = None
    unresolved_blockers: List[str] = Field(default_factory=list)
    audit_trail: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# VERIFICATION BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Test valid approval
    report = CritiqueReport(
        round_number=1,
        is_approved=True,
        critique_points=[],
        summary="All claims substantiated and timelines match technical feasibility."
    )
    print("Compiled CritiqueReport schema:", report.is_approved)
    print("[OK] debate_contracts.py compiled successfully!")

