"""
debate_protocol.py - Autonomous Coordinator for Build 4: Debate & Consensus.
Week 5: Multi-Agent Systems Engineering
"""

from typing import List, Optional
from multi_agent_platform.build1_sequential.contracts import CadenceStrategy
from multi_agent_platform.build4_debate_consensus.debate_contracts import (
    CritiqueSeverity,
    CritiqueReport,
    DebateDraft,
    ConsensusVerdict,
)
from multi_agent_platform.build4_debate_consensus.debate_agents import DebateCopywriterAgent, RiskAndComplianceCriticAgent


class DebateProtocolCoordinator:
    """
    Coordinates the dialectic debate loop between Proposer and Critic.
    Enforces the iteration ceiling, captures the audit trail,
    and returns an immutable ConsensusVerdict.
    """
    def __init__(
        self,
        copywriter: DebateCopywriterAgent,
        critic: RiskAndComplianceCriticAgent,
        max_rounds: int = 3
    ):
        self.copywriter = copywriter
        self.critic = critic
        self.max_rounds = max_rounds

    def run_debate(self, strategy: CadenceStrategy) -> ConsensusVerdict:
        """
        Executes the debate rounds until convergence or circuit breaker ceiling.
        """
        audit_trail: List[str] = []
        
        # -------------------------------------------------------------------
        # Round 1: Baseline Genesis
        # -------------------------------------------------------------------
        current_round = 1
        audit_trail.append(f"Round {current_round}: Initiating baseline draft from cadence strategy.")
        
        current_draft = self.copywriter.draft_initial(strategy)
        current_critique = self.critic.evaluate_draft(current_draft)
        
        audit_trail.append(
            f"Round {current_round} Audit: Approved={current_critique.is_approved}, "
            f"Blockers={len([p for p in current_critique.critique_points if p.severity == CritiqueSeverity.BLOCKER])}."
        )

        # -------------------------------------------------------------------
        # Dialectic Loop (Rounds 2 .. max_rounds)
        # -------------------------------------------------------------------
        while not current_critique.is_approved and current_round < self.max_rounds:
            current_round += 1
            audit_trail.append(f"Round {current_round}: Copywriter revising draft against critic blockers.")
            
            # Revision step
            current_draft = self.copywriter.revise(current_draft, current_critique)
            audit_trail.append(f"Round {current_round} Fixes Applied: {current_draft.revision_notes}")
            
            # Re-evaluation step
            current_critique = self.critic.evaluate_draft(current_draft)
            blocker_count = len([p for p in current_critique.critique_points if p.severity == CritiqueSeverity.BLOCKER])
            audit_trail.append(f"Round {current_round} Audit: Approved={current_critique.is_approved}, Blockers={blocker_count}.")

        # -------------------------------------------------------------------
        # Resolution & Convergence Gate
        # -------------------------------------------------------------------
        if current_critique.is_approved:
            audit_trail.append(f"Consensus achieved successfully on Round {current_round}.")
            return ConsensusVerdict(
                converged=True,
                total_rounds=current_round,
                final_draft=current_draft,
                unresolved_blockers=[],
                audit_trail=audit_trail
            )
        else:
            # Circuit breaker tripped: Unresolved blockers remain
            blockers = [p.feedback for p in current_critique.critique_points if p.severity == CritiqueSeverity.BLOCKER]
            audit_trail.append(f"Circuit breaker tripped at max rounds ({self.max_rounds}). Deadlock declared.")
            return ConsensusVerdict(
                converged=False,
                total_rounds=current_round,
                final_draft=None,  # Fail closed: Do not release unapproved content
                unresolved_blockers=blockers,
                audit_trail=audit_trail
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

    print("=== TEST 1: Standard Debate Loop (Convergence in 2 Rounds) ===")
    coordinator = DebateProtocolCoordinator(copywriter=copywriter, critic=critic, max_rounds=3)
    verdict = coordinator.run_debate(strat)

    print(f"Converged: {verdict.converged}")
    print(f"Total Rounds: {verdict.total_rounds}")
    print("Audit Trail:")
    for step in verdict.audit_trail:
        print(f"  • {step}")

    assert verdict.converged is True
    assert verdict.total_rounds == 2
    assert verdict.final_draft is not None
    assert "99.9% high availability" in verdict.final_draft.emails[0].body
    print("[OK] Test 1 Passed: Dialectic convergence verified!\n")

    print("=== TEST 2: Circuit Breaker Safety (Forced Max Rounds = 1) ===")
    strict_coordinator = DebateProtocolCoordinator(copywriter=copywriter, critic=critic, max_rounds=1)
    fail_verdict = strict_coordinator.run_debate(strat)

    print(f"Converged: {fail_verdict.converged}")
    print(f"Total Rounds: {fail_verdict.total_rounds}")
    print(f"Final Draft is None: {fail_verdict.final_draft is None}")
    print(f"Unresolved Blockers: {fail_verdict.unresolved_blockers}")

    assert fail_verdict.converged is False
    assert fail_verdict.final_draft is None  # Proves fail-closed safety!
    print("[OK] Test 2 Passed: Circuit breaker and fail-closed security verified!")
