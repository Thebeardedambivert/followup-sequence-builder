# 🤖 Multi-Agent Follow-Up & Debate Platform

> **Production Distributed Multi-Agent Systems Engineering**  
> *Built as part of the Microsoft Agent Framework Advanced Systems Laboratory.*  
> **Author:** Cyril Nwachukwu ([@Thebeardedambivert](https://github.com/Thebeardedambivert))  
> **Repository:** [https://github.com/Thebeardedambivert/followup-sequence-builder](https://github.com/Thebeardedambivert/followup-sequence-builder)

---

## 🏛️ Executive Architectural Overview

This platform is an enterprise-grade multi-agent operations platform that processes incoming sales leads, executes parallel financial/technical feasibility audits, conducts adversarial dialectic debates on marketing copy, and dispatches remote regulatory compliance audits across network boundaries.

Rather than treating multi-agent workflows as black-box prompt chains, this repository treats **multi-agent systems as distributed systems**: enforcing typed boundary contracts, single-writer state isolation, deterministic iteration ceilings (circuit breakers), network idempotency keys, and fail-closed security postures.

```
                                [ Incoming Raw Lead ]
                                          │
                                          ▼
                               ┌────────────────────┐
                               │   Lead Extractor   │ (Build 1: Boundary Guard)
                               └──────────┬─────────┘
                                          │
                                          ▼
                               ┌────────────────────┐
                               │  Lead Supervisor   │ (Build 3: Dynamic Triage)
                               └──────────┬─────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │                             │                             │
   [OPT_OUT_ESCALATE]                [FAST_TRACK]                  [DEEP_AUDIT]
            │                             │                             │
     Compliance DLQ                       │                 ┌───────────┴───────────┐
     0 emails drafted                     │                 ▼                       ▼
                                          │         [In-Process Squad]      [Remote A2A Specialist]
                                          │         CFO + Architect         GDPR Compliance Officer
                                          │         (Build 2: Parallel)     (Build 5: HTTP/JSON-RPC)
                                          │                 │                       │
                                          │                 └───────────┬───────────┘
                                          │                             │
                                          │                    Deterministic Gate:
                                          │                    Is Lead Approved?
                                          │                   /                 \
                                          │                 YES                  NO
                                          │                  │                    │
                                          └─────────────────►│            [Halt Execution]
                                                             ▼            Log Rejection & Telemetry
                                                   ┌───────────────────┐
                                                   │ SequenceStrategist│ (Build 1)
                                                   └─────────┬─────────┘
                                                             │
                                                             ▼
                                                   ┌───────────────────┐
                                                   │ Debate & Consensus│ (Build 4: Adversarial Audit)
                                                   │ Proposer vs Critic│
                                                   └─────────┬─────────┘
                                                             │
                                                             ▼
                                                   [ Final Clearance ]
                                                   Verified 3-Step Sequence
                                                   + Flight Recorder Ledger
```

---

## 🚀 The 6 Distributed Builds

| Build | Core Pattern | Key Modules | Hard Distributed Invariants |
| :--- | :--- | :--- | :--- |
| **Build 1** | **Sequential Specialists** | `contracts.py`<br>`agents.py`<br>`pipeline.py` | Typed boundary envelopes (`ExtractedLead`, `CadenceStrategy`, `FinalSequence`); deterministic boundary guards (`reject_lazy_extractions`); per-station latency telemetry. |
| **Build 2** | **Parallel Fan-Out / Fan-In** | `evaluator_contracts.py`<br>`evaluators.py`<br>`parallel_evaluator_squad.py` | Single-writer principle (no shared mutable memory); concurrency speedup (409 ms parallel vs 1,200 ms sequential); bounded-wait timeout sensors (`asyncio.wait_for`); partial-failure fault containment. |
| **Build 3** | **The Supervisor Pattern** | `supervisor_contracts.py`<br>`supervisor.py` | Dynamic triage doctor (`FAST_TRACK`, `DEEP_AUDIT`, `OPT_OUT_ESCALATE`); pure-Python iteration ceiling; deterministic clearance gate preventing silent business logic bypass. |
| **Build 4** | **Debate & Consensus** | `debate_contracts.py`<br>`debate_agents.py`<br>`debate_protocol.py` | Adversarial cross-agent audit; dialectic convergence loop; targeted delta patching (eliminating stochastic regression); fail-closed termination (`final_draft = None` on circuit trip). |
| **Build 5** | **Remote A2A Specialist** | `a2a_contracts.py`<br>`remote_compliance_service.py`<br>`a2a_client.py`<br>`test_a2a_resilience.py` | Crossing network boundaries via JSON-RPC 2.0; Agent Capability Discovery (`AgentCapabilityCard`); distributed idempotency caching (**2 ms** replay vs 203 ms execution); fail-closed SLA timeout containment. |
| **Build 6** | **Production Follow-Up Engine** | *Active Resumption Point* | End-to-end multi-agent orchestration integrating all 5 patterns into an enterprise hardened system. |

---

## 🛡️ Core Engineering Invariants (Zero Toy Code)

### 1. The Single-Writer Principle (Rule 24)
Parallel worker agents have **zero write access** to global shared memory. Specialists emit read-only, immutable Pydantic envelopes. State mutation is restricted to a single downstream aggregator/reducer, eliminating **Last-Write-Wins (LWW)** race conditions.

### 2. Fail-Closed Security Posture (Rule 27)
Enterprise autonomous systems must **never fail-open**. 
* If parallel legal auditors time out, the clearance status deterministically defaults to `REQUIRES_HUMAN_REVIEW` with `is_auto_cleared = False`.
* If a remote compliance service hangs or crashes, the A2A proxy returns `status = RESTRICTED` with `risk_score = 10`.
* If an adversarial debate exceeds its iteration ceiling without unanimous consensus, `final_draft = None` is returned, preventing automated dispatchers from leaking dangerous unvetted promises.

### 3. Distributed Idempotency & The Unknown-Success Dilemma
In distributed networks, an HTTP timeout indicates an **UNKNOWN** state, not a failure. Every request carries a deterministic `idempotency_key`. The remote service verifies its in-memory ledger before execution: if already processed, it re-emits the cached verdict in **2.02 ms**, eliminating duplicate LLM token expenses and preventing duplicate database side effects.

### 4. Deep Modules & Information Hiding (John Ousterhout)
Specialist agents (`Copywriter`, `Auditor`, `Critic`) are pure deep modules:
* Narrow, simple interfaces accepting typed inputs and returning typed outputs.
* Specialists are completely blind to workflow iteration counters, SLA budgets, and global routing topologies.
* The Coordinator alone owns **Policy**; the Specialist alone owns **Mechanism**.

---

## 📁 Repository Structure

```
followup-sequence-builder/
├── README.md                          # Comprehensive Architecture & Operations Guide
├── requirements.txt                   # Pinned production dependencies
├── schemas.py                         # SQLite session persistence models
├── session_store.py                   # Durable thread state management
└── multi_agent_platform/              # Core Multi-Agent Distributed Engine
    ├── __init__.py                    # Package initialization
    ├── MASTER_ARCHITECTURE.md         # In-depth architectural notes & lineage
    │
    ├── build1_sequential/             # Build 1: Sequential Specialists
    │   ├── __init__.py
    │   ├── contracts.py               # Typed boundary envelopes
    │   ├── agents.py                  # LeadExtractor, SequenceStrategist, Copywriter
    │   └── pipeline.py                # Pipeline runner & telemetry
    │
    ├── build2_parallel_evaluators/    # Build 2: Parallel Fan-Out / Fan-In
    │   ├── __init__.py
    │   ├── evaluator_contracts.py     # Evaluation reports & ClearanceVerdict
    │   ├── evaluators.py              # CFO, Architect, Legal evaluators
    │   └── parallel_evaluator_squad.py# Fan-out / Fan-in aggregator & timeout sensors
    │
    ├── build3_supervisor/             # Build 3: Supervisor Pattern
    │   ├── __init__.py
    │   ├── supervisor_contracts.py    # Routing decisions & coordinator result
    │   └── supervisor.py              # Triage doctor & host engine
    │
    ├── build4_debate_consensus/       # Build 4: Debate & Consensus Protocol
    │   ├── __init__.py
    │   ├── debate_contracts.py        # Critique points & ConsensusVerdict
    │   ├── debate_agents.py           # DebateCopywriter & ComplianceCritic
    │   └── debate_protocol.py         # Dialectic convergence coordinator
    │
    └── build5_remote_a2a/             # Build 5: Remote A2A Specialist
        ├── __init__.py
        ├── a2a_contracts.py           # JSON-RPC 2.0 & Capability envelopes
        ├── remote_compliance_service.py # Standalone HTTP A2A specialist & idempotency cache
        ├── a2a_client.py              # Resilient client proxy & fail-closed containment
        └── test_a2a_resilience.py     # End-to-end resilience verification suite
```

---

## ⚡ How to Run Verification Test Suites

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Build 1: Sequential Specialist Pipeline
```bash
python -m multi_agent_platform.build1_sequential.pipeline
```

### 3. Run Build 2: Parallel Fan-Out / Fan-In Squad
```bash
python -m multi_agent_platform.build2_parallel_evaluators.parallel_evaluator_squad
```

### 4. Run Build 3: Supervisor Pattern (Dynamic Triage)
```bash
python -m multi_agent_platform.build3_supervisor.supervisor
```

### 5. Run Build 4: Debate & Consensus Protocol
```bash
python -m multi_agent_platform.build4_debate_consensus.debate_protocol
```

### 6. Run Build 5: Remote A2A Specialist & Idempotency Resilience
```bash
python -m multi_agent_platform.build5_remote_a2a.test_a2a_resilience
```

---

## 📜 License
MIT License. Authored by Cyril Nwachukwu.
