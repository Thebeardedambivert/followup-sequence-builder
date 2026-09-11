"""
supervisor.py - Dynamic Routing Supervisor & Host Coordinator Engine.
Week 5: Multi-Agent Systems Engineering (Build 3)
"""

import asyncio
import time
from typing import List, Optional

from multi_agent_platform.build1_sequential.contracts import ExtractedLead, DealTier, CadenceStrategy, FinalSequence
from multi_agent_platform.build1_sequential.agents import SequenceStrategistAgent, CopywriterAgent
from multi_agent_platform.build2_parallel_evaluators.evaluator_contracts import ClearanceStatus, DealClearanceVerdict
from multi_agent_platform.build2_parallel_evaluators.evaluators import FinancialAuditorAgent, TechnicalAuditorAgent, ComplianceAuditorAgent
from multi_agent_platform.build2_parallel_evaluators.parallel_evaluator_squad import ParallelEvaluatorSquad
from multi_agent_platform.build3_supervisor.supervisor_contracts import RouteDecision, SupervisorDecision, CoordinatorResult


class LeadSupervisorAgent:
    """
    The Triage Doctor:
    Analyzes lead metadata, intent signals, and risk factors to produce a typed routing decision.
    """
    def decide_route(self, lead: ExtractedLead) -> SupervisorDecision:
        # 1. Immediate Safety / Compliance Check
        opt_out_keywords = ["unsubscribe", "stop emailing", "remove me", "not interested", "do not contact"]
        if any(keyword in lead.core_pain_point.lower() for keyword in opt_out_keywords):
            return SupervisorDecision(
                route=RouteDecision.OPT_OUT_ESCALATE,
                reasoning=f"Lead expressed opt-out or negative contact intent: '{lead.core_pain_point}'. Escalating to compliance.",
                requires_human_gate=False
            )

        # 2. Enterprise Tier or High Value -> Deep Parallel Audit
        if lead.deal_tier == DealTier.ENTERPRISE or lead.deal_size_usd >= 50000.0:
            return SupervisorDecision(
                route=RouteDecision.DEEP_AUDIT,
                reasoning=f"Enterprise deal (${lead.deal_size_usd:,.2f}) requires multi-specialist squad clearance.",
                requires_human_gate=False
            )

        # 3. Standard / Mid-Market Lead -> Fast Track
        return SupervisorDecision(
            route=RouteDecision.FAST_TRACK,
            reasoning=f"Standard tier deal (${lead.deal_size_usd:,.2f}) qualifies for accelerated direct drafting.",
            requires_human_gate=False
        )


