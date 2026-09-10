# 🏛️ Multi-Agent Systems Engineering (Week 5) — Master Architecture & Knowledge Base

> **Virtual Twin & Autonomous Agent Context**  
> **Workspace:** `c:/Users/Cyril Uzochukwu/Downloads/Lessons/multi_agent_platform/`  
> **Repository:** `https://github.com/Thebeardedambivert/followup-sequence-builder`  
> **Framework:** Microsoft Agent Framework Laboratory (AutoGen 0.4 lineage)  
> **Subject:** Multi-Agent Systems as Distributed Systems (Contracts, Coordination, State Ownership, Failure Domains, Observability).

---

## 🧭 The Core System Invariants

1. **A multi-agent system is a distributed system.** Crossing an agent boundary introduces network latency, partial failures, serialization boundaries, and message delivery uncertainty.
2. **Deep Modules Over Shallow Modules (John Ousterhout):** Specialist agents must have simple, narrow interfaces encapsulating internal prompting/reasoning complexity. They do not know about global workflow topology or global termination conditions.
3. **The Single-Writer Principle (Rule 24):** Parallel agents return isolated, immutable envelopes (`FinancialReport`, `TechnicalReport`, `ComplianceReport`). Zero direct mutation of shared state.
4. **Deterministic Policy Gates (Rule 22):** The LLM proposes probabilistic assessments; pure Python gates deterministically decide whether execution halts or advances. Never trust an LLM to enforce its own safety boundaries.
5. **Fail-Closed Security Posture (Rule 27):** Under partial failure or timeout, the system defaults to `ClearanceStatus.REQUIRES_HUMAN_REVIEW` with `is_auto_cleared=False` (never auto-clearing unverified deals).
6. **Idempotency & Replay Semantics:** Retries across external network boundaries carry deterministic idempotency keys (`idempotency_key = f"lead_{company}_{step}"`) to eliminate duplicate side effects (spammed emails, duplicate billing).

---

## 🏗️ 6-Build Architecture Matrix

```
[Incoming Lead]
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Build 3: SupervisorCoordinator (Triage Doctor & Router)     │
│   ├── OPT_OUT_ESCALATE ──> [Halt & Log Compliance]          │
│   ├── FAST_TRACK       ──> [Build 1: Specialist Cadence]    │
│   └── DEEP_AUDIT       ──> [Build 2: Parallel Squad]        │
│                                  │                          │
│                                  ├── APPROVED ──────────────┘
│                                  └── REJECTED / REVIEW ──> [Halt & Escalate]
└─────────────────────────────────────────────────────────────┘
```

| Build | Component / Module | Production Role | Key Files | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Build 1** | Sequential Specialists | Assembly line processing of clean leads | `contracts.py`, `agents.py`, `pipeline.py` | ✅ **DONE** |
| **Build 2** | Parallel Fan-Out / Fan-In | Concurrent independent audits with timeout bounds | `evaluator_contracts.py`, `evaluators.py`, `parallel_evaluator_squad.py` | ✅ **DONE** |
| **Build 3** | Supervisor Pattern | Dynamic triage, routing, circuit breakers, and deterministic gates | `supervisor_contracts.py`, `supervisor.py` | ✅ **DONE** |
| **Build 4** | Debate & Consensus | Multi-agent critique, cross-examination, and convergence protocol | `debate_contracts.py`, `debate_agents.py`, `debate_protocol.py` | ✅ **DONE & VERIFIED** |
| **Build 5** | Remote A2A Specialist | Crossing network boundaries via explicit JSON/gRPC contracts | `a2a_contracts.py`, `a2a_bridge.py` | ⏳ **ACTIVE NEXT** |
| **Build 6** | Production Follow-Up Engine | Persistent, policy-governed, failure-hardened end-to-end platform | `followup_engine.py`, `db_checkpointer.py` | ⏹️ *Queued* |

---

## 📦 Data Contracts & Boundary Envelopes

### 1. Lead Intake Contracts (`contracts.py`)
* `DealTier(str, Enum)`: `STANDARD`, `MID_MARKET`, `ENTERPRISE`.
* `ExtractedLead(BaseModel)`:
  * `client_name: str`
  * `company_name: str`
  * `deal_size_usd: float`
  * `core_pain_point: str` (Guarded by `reject_lazy_extractions` validator blocking placeholders).
  * `deal_tier: DealTier`
