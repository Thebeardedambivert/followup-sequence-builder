"""
schemas.py - Strongly-typed Pydantic contracts for the Follow-Up Sequence Builder.
Module: Week 5 Microsoft Agent Framework Project
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# 1. ENUMS FOR STRICT INVARIANTS
# ---------------------------------------------------------------------------

class LeadPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ENTERPRISE = "ENTERPRISE"


class CadenceStep(str, Enum):
    DAY_1_RECAP = "DAY_1_RECAP"
    DAY_3_VALUE_ADD = "DAY_3_VALUE_ADD"
    DAY_7_BREAKUP = "DAY_7_BREAKUP"


# ---------------------------------------------------------------------------
# 2. INBOUND CONTEXT (The Input Contract)
# ---------------------------------------------------------------------------

class InboundLeadContext(BaseModel):
    lead_id: str = Field(..., description="Unique CRM identifier for the prospect")
    client_name: str = Field(..., description="Full name of the prospect")
    client_email: str = Field(..., description="Direct contact email")
    company_name: str = Field(..., description="Company name")
    meeting_transcript: str = Field(..., description="Raw notes or transcript from the discovery call")
    deal_size_estimate: float = Field(default=0.0, ge=0.0, description="Estimated deal value in USD")
    priority: LeadPriority = Field(default=LeadPriority.MEDIUM)


# ---------------------------------------------------------------------------
# 3. SEQUENCE DELIVERABLES (The Output Contract)
# ---------------------------------------------------------------------------

class EmailMessage(BaseModel):
    step: CadenceStep
    delay_days: int = Field(..., ge=0, description="Number of days to wait before sending")
    subject: str = Field(..., min_length=5, description="Compelling, personalized subject line")
    body: str = Field(..., min_length=20, description="Full body text of the follow-up email")
    call_to_action: str = Field(..., description="The single specific action requested")


class FollowUpSequence(BaseModel):
    lead_id: str
    company_name: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    emails: List[EmailMessage] = Field(..., min_length=3, max_length=3)
    requires_human_review: bool = Field(default=False)


if __name__ == "__main__":
    # Self-verification check
    sample_context = InboundLeadContext(
        lead_id="lead_uk_902",
        client_name="Adam Burns",
        client_email="adam@advantageinvestment.co.uk",
        company_name="Advantage Investment",
        meeting_transcript="Discussed automated deal packaging and off-plan BTL pipeline in Liverpool.",
        deal_size_estimate=45000.0,
        priority=LeadPriority.HIGH
    )
    print("InboundLeadContext verified:", sample_context.model_dump_json(indent=2))

    sample_sequence = FollowUpSequence(
        lead_id=sample_context.lead_id,
        company_name=sample_context.company_name,
        emails=[
            EmailMessage(
                step=CadenceStep.DAY_1_RECAP,
                delay_days=1,
                subject="Recap: Deal packaging automation for Advantage Investment",
                body="Hi Adam, great connecting earlier today regarding off-market BTL developments...",
                call_to_action="Confirm if the unit breakdown matches your current Liverpool pipeline."
            ),
            EmailMessage(
                step=CadenceStep.DAY_3_VALUE_ADD,
                delay_days=3,
                subject="Live comps model for Liverpool & Manchester allocations",
                body="Hi Adam, sharing a working demo of the Land Registry comps and stamp duty engine...",
                call_to_action="Let us know if you want to test this on your next 3 development packs."
            ),
            EmailMessage(
                step=CadenceStep.DAY_7_BREAKUP,
                delay_days=7,
                subject="Closing the loop on Advantage Investment zero-cost pilot",
                body="Hi Adam, checking in one last time before releasing our development squad allocation...",
                call_to_action="Reply to claim your 2-week zero-cost pilot sprint."
            ),
        ]
    )
    print("\nFollowUpSequence verified:", sample_sequence.model_dump_json(indent=2))
    print("\n[OK] schemas.py contracts compiled and validated with 100% precision!")