class SupervisorCoordinator:
    """
    The Host Coordinator Engine:
    Executes the dynamic routing loop, enforces iteration ceilings (circuit breaker),
    and applies deterministic clearance gates before specialist invocation.
    """
    def __init__(
        self,
        supervisor: Optional[LeadSupervisorAgent] = None,
        evaluator_squad: Optional[ParallelEvaluatorSquad] = None,
        strategist: Optional[SequenceStrategistAgent] = None,
        copywriter: Optional[CopywriterAgent] = None,
        max_iterations: int = 3,
    ):
        self.supervisor = supervisor or LeadSupervisorAgent()
        self.evaluator_squad = evaluator_squad or ParallelEvaluatorSquad()
        self.strategist = strategist or SequenceStrategistAgent()
        self.copywriter = copywriter or CopywriterAgent()
        self.max_iterations = max_iterations

    async def process_lead(self, lead: ExtractedLead) -> CoordinatorResult:
        start_time = time.time()
        execution_trace: List[str] = ["coordinator_start"]
        iterations = 0
        verdict: Optional[DealClearanceVerdict] = None
        sequence: Optional[FinalSequence] = None

        # -------------------------------------------------------------------
        # 1. Triage: Supervisor determines initial route
        # -------------------------------------------------------------------
        iterations += 1
        decision = self.supervisor.decide_route(lead)
        execution_trace.append(f"supervisor_decision:{decision.route.value}")

        # Circuit Breaker Check (Rule 22)
        if iterations > self.max_iterations:
            total_latency = round((time.time() - start_time) * 1000, 2)
            return CoordinatorResult(
                lead_company=lead.company_name,
                final_route=decision.route,
                iterations=iterations,
                execution_trace=execution_trace,
                clearance_verdict=None,
                final_sequence=None,
                success=False,
                error_message=f"Circuit Breaker Tripped: Exceeded max iterations ({self.max_iterations})",
                total_latency_ms=total_latency
            )

        # -------------------------------------------------------------------
        # 2. Route Dispatch: Branching Logic
        # -------------------------------------------------------------------
        
        # Branch A: Opt-Out Escalation (Halt immediately)
        if decision.route == RouteDecision.OPT_OUT_ESCALATE:
            execution_trace.append("station:compliance_opt_out_logged")
            total_latency = round((time.time() - start_time) * 1000, 2)
            return CoordinatorResult(
                lead_company=lead.company_name,
                final_route=decision.route,
                iterations=iterations,
                execution_trace=execution_trace,
                clearance_verdict=None,
                final_sequence=None,
                success=True,
                error_message=None,
                total_latency_ms=total_latency
            )

        # Branch B: Deep Audit (Parallel Fan-Out Squad)
        if decision.route == RouteDecision.DEEP_AUDIT:
            execution_trace.append("station:parallel_evaluator_squad")
            verdict = await self.evaluator_squad.evaluate_deal(lead)
            execution_trace.append(f"squad_verdict:{verdict.status.value}")

            # DETERMINISTIC GATE (Rule 22 & Rule 27):
            # Only proceed to drafting if STRICTLY APPROVED.
            if verdict.status != ClearanceStatus.APPROVED:
                execution_trace.append("gate:blocked_by_evaluator_squad")
                total_latency = round((time.time() - start_time) * 1000, 2)
                return CoordinatorResult(
                    lead_company=lead.company_name,
                    final_route=decision.route,
                    iterations=iterations,
                    execution_trace=execution_trace,
                    clearance_verdict=verdict,
                    final_sequence=None,
                    success=False,
                    error_message=f"Clearance rejected or requires review: {verdict.status.value}. Reasons: {verdict.rejection_reasons or verdict.partial_failures}",
                    total_latency_ms=total_latency
                )

        # Branch C: Fast Track or Approved Deep Audit -> Specialist Cadence Generation
        execution_trace.append("station:sequence_strategist")
        strategy = self.strategist.process(lead)

        execution_trace.append("station:copywriter")
        sequence = self.copywriter.process(strategy)
        execution_trace.append("coordinator_complete")

        total_latency = round((time.time() - start_time) * 1000, 2)
        return CoordinatorResult(
            lead_company=lead.company_name,
            final_route=decision.route,
            iterations=iterations,
            execution_trace=execution_trace,
            clearance_verdict=verdict,
            final_sequence=sequence,
            success=True,
            error_message=None,
            total_latency_ms=total_latency
        )


