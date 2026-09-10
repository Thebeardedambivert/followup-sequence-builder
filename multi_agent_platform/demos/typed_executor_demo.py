from pydantic import BaseModel, Field
from typing import List, Optional
from  enum import Enum
from datetime import datetime

class DealSizeTier(str, Enum):
    TIER_STARTER = "deals < $10k"
    TIER_GROWTH = "deals >= $10k and < $50k"
    TIER_ENTERPRISE = "deals >= $50k"

class ProposalRequest(BaseModel):
    client_name: str
    deal_value: float = Field(..., ge=0, description="The total value of the deal in USD.")
    custom_features_count: int = Field(..., ge=0, 
        description="The number of custom features required.")
        
class ProposalResponse(BaseModel):
    client_name: str
    deal_tier: DealSizeTier
    deal_value: float
    requires_senior_signoff: bool
    summary: str

class ProposalGeneratorExecutor:
    """
    Typed Executor that evaluates deal size, determines tier,
    checks senior sign-off rules, and outputs a ProposalResponse.
    """

    def execute(self, request: ProposalRequest) -> ProposalResponse:
        # 1. Determine the Deal Tier based on deal_value
        if request.deal_value < 10_000:
            tier = DealSizeTier.TIER_STARTER
        elif request.deal_value < 50_000:
            tier = DealSizeTier.TIER_GROWTH
        else:
            tier = DealSizeTier.TIER_ENTERPRISE

        # 2. Check if Senior Sign-off is required:
        # (deal_value > 50,000 OR custom_features_count > 5)
        requires_signoff = (
            request.deal_value > 50_000 
            or request.custom_features_count > 5
        )

        # 3. Create a brief summary
        summary = (
            f"Proposal for {request.client_name}: Tier is {tier.name} "
            f"with {request.custom_features_count} custom features. "
            f"Sign-off required: {requires_signoff}."
        )

        # 4. Return the guaranteed ProposalResponse object!
        return ProposalResponse(
            client_name=request.client_name,
            deal_tier=tier,
            deal_value=request.deal_value,
            requires_senior_signoff=requires_signoff,
            summary=summary
        )

    
if __name__ == "__main__":
    executor = ProposalGeneratorExecutor()

    # Test 1: Starter deal, no signoff
    req1 = ProposalRequest(client_name="Acme Corp", deal_value=5000.0, custom_features_count=2)
    res1 = executor.execute(req1)
    print("Test 1 Result:", res1)
    assert res1.deal_tier == DealSizeTier.TIER_STARTER
    assert res1.requires_senior_signoff is False

    # Test 2: Enterprise deal, requires signoff
    req2 = ProposalRequest(client_name="Global Tech", deal_value=75000.0, custom_features_count=1)
    res2 = executor.execute(req2)
    print("Test 2 Result:", res2)
    assert res2.deal_tier == DealSizeTier.TIER_ENTERPRISE
    assert res2.requires_senior_signoff is True

    # Test 3: Growth deal but high custom features -> requires signoff
    req3 = ProposalRequest(client_name="HyperScale", deal_value=30000.0, custom_features_count=8)
    res3 = executor.execute(req3)
    print("Test 3 Result:", res3)
    assert res3.deal_tier == DealSizeTier.TIER_GROWTH
    assert res3.requires_senior_signoff is True

    print("\nAll 3 Typed Executor tests passed with 100% precision!")
