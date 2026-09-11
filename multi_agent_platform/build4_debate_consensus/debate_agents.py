"""
debate_agents.py - Proposer and Critic actors for Build 4: Debate & Consensus.
Week 5: Multi-Agent Systems Engineering
"""

from typing import List, Optional
from multi_agent_platform.build1_sequential.contracts import CadenceStrategy, EmailDraft
from multi_agent_platform.build4_debate_consensus.debate_contracts import (
    CritiqueCategory,
    CritiqueSeverity,
    CritiquePoint,
    CritiqueReport,
    DebateDraft,
)


# ---------------------------------------------------------------------------
# Actor 1: The Proposer (Copywriter with Revision Capabilities)
# ---------------------------------------------------------------------------

class DebateCopywriterAgent:
    """
    Drafts initial sales outreach, and revises copy when challenged by the Critic.
    """
    def __init__(self, agent_name: str = "copywriter_proposer"):
        self.agent_name = agent_name

    def draft_initial(self, strategy: CadenceStrategy) -> DebateDraft:
        """
        Round 1: Creates the first draft.
        Deliberately contains an overly-aggressive claim for testing debate convergence!
        """
        emails = [
            EmailDraft(
                day=1,
                subject=f"Accelerating {strategy.company_name}'s Delivery",
                body=(
                    f"Hi team, {strategy.day_1_angle}. "
                    "We can guarantee 100% zero downtime from Day 1 with our turnkey solution."
                )
            ),
            EmailDraft(
                day=3,
                subject="Case Study & Proof of Execution",
                body=f"Sharing relevant work: {strategy.day_3_case_study}. We are ready to deploy."
            ),
            EmailDraft(
                day=7,
                subject="Final Touchpoint on Allocation",
                body=f"Quick check-in: {strategy.day_7_urgency_trigger}. Let us know your thoughts."
            )
        ]
        return DebateDraft(
            round_number=1,
            emails=emails,
            revision_notes="Initial baseline draft generated from cadence strategy."
        )

    def revise(self, previous_draft: DebateDraft, critique: CritiqueReport) -> DebateDraft:
        """
        Round 2+: Reads the critique points, removes the offending phrases,
        and outputs a sanitized revision.
        """
        new_round = previous_draft.round_number + 1
        revised_emails: List[EmailDraft] = []
        applied_fixes: List[str] = []

        for email in previous_draft.emails:
            current_body = email.body
            for point in critique.critique_points:
                if point.offending_text in current_body:
                    # Sanitize by replacing the risky claim with the suggested fix
                    current_body = current_body.replace(point.offending_text, point.suggested_fix)
                    applied_fixes.append(f"Replaced '{point.offending_text}' with '{point.suggested_fix}'")

            revised_emails.append(EmailDraft(day=email.day, subject=email.subject, body=current_body))

        return DebateDraft(
            round_number=new_round,
            emails=revised_emails,
            revision_notes="; ".join(applied_fixes) if applied_fixes else "No changes required."
        )


# ---------------------------------------------------------------------------
# Actor 2: The Challenger (Risk & Compliance Critic)
# ---------------------------------------------------------------------------

class RiskAndComplianceCriticAgent:
    """
    Audits outreach copy against strict corporate policy, truth in advertising,
    and technical feasibility bounds.
    """
    def __init__(self, agent_name: str = "compliance_critic"):
        self.agent_name = agent_name

    def evaluate_draft(self, draft: DebateDraft) -> CritiqueReport:
        """
        Audits all emails in the draft. Emits structured critique points.
        """
        critique_points: List[CritiquePoint] = []

        for email in draft.emails:
            body = email.body

            # Check 1: Unverified uptime claims
            if "100% zero downtime" in body:
                critique_points.append(
                    CritiquePoint(
                        category=CritiqueCategory.UNVERIFIED_CLAIM,
                        severity=CritiqueSeverity.BLOCKER,
                        offending_text="guarantee 100% zero downtime",
                        feedback="SLA contractually guarantees 99.9% uptime, not 100%. Exposes company to breach of contract.",
                        suggested_fix="deliver industry-standard 99.9% high availability"
                    )
                )

            # Check 2: Unrealistic rush promises
            if "in 1 week" in body.lower():
                critique_points.append(
                    CritiquePoint(
                        category=CritiqueCategory.UNREALISTIC_TIMELINE,
                        severity=CritiqueSeverity.BLOCKER,
                        offending_text="in 1 week",
                        feedback="Technical audit requires minimum 2 to 4 sprint weeks.",
                        suggested_fix="within 2 to 4 weeks"
                    )
                )

        # Deterministic consensus rule
        has_blocker = any(p.severity == CritiqueSeverity.BLOCKER for p in critique_points)
        is_approved = not has_blocker

        summary = (
            "Draft fully compliant with legal and architecture standards."
            if is_approved
            else f"Draft rejected with {len(critique_points)} blocker(s). Revisions required."
        )

        return CritiqueReport(
            round_number=draft.round_number,
            is_approved=is_approved,
            critique_points=critique_points,
            summary=summary
        )


# ---------------------------------------------------------------------------
# VERIFICATION BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from multi_agent_platform.build1_sequential.contracts import DealTier

    strat = CadenceStrategy(
        company_name="Cyberdyne Systems",
        deal_tier=DealTier.ENTERPRISE,
        day_1_angle="Operational telemetry audit",
        day_3_case_study="Whitepaper on real-time streaming",
        day_7_urgency_trigger="14-day sandboxed pilot"
    )

    copywriter = DebateCopywriterAgent()
    critic = RiskAndComplianceCriticAgent()

    # Round 1: Initial draft
    d1 = copywriter.draft_initial(strat)
    r1 = critic.evaluate_draft(d1)
    print(f"Round 1 Approved: {r1.is_approved} | Blockers: {len(r1.critique_points)}")

    # Round 2: Revision
    d2 = copywriter.revise(d1, r1)
    r2 = critic.evaluate_draft(d2)
    print(f"Round 2 Approved: {r2.is_approved} | Blockers: {len(r2.critique_points)}")
    print("Revision Notes Applied:", d2.revision_notes)

    assert r1.is_approved is False
    assert r2.is_approved is True
    print("\n[OK] Both debate agents verified in 2-round convergence test!")