# ===========================================================================
# Controlled Verification Suite (4 Distinct Test Scenarios)
# ===========================================================================
if __name__ == "__main__":
    async def run_supervisor_tests():
        coordinator = SupervisorCoordinator()

        print("\n========================================================")
        print("  TEST 1: Standard Lead -> Fast-Track Route")
        print("========================================================")
        standard_lead = ExtractedLead(
            client_name="Sarah Jenkins",
            company_name="Boutique Living Real Estate",
            deal_size_usd=18000.0,
            core_pain_point="Manual lead chasing across WhatsApp and Gmail",
            deal_tier=DealTier.STANDARD
        )
        res1 = await coordinator.process_lead(standard_lead)
        print(f"Company: {res1.lead_company}")
        print(f"Route: {res1.final_route.value}")
        print(f"Success: {res1.success}")
        print(f"Trace: {res1.execution_trace}")
        print(f"Emails Drafted: {len(res1.final_sequence.emails) if res1.final_sequence else 0}")
        assert res1.final_route == RouteDecision.FAST_TRACK
        assert res1.success is True
        assert res1.final_sequence is not None
        assert "station:parallel_evaluator_squad" not in res1.execution_trace
        print("[PASS] Test 1: Standard lead fast-tracked, bypassed evaluators cleanly!")

        print("\n========================================================")
        print("  TEST 2: Enterprise Lead -> Deep Audit -> Approved")
        print("========================================================")
        enterprise_lead = ExtractedLead(
            client_name="Adam Burns",
            company_name="Advantage Investment UK",
            deal_size_usd=75000.0,
            core_pain_point="Off-plan allocation bottlenecks across Liverpool developments",
            deal_tier=DealTier.ENTERPRISE
        )
        res2 = await coordinator.process_lead(enterprise_lead)
        print(f"Company: {res2.lead_company}")
        print(f"Route: {res2.final_route.value}")
        print(f"Success: {res2.success}")
        print(f"Squad Status: {res2.clearance_verdict.status.value if res2.clearance_verdict else None}")
        print(f"Trace: {res2.execution_trace}")
        print(f"Emails Drafted: {len(res2.final_sequence.emails) if res2.final_sequence else 0}")
        assert res2.final_route == RouteDecision.DEEP_AUDIT
        assert res2.success is True
        assert res2.clearance_verdict.status == ClearanceStatus.APPROVED
        assert res2.final_sequence is not None
        assert "station:parallel_evaluator_squad" in res2.execution_trace
        print("[PASS] Test 2: Enterprise lead cleared by squad and drafted!")

        print("\n========================================================")
        print("  TEST 3: Controlled Gate Halt (High Risk / Infeasible Deal)")
        print("========================================================")
        # Technical Auditor rejects deals when client_name contains 'Infeasible'
        failing_enterprise_lead = ExtractedLead(
            client_name="Dr. Infeasible Legacy",
            company_name="Legacy Systems Group",
            deal_size_usd=120000.0,
            core_pain_point="Require on-premise mainframe sync with COBOL batch runs",
            deal_tier=DealTier.ENTERPRISE
        )
        res3 = await coordinator.process_lead(failing_enterprise_lead)
        print(f"Company: {res3.lead_company}")
        print(f"Route: {res3.final_route.value}")
        print(f"Success: {res3.success}")
        print(f"Gate Triggered: {'gate:blocked_by_evaluator_squad' in res3.execution_trace}")
        print(f"Error Message: {res3.error_message}")
        print(f"Emails Drafted: {res3.final_sequence is not None}")
        assert res3.success is False
        assert res3.final_sequence is None
        assert "gate:blocked_by_evaluator_squad" in res3.execution_trace
        print("[PASS] Test 3: Deterministic gate halted rejected deal; zero emails drafted!")

        print("\n========================================================")
        print("  TEST 4: Immediate Opt-Out Escalation")
        print("========================================================")
        opt_out_lead = ExtractedLead(
            client_name="Angry Prospect",
            company_name="Apex Global",
            deal_size_usd=5000.0,
            core_pain_point="Please stop emailing me and unsubscribe our company",
            deal_tier=DealTier.STANDARD
        )
        res4 = await coordinator.process_lead(opt_out_lead)
        print(f"Company: {res4.lead_company}")
        print(f"Route: {res4.final_route.value}")
        print(f"Trace: {res4.execution_trace}")
        print(f"Emails Drafted: {res4.final_sequence is not None}")
        assert res4.final_route == RouteDecision.OPT_OUT_ESCALATE
        assert res4.success is True
        assert res4.final_sequence is None
        assert "station:compliance_opt_out_logged" in res4.execution_trace
        assert "station:sequence_strategist" not in res4.execution_trace
        print("[PASS] Test 4: Opt-out halted marketing sequence immediately!")

    asyncio.run(run_supervisor_tests())
