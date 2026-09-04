"""
evaluators.py - Independent Asynchronous Evaluators for Build 2.
Week 5: Multi-Agent Systems Engineering
"""

import asyncio
from contracts import ExtractedLead, DealTier
from evaluator_contracts import FinancialReport, TechnicalReport, ComplianceReport


# ---------------------------------------------------------------------------
# Inspector 1: Financial Auditor Agent (The CFO)
# ---------------------------------------------------------------------------
class FinancialAuditorAgent:
    """
    Audits deal economics, creditworthiness, and contract payment terms.
    """
    def __init__(self, agent_name: str = "cfo_auditor"):
        self.agent_name = agent_name

    async def evaluate(self, lead: ExtractedLead) -> FinancialReport:
        # Simulate network latency / LLM evaluation time
        await asyncio.sleep(0.4)

        if lead.deal_size_usd > 100000.0:
            # High-value enterprise account
            return FinancialReport(
                evaluator_name=self.agent_name,
                risk_score=3,
                payment_terms_approved=True,
                budget_verified=True,
                flags=["Requires escrow for deal size over $100k"]
            )
        elif lead.deal_size_usd == 0.0:
            # Suspicious zero-budget lead
            return FinancialReport(
                evaluator_name=self.agent_name,
                risk_score=9,
                payment_terms_approved=False,
                budget_verified=False,
                flags=["Zero budget allocated in transcript"]
            )
        else:
            # Healthy standard tier
            return FinancialReport(
                evaluator_name=self.agent_name,
                risk_score=2,
                payment_terms_approved=True,
                budget_verified=True,
                flags=[]
            )


# ---------------------------------------------------------------------------
# Inspector 2: Technical Architect Agent (The Chief Architect)
# ---------------------------------------------------------------------------
class TechnicalAuditorAgent:
    """
    Audits implementation complexity, API limitations, and infrastructure scope.
    """
    def __init__(self, agent_name: str = "tech_architect"):
        self.agent_name = agent_name

    async def evaluate(self, lead: ExtractedLead) -> TechnicalReport:
        # Simulate network latency / LLM evaluation time
        await asyncio.sleep(0.4)

        lowered_pain = lead.core_pain_point.lower()
        if "telemetry" in lowered_pain or "robot" in lowered_pain:
            return TechnicalReport(
                evaluator_name=self.agent_name,
                is_feasible=True,
                estimated_sprint_weeks=4,
                infrastructure_requirements=["High-throughput WebSocket Gateway", "TimescaleDB Cluster"]
            )
        else:
            return TechnicalReport(
                evaluator_name=self.agent_name,
                is_feasible=True,
                estimated_sprint_weeks=2,
                infrastructure_requirements=["Land Registry Webhook Bridge", "PDF Generation Worker"]
            )


# ---------------------------------------------------------------------------
# Inspector 3: Legal & Compliance Counsel Agent (The General Counsel)
# ---------------------------------------------------------------------------
class ComplianceAuditorAgent:
    """
    Audits GDPR compliance, regional data sovereignty, and security frameworks.
    Has a configurable delay to allow controlled failure testing.
    """
    def __init__(self, agent_name: str = "general_counsel", simulated_delay: float = 0.4):
        self.agent_name = agent_name
        self.simulated_delay = simulated_delay

    async def evaluate(self, lead: ExtractedLead) -> ComplianceReport:
        # Await simulated thinking or hanging delay
        await asyncio.sleep(self.simulated_delay)

        # UK and Enterprise accounts require strict GDPR review
        return ComplianceReport(
            evaluator_name=self.agent_name,
            gdpr_compliant=True,
            data_residency_ok=True,
            risk_level="LOW"
        )


if __name__ == "__main__":
    import time

    async def main():
        sample_lead = ExtractedLead(
            client_name="Adam Burns",
            company_name="Advantage Investment",
            deal_size_usd=45000.0,
            core_pain_point="Manual deal packaging delays off-plan allocation in Liverpool",
            deal_tier=DealTier.STANDARD
        )

        cfo = FinancialAuditorAgent()
        architect = TechnicalAuditorAgent()
        counsel = ComplianceAuditorAgent(simulated_delay=0.4)

        print("Running all 3 evaluators CONCURRENTLY via asyncio.gather...")
        t0 = time.time()
        
        # 🚀 THE PARALLEL FAN-OUT:
        fin_report, tech_report, comp_report = await asyncio.gather(
            cfo.evaluate(sample_lead),
            architect.evaluate(sample_lead),
            counsel.evaluate(sample_lead)
        )
        
        elapsed = round((time.time() - t0), 2)
        print(f"Done in {elapsed}s! (Sequential would have taken ~1.2s)")
        print("- Financial Risk Score:", fin_report.risk_score)
        print("- Tech Feasible:", tech_report.is_feasible, "| Sprints:", tech_report.estimated_sprint_weeks)
        print("- GDPR Compliant:", comp_report.gdpr_compliant)
        assert elapsed < 0.7, "Concurrency failure: total time took as long as sequential!"
        print("[OK] evaluators.py concurrency verified!")

    asyncio.run(main())
