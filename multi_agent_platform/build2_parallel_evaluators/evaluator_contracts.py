"""
evaluator_contracts.py - Typed Envelopes for Build 2: Parallel Fan-Out / Fan-In.
Week 5: Multi-Agent Systems Engineering
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ClearanceStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"


# ---------------------------------------------------------------------------
# Envelope 1: Financial Auditor Report
# ---------------------------------------------------------------------------
class FinancialReport(BaseModel):
    evaluator_name: str = "financial_auditor"
    risk_score: int = Field(..., ge=1, le=10, description="1 is low risk, 10 is high risk")
    payment_terms_approved: bool
    budget_verified: bool
    flags: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Envelope 2: Technical Feasibility Report
# ---------------------------------------------------------------------------
class TechnicalReport(BaseModel):
    evaluator_name: str = "technical_architect"
    is_feasible: bool
    estimated_sprint_weeks: int = Field(..., ge=1)
    infrastructure_requirements: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Envelope 3: Legal & Compliance Report
# ---------------------------------------------------------------------------
class ComplianceReport(BaseModel):
    evaluator_name: str = "compliance_counsel"
    gdpr_compliant: bool
    data_residency_ok: bool
    risk_level: str = Field(default="LOW")


# ---------------------------------------------------------------------------
# The Consolidated Deliverable (Fan-In Aggregation)
# ---------------------------------------------------------------------------
class DealClearanceVerdict(BaseModel):
    company_name: str
    status: ClearanceStatus
    is_auto_cleared: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    financial: Optional[FinancialReport] = None
    technical: Optional[TechnicalReport] = None
    compliance: Optional[ComplianceReport] = None
    partial_failures: List[str] = Field(default_factory=list)
    total_latency_ms: float = 0.0


if __name__ == "__main__":
    # Test valid aggregation envelope
    sample_verdict = DealClearanceVerdict(
        company_name="Cyberdyne Systems",
        status=ClearanceStatus.APPROVED,
        is_auto_cleared=True,
        financial=FinancialReport(risk_score=2, payment_terms_approved=True, budget_verified=True),
        technical=TechnicalReport(is_feasible=True, estimated_sprint_weeks=2),
        compliance=ComplianceReport(gdpr_compliant=True, data_residency_ok=True)
    )
    print("Sample Verdict Schema Validated:", sample_verdict.status.value)
    print("[OK] evaluator_contracts.py compiled successfully!")
