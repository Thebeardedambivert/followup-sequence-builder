"""
parallel_evaluator_squad.py - Fan-In Aggregator with Timeout Sensors & Partial Failure Handling.
Week 5: Multi-Agent Systems Engineering (Build 2 Part B)
"""

import asyncio
import time
from typing import List, Tuple, Union

from multi_agent_platform.build1_sequential.contracts import ExtractedLead
from multi_agent_platform.build2_parallel_evaluators.evaluator_contracts import (
    ClearanceStatus,
    DealClearanceVerdict,
    FinancialReport,
    TechnicalReport,
    ComplianceReport,
)
from multi_agent_platform.build2_parallel_evaluators.evaluators import (
    FinancialAuditorAgent,
    TechnicalAuditorAgent,
    ComplianceAuditorAgent,
)


class ParallelEvaluatorSquad:
    """
    Fan-In Aggregator:
    Orchestrates concurrent evaluations, enforces strict timeout bounds,
    isolates partial failures, and applies deterministic clearance rules.
    """
    def __init__(
        self,
        cfo: FinancialAuditorAgent = None,
        architect: TechnicalAuditorAgent = None,
        counsel: ComplianceAuditorAgent = None,
        timeout_seconds: float = 1.5,
    ):
        # Allow dependency injection for testing and failure simulation
        self.cfo = cfo or FinancialAuditorAgent()
        self.architect = architect or TechnicalAuditorAgent()
        self.counsel = counsel or ComplianceAuditorAgent()
        # The hard boundary timeout: no single agent may block the squad longer than this
        self.timeout_seconds = timeout_seconds

    async def _evaluate_with_timeout(self, agent_name: str, coro) -> Union[object, Exception]:
        """
        Helper mechanism: Wraps an agent's coroutine with a timeout sensor.
        If it times out, it converts the TimeoutError into a clear descriptive string or exception.
        """
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            return TimeoutError(f"Agent '{agent_name}' timed out after {self.timeout_seconds}s")
        except Exception as exc:
            return exc

    async def evaluate_deal(self, lead: ExtractedLead) -> DealClearanceVerdict:
        """
        The Fan-In Aggregator:
        1. Fans out evaluations concurrently with timeout sensors.
        2. Aggregates results, isolating exceptions and partial failures.
        3. Applies deterministic clearance policies.
        4. Emits an immutable DealClearanceVerdict envelope with telemetry.
        """
        start_time = time.time()
        partial_failures: List[str] = []
        rejection_reasons: List[str] = []

        # 🚀 FAN-OUT: Launch all 3 evaluators concurrently wrapped with timeout guards
        fin_task = self._evaluate_with_timeout("cfo_auditor", self.cfo.evaluate(lead))
        tech_task = self._evaluate_with_timeout("tech_architect", self.architect.evaluate(lead))
        comp_task = self._evaluate_with_timeout("compliance_counsel", self.counsel.evaluate(lead))

        # Gather results with fault-isolation enabled
        fin_res, tech_res, comp_res = await asyncio.gather(
            fin_task, tech_task, comp_task, return_exceptions=True
        )

        # -------------------------------------------------------------------
        # 1. Inspect Financial Auditor Result
        # -------------------------------------------------------------------
        fin_report: Optional[FinancialReport] = None
        if isinstance(fin_res, Exception):
            partial_failures.append(f"Financial audit failure: {str(fin_res)}")
        else:
            fin_report = fin_res
            if not fin_report.payment_terms_approved:
                rejection_reasons.append("Payment terms rejected by CFO")
            if not fin_report.budget_verified:
                rejection_reasons.append("Budget not verified by CFO")
            if fin_report.risk_score > 7:
                rejection_reasons.append(f"Financial risk score {fin_report.risk_score} exceeds acceptable threshold (7)")

        # -------------------------------------------------------------------
        # 2. Inspect Technical Architect Result
        # -------------------------------------------------------------------
        tech_report: Optional[TechnicalReport] = None
        if isinstance(tech_res, Exception):
            partial_failures.append(f"Technical audit failure: {str(tech_res)}")
        else:
            tech_report = tech_res
            if not tech_report.is_feasible:
                rejection_reasons.append("Architecture feasibility audit marked implementation infeasible")
            if tech_report.estimated_sprint_weeks > 8:
                rejection_reasons.append(f"Sprint estimate ({tech_report.estimated_sprint_weeks}w) exceeds delivery limit (8w)")

        # -------------------------------------------------------------------
        # 3. Inspect Legal & Compliance Counsel Result
        # -------------------------------------------------------------------
        comp_report: Optional[ComplianceReport] = None
        if isinstance(comp_res, Exception):
            partial_failures.append(f"Compliance audit failure: {str(comp_res)}")
        else:
            comp_report = comp_res
            if not comp_report.gdpr_compliant:
                rejection_reasons.append("Lead violates GDPR compliance policies")
            if not comp_report.data_residency_ok:
                rejection_reasons.append("Lead fails data residency sovereignty requirements")

        # -------------------------------------------------------------------
        # 4. Deterministic Clearance Policy Gate (Rule 22 & Rule 27)
        # -------------------------------------------------------------------
        if partial_failures:
            # FAIL-SAFE INVARIANT: Missing reports require human clearance
            status = ClearanceStatus.REQUIRES_HUMAN_REVIEW
            is_auto_cleared = False
        elif rejection_reasons:
            status = ClearanceStatus.REJECTED
            is_auto_cleared = False
        else:
            status = ClearanceStatus.APPROVED
            is_auto_cleared = True

        total_latency_ms = round((time.time() - start_time) * 1000, 2)

        return DealClearanceVerdict(
            company_name=lead.company_name,
            status=status,
            is_auto_cleared=is_auto_cleared,
            rejection_reasons=rejection_reasons,
            financial=fin_report,
            technical=tech_report,
            compliance=comp_report,
            partial_failures=partial_failures,
            total_latency_ms=total_latency_ms,
        )


