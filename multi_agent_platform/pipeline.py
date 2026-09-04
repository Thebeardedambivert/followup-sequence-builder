"""
pipeline.py - Factory Floor Foreman for Build 1: Sequential Specialists.
Week 5: Multi-Agent Systems Engineering
"""

import time
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from contracts import ExtractedLead, CadenceStrategy, FinalSequence
from agents import LeadExtractorAgent, SequenceStrategistAgent, CopywriterAgent


# ---------------------------------------------------------------------------
# Telemetry & Execution Contract (Rule 28: Observability as Evidence)
# ---------------------------------------------------------------------------
class PipelineResult(BaseModel):
    success: bool
    final_sequence: Optional[FinalSequence] = None
    step_failed: Optional[str] = None
    error_message: Optional[str] = None
    telemetry: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# The Factory Floor Foreman (The Orchestrator)
# ---------------------------------------------------------------------------
class SequentialLeadPipeline:
    """
    Orchestrates the assembly line:
    Raw Transcript -> Extractor -> Strategist -> Copywriter -> Final Deliverable.
    Enforces boundary isolation and step-level error handling.
    """
    def __init__(self):
        self.extractor = LeadExtractorAgent(agent_name="station_1_extractor")
        self.strategist = SequenceStrategistAgent(agent_name="station_2_strategist")
        self.copywriter = CopywriterAgent(agent_name="station_3_copywriter")

    def run(self, raw_transcript: str) -> PipelineResult:
        start_time = time.time()
        telemetry: Dict[str, Any] = {}

        # -------------------------------------------------------------------
        # Station 1: The Extractor
        # -------------------------------------------------------------------
        s1_start = time.time()
        try:
            lead: ExtractedLead = self.extractor.process(raw_transcript)
            telemetry["station_1_extractor"] = {
                "status": "SUCCESS",
                "duration_ms": round((time.time() - s1_start) * 1000, 2),
                "deal_tier": lead.deal_tier.value
            }
        except Exception as e:
            return PipelineResult(
                success=False,
                step_failed="station_1_extractor",
                error_message=str(e),
                telemetry={"station_1_extractor": {"status": "FAILED", "error": str(e)}}
            )

        # -------------------------------------------------------------------
        # Station 2: The Strategist
        # -------------------------------------------------------------------
        s2_start = time.time()
        try:
            strategy: CadenceStrategy = self.strategist.process(lead)
            telemetry["station_2_strategist"] = {
                "status": "SUCCESS",
                "duration_ms": round((time.time() - s2_start) * 1000, 2),
                "day_1_angle": strategy.day_1_angle
            }
        except Exception as e:
            return PipelineResult(
                success=False,
                step_failed="station_2_strategist",
                error_message=str(e),
                telemetry=telemetry
            )

        # -------------------------------------------------------------------
        # Station 3: The Copywriter
        # -------------------------------------------------------------------
        s3_start = time.time()
        try:
            sequence: FinalSequence = self.copywriter.process(strategy)
            telemetry["station_3_copywriter"] = {
                "status": "SUCCESS",
                "duration_ms": round((time.time() - s3_start) * 1000, 2),
                "emails_generated": len(sequence.emails)
            }
        except Exception as e:
            return PipelineResult(
                success=False,
                step_failed="station_3_copywriter",
                error_message=str(e),
                telemetry=telemetry
            )

        total_duration_ms = round((time.time() - start_time) * 1000, 2)
        telemetry["total_pipeline_duration_ms"] = total_duration_ms

        return PipelineResult(
            success=True,
            final_sequence=sequence,
            telemetry=telemetry
        )


if __name__ == "__main__":
    pipeline = SequentialLeadPipeline()

    print("=================================================================")
    print("TEST 1: HAPPY PATH (Clean Advantage Investment Transcript)")
    print("=================================================================")
    clean_transcript = "Met with Adam Burns at Advantage Investment. Their Liverpool pipeline is bottlenecked by manual deal packs."
    res1 = pipeline.run(clean_transcript)
    print("Success:", res1.success)
    print("Company:", res1.final_sequence.company_name)
    print(f"Emails Generated: {len(res1.final_sequence.emails)}")
    print("Telemetry:", res1.telemetry)
    assert res1.success is True
    assert len(res1.final_sequence.emails) == 3

    print("\n=================================================================")
    print("TEST 2: CONTROLLED FAILURE (Rule 23: Boundary Violation Injection)")
    print("=================================================================")
    # We deliberately inject a transcript that triggers a lazy extraction failure!
    corrupted_transcript = "Met with client. Bottleneck: none."
    
    # We temporarily simulate a lazy extraction failure
    class BrokenExtractor(LeadExtractorAgent):
        def process(self, text: str) -> ExtractedLead:
            return ExtractedLead(
                client_name="John Doe",
                company_name="Acme Corp",
                deal_size_usd=10000.0,
                core_pain_point="None mentioned"  # 🚨 Boundary Guard will trigger!
            )
            
    broken_pipeline = SequentialLeadPipeline()
    broken_pipeline.extractor = BrokenExtractor()
    res2 = broken_pipeline.run(corrupted_transcript)
    
    print("Success:", res2.success)
    print("Step Failed:", res2.step_failed)
    print("Observed Error:", res2.error_message)
    assert res2.success is False
    assert res2.step_failed == "station_1_extractor"
    print("\n[OK] Build 1: Sequential Specialist Pipeline completely verified!")
