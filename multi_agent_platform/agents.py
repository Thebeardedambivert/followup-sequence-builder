"""
agents.py - Independent Specialist Actors for Build 1: Sequential Specialists.
Week 5: Multi-Agent Systems Engineering
"""

from contracts import (
    ExtractedLead,
    CadenceStrategy,
    FinalSequence,
    EmailDraft,
    DealTier
)


# ---------------------------------------------------------------------------
# Specialist 1: The Extractor
# ---------------------------------------------------------------------------
class LeadExtractorAgent:
    """
    Scans messy discovery call transcripts and distills them into 
    a strictly-typed ExtractedLead contract.
    """
    def __init__(self, agent_name: str = "extractor_alpha"):
        self.agent_name = agent_name

    def process(self, raw_transcript: str) -> ExtractedLead:
        # In production, this executes an LLM call with structured output.
        # Here we demonstrate the deterministic boundary transformation:
        if "Advantage Investment" in raw_transcript:
            return ExtractedLead(
                client_name="Adam Burns",
                company_name="Advantage Investment",
                deal_size_usd=45000.0,
                core_pain_point="Manual deal packaging delays off-plan allocation in Liverpool",
                deal_tier=DealTier.STANDARD
            )
        else:
            # Fallback extraction for enterprise test fixtures
            return ExtractedLead(
                client_name="Sarah Connor",
                company_name="Cyberdyne Systems",
                deal_size_usd=150000.0,
                core_pain_point="Zero real-time telemetry across autonomous factory robots",
                deal_tier=DealTier.ENTERPRISE
            )


# ---------------------------------------------------------------------------
# Specialist 2: The Strategist
# ---------------------------------------------------------------------------
class SequenceStrategistAgent:
    """
    Consumes ExtractedLead and architects the multi-day narrative angle.
    Never sees the raw transcript!
    """
    def __init__(self, agent_name: str = "strategist_beta"):
        self.agent_name = agent_name

    def process(self, lead: ExtractedLead) -> CadenceStrategy:
        # Adjust strategy based on Deal Tier
        if lead.deal_tier == DealTier.ENTERPRISE:
            return CadenceStrategy(
                company_name=lead.company_name,
                deal_tier=lead.deal_tier,
                day_1_angle=f"Immediate executive recap addressing {lead.core_pain_point}",
                day_3_case_study="Whitepaper on ISO-27001 compliant autonomous telemetry",
                day_7_urgency_trigger="Direct line to VP of Engineering for 14-day sandboxed pilot"
            )
        else:
            return CadenceStrategy(
                company_name=lead.company_name,
                deal_tier=lead.deal_tier,
                day_1_angle=f"Operational breakdown solving {lead.core_pain_point}",
                day_3_case_study="Liverpool pipeline automation demo with Land Registry comps",
                day_7_urgency_trigger="Claim 2-week zero-risk sprint before allocation closes"
            )


# ---------------------------------------------------------------------------
# Specialist 3: The Copywriter
# ---------------------------------------------------------------------------
class CopywriterAgent:
    """
    Consumes CadenceStrategy and writes the final 3-email sequence.
    Enforces the min_length=3, max_length=3 production invariant!
    """
    def __init__(self, agent_name: str = "copywriter_gamma"):
        self.agent_name = agent_name

    def process(self, strategy: CadenceStrategy) -> FinalSequence:
        return FinalSequence(
            company_name=strategy.company_name,
            emails=[
                EmailDraft(
                    day=1,
                    subject=f"Recap: Solving bottleneck at {strategy.company_name}",
                    body=f"Hi team, following up on our discussion: {strategy.day_1_angle}. Let me know if you are free tomorrow."
                ),
                EmailDraft(
                    day=3,
                    subject=f"Resource: {strategy.day_3_case_study}",
                    body=f"Sharing relevant benchmark data for {strategy.company_name}: {strategy.day_3_case_study}."
                ),
                EmailDraft(
                    day=7,
                    subject=f"Final check-in regarding {strategy.company_name} pilot",
                    body=f"Checking in one last time before releasing reserved squad slots: {strategy.day_7_urgency_trigger}."
                )
            ]
        )


if __name__ == "__main__":
    # Test each specialist individually in isolation
    extractor = LeadExtractorAgent()
    strategist = SequenceStrategistAgent()
    copywriter = CopywriterAgent()

    # Step 1: Raw transcript -> ExtractedLead
    sample_transcript = "Met with Adam Burns at Advantage Investment. Their Liverpool pipeline is bottlenecked by manual deal packs."
    lead = extractor.process(sample_transcript)
    print("1. Extractor Output:", lead.company_name, "| Deal Size:", lead.deal_size_usd)

    # Step 2: ExtractedLead -> CadenceStrategy
    strategy = strategist.process(lead)
    print("2. Strategist Output:", strategy.day_1_angle)

    # Step 3: CadenceStrategy -> FinalSequence
    sequence = copywriter.process(strategy)
    print(f"3. Copywriter Output: Successfully generated {len(sequence.emails)} emails!")
    print("[OK] All 3 specialists compiled and verified in isolation!")