# ===========================================================================
# Controlled Verification Suite (Happy Path, Hanging Timeout, and Policy Rejection)
# ===========================================================================
if __name__ == "__main__":
    from multi_agent_platform.build1_sequential.contracts import DealTier

    async def run_tests():
        print("\n========================================================")
        print("  TEST 1: Clean Happy Path (Advantage Investment)")
        print("========================================================")
        healthy_lead = ExtractedLead(
            client_name="Adam Burns",
            company_name="Advantage Investment",
            deal_size_usd=45000.0,
            core_pain_point="Manual deal packaging delays off-plan allocation in Liverpool",
            deal_tier=DealTier.STANDARD
        )
        squad = ParallelEvaluatorSquad(timeout_seconds=1.5)
        verdict = await squad.evaluate_deal(healthy_lead)
        
        print(f"Status: {verdict.status.value}")
        print(f"Auto Cleared: {verdict.is_auto_cleared}")
        print(f"Total Latency: {verdict.total_latency_ms} ms")
        assert verdict.status == ClearanceStatus.APPROVED
        assert verdict.is_auto_cleared is True
        assert len(verdict.partial_failures) == 0
        print("[PASS] Test 1: Happy path cleared successfully!")

        print("\n========================================================")
        print("  TEST 2: Controlled Partial Failure (Hanging Legal Agent)")
        print("========================================================")
        # We inject a simulated delay of 3.0s into the compliance counsel,
        # but set our squad boundary timeout to 1.0s!
        hanging_counsel = ComplianceAuditorAgent(simulated_delay=3.0)
        squad_with_timeout = ParallelEvaluatorSquad(counsel=hanging_counsel, timeout_seconds=1.0)
        verdict_failure = await squad_with_timeout.evaluate_deal(healthy_lead)

        print(f"Status: {verdict_failure.status.value}")
        print(f"Auto Cleared: {verdict_failure.is_auto_cleared}")
        print(f"Partial Failures: {verdict_failure.partial_failures}")
        print(f"Financial Report Present: {verdict_failure.financial is not None}")
        print(f"Technical Report Present: {verdict_failure.technical is not None}")
        print(f"Compliance Report Present: {verdict_failure.compliance is not None}")
        print(f"Total Latency: {verdict_failure.total_latency_ms} ms")
        
        # Verify the fail-safe invariant
        assert verdict_failure.status == ClearanceStatus.REQUIRES_HUMAN_REVIEW
        assert verdict_failure.is_auto_cleared is False
        assert len(verdict_failure.partial_failures) == 1
        assert "timed out after 1.0s" in verdict_failure.partial_failures[0]
        # Verify other agents' work was preserved
        assert verdict_failure.financial is not None
        assert verdict_failure.technical is not None
        assert verdict_failure.compliance is None
        print("[PASS] Test 2: System gracefully degraded with partial availability preserved!")

    asyncio.run(run_tests())