* `CadenceStrategy(BaseModel)`: 3-step cadence metadata, target persona, and hook.
* `FinalSequence(BaseModel)`: Exactly 3 drafted emails (`min_length=3, max_length=3`).

### 2. Parallel Evaluator Contracts (`evaluator_contracts.py`)
* `ClearanceStatus(str, Enum)`: `APPROVED`, `REJECTED`, `REQUIRES_HUMAN_REVIEW`.
* `FinancialReport(BaseModel)`: `risk_score` (1-10), `payment_terms_approved`, `budget_verified`.
* `TechnicalReport(BaseModel)`: `is_feasible`, `estimated_sprint_weeks`, `blockers`.
* `ComplianceReport(BaseModel)`: `gdpr_compliant`, `data_residency_ok`, `nda_signed`.
* `DealClearanceVerdict(BaseModel)`:
  * `status: ClearanceStatus`
  * `is_auto_cleared: bool`
  * `rejection_reasons: List[str]`
  * `partial_failures: List[str]`
  * `financial`, `technical`, `compliance` (Optional report slots)
  * `total_latency_ms: float`

### 3. Supervisor & Coordinator Contracts (`supervisor_contracts.py`)
* `RouteDecision(str, Enum)`: `FAST_TRACK`, `DEEP_AUDIT`, `OPT_OUT_ESCALATE`, `COMPLETE`.
* `SupervisorDecision(BaseModel)`: `route`, `reasoning` (min 10 chars), `requires_human_gate`.
* `CoordinatorResult(BaseModel)`:
  * `lead_company: str`
  * `final_route: RouteDecision`
  * `iterations: int` (bounded 1 to 10)
  * `execution_trace: List[str]` (ordered audit trail)
  * `clearance_verdict: Optional[DealClearanceVerdict]`
  * `final_sequence: Optional[FinalSequence]`
  * `success: bool`
  * `total_latency_ms: float`

### 4. Debate & Consensus Contracts (`debate_contracts.py`)
* `CritiqueSeverity(str, Enum)`: `BLOCKER`, `WARNING`.
* `CritiqueCategory(str, Enum)`: `UNVERIFIED_CLAIM`, `UNREALISTIC_TIMELINE`, `PRICING_MISMATCH`.
* `CritiquePoint(BaseModel)`: `category`, `severity`, `offending_text`, `feedback`, `suggested_fix`.
* `CritiqueReport(BaseModel)`: `round_number`, `is_approved`, `critique_points`, `summary` (Guarded by `reject_approved_with_blockers` validator).
* `DebateDraft(BaseModel)`: `round_number`, `emails` (exactly 3), `revision_notes`.
* `ConsensusVerdict(BaseModel)`:
  * `converged: bool`
  * `total_rounds: int`
  * `final_draft: Optional[DebateDraft]` (Enforces fail-closed: `None` when `converged=False`)
  * `unresolved_blockers: List[str]`
  * `audit_trail: List[str]` (ordered dialectic ledger)

---

## ⚡ Failure Engineering & Defense Guide

* **Loud vs. Silent Failures:**
  * Missing Pydantic fields / bad enum types: **Loud failure** (`ValidationError` at runtime boundary).
  * Bypassing clearance gates: **Silent failure** (script exits 0, green dashboard, but sends bad contracts).
* **Fault Containment:**
  * Evaluators run concurrently with `asyncio.wait_for(coro, timeout=1.5)` and `asyncio.gather(..., return_exceptions=True)`.
  * Partial exceptions do not crash the host harness.
* **Circuit Breakers:**
  * The Supervisor Coordinator enforces `max_iterations = 3`. Loops exceeding this threshold trip deterministically.
  * The Debate Coordinator enforces `max_rounds = 3`. If consensus is not reached, execution halts, prevents runaway token burn, and declares deadlock.
* **Fail-Closed Consensus Posture:**
  * Under non-convergence / circuit-breaker trip, `final_draft` is strictly set to `None`. This physically prevents unverified, toxic marketing claims from leaking into customer send queues.
