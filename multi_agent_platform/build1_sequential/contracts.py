"""
contracts.py - Typed Boundary Envelopes for Build 1: Sequential Specialists.
Week 5: Multi-Agent Systems Engineering
"""

from pydantic import BaseModel, Field, field_validator
from typing import List
from enum import Enum


class DealTier(str, Enum):
    STANDARD = "STANDARD"
    ENTERPRISE = "ENTERPRISE"


# ---------------------------------------------------------------------------
# Envelope 1: Extractor (Agent 1) -> Strategist (Agent 2)
# ---------------------------------------------------------------------------
class ExtractedLead(BaseModel):
    client_name: str = Field(..., min_length=2, description="Prospect full name")
    company_name: str = Field(..., min_length=2, description="Prospect company")
    deal_size_usd: float = Field(default=0.0, ge=0.0, description="Estimated deal value")
    core_pain_point: str = Field(..., min_length=15, description="Specific business bottleneck identified")
    deal_tier: DealTier = Field(default=DealTier.STANDARD)

    @field_validator("core_pain_point")
    @classmethod
    def reject_lazy_extractions(cls, value: str) -> str:
        """Deterministic boundary guard preventing hallucinated placeholders."""
        lowered = value.strip().lower()
        banned_phrases = ["none", "n/a", "not mentioned", "unknown"]
        if any(banned in lowered for banned in banned_phrases):
            raise ValueError(
                f"Boundary Violation: 'core_pain_point' contains a lazy placeholder ('{value}'). "
                "Agent 1 must extract a real business problem."
            )
        return value


# ---------------------------------------------------------------------------
# Envelope 2: Strategist (Agent 2) -> Copywriter (Agent 3)
# ---------------------------------------------------------------------------
class CadenceStrategy(BaseModel):
    company_name: str
    deal_tier: DealTier
    day_1_angle: str = Field(..., min_length=10, description="Recap angle focusing on pain point")
    day_3_case_study: str = Field(..., min_length=10, description="Relevant proof of work")
    day_7_urgency_trigger: str = Field(..., min_length=10, description="Final call to action")


# ---------------------------------------------------------------------------
# Envelope 3: Copywriter (Agent 3) -> Dispatch
# ---------------------------------------------------------------------------
class EmailDraft(BaseModel):
    day: int = Field(..., ge=1)
    subject: str = Field(..., min_length=5)
    body: str = Field(..., min_length=20)


class FinalSequence(BaseModel):
    company_name: str
    emails: List[EmailDraft] = Field(..., min_length=3, max_length=3)


if __name__ == "__main__":
    # Test our boundary guard against a lazy extraction
    try:
        ExtractedLead(
            client_name="Sarah Connor",
            company_name="Cyberdyne",
            deal_size_usd=50000.0,
            core_pain_point="None mentioned in call"  # 🚨 Should trigger loud error!
        )
        print("❌ Test Failed: Boundary guard was bypassed!")
    except Exception as e:
        print("[OK] Boundary Guard Triggered Loud Exception:", e)
