"""
test_a2a_resilience.py
======================
Build 5 Verification Suite: End-to-End A2A Remote Specialist Resilience.

Tests verified:
1. Capability Discovery via JSON-RPC 2.0
2. Happy Path Compliance Clearance
3. EU GDPR Boundary Rule Violation
4. Distributed Idempotency (Deduplication Cache)
5. Network Latency Timeout & Fail-Closed Posture
6. Remote Internal Crash & Error Handling
"""

import asyncio
import time
from multi_agent_platform.build5_remote_a2a.remote_compliance_service import RemoteComplianceServer
from multi_agent_platform.build5_remote_a2a.a2a_client import RemoteComplianceClient
from multi_agent_platform.build5_remote_a2a.a2a_contracts import ComplianceAuditStatus


async def run_resilience_test_suite():
    print("\n" + "=" * 80)
    print(">>> STARTING BUILD 5 VERIFICATION SUITE: REMOTE A2A SPECIALIST")
    print("=" * 80)

    server = RemoteComplianceServer(host="127.0.0.1", port=8765)
    await server.start()
    print("[HTTP Server] Remote Compliance Specialist started on http://127.0.0.1:8765/rpc\n")

    client = RemoteComplianceClient(service_url="http://127.0.0.1:8765/rpc", default_timeout=1.0)

    try:
        # -------------------------------------------------------------
        # TEST 1: Agent Capability Discovery
        # -------------------------------------------------------------
        print("--- [TEST 1] A2A Capability Card Discovery ---")
        card = await client.get_capability_card()
        print(f"Discovered Remote Agent: {card.agent_name} (v{card.version})")
        print(f"Supported Capabilities: {card.supported_methods}")
        print(f"Remote SLA Guarantee: {card.sla_timeout_seconds}s")
        assert card.agent_id == "agent_compliance_eu_01"
        assert "audit_lead_compliance" in card.supported_methods
        print("[OK] TEST 1 PASSED: Remote capability successfully discovered.\n")

        # -------------------------------------------------------------
        # TEST 2: Clean Happy-Path Clearance
        # -------------------------------------------------------------
        print("--- [TEST 2] Standard US B2B Lead Clearance ---")
        res_us = await client.audit_lead(
            company_name="Apex Global Analytics",
            country="US",
            explicit_opt_in=False,
            industry="Software Development",
        )
        print(f"Company: {res_us.company_name}")
        print(f"Verdict: {res_us.status.value} (Risk Score: {res_us.risk_score})")
        print(f"Rationale: {res_us.explanation}")
        assert res_us.status == ComplianceAuditStatus.CLEARED
        assert res_us.risk_score == 1
        print("[OK] TEST 2 PASSED: Compliant lead cleared cleanly.\n")

        # -------------------------------------------------------------
        # TEST 3: EU GDPR Strict Opt-In Boundary Enforcement
        # -------------------------------------------------------------
        print("--- [TEST 3] EU Lead Missing Explicit Opt-In (GDPR Breach) ---")
        res_de = await client.audit_lead(
            company_name="Berlin Fintech Ventures",
            country="DE",
            explicit_opt_in=False,
            industry="Finance",
        )
        print(f"Company: {res_de.company_name}")
        print(f"Verdict: {res_de.status.value} (Risk Score: {res_de.risk_score})")
        print(f"Restrictions: {res_de.jurisdiction_restrictions}")
        print(f"Rationale: {res_de.explanation}")
        assert res_de.status == ComplianceAuditStatus.RESTRICTED
        assert res_de.risk_score == 7
        assert not res_de.gdpr_compliant
        print("[OK] TEST 3 PASSED: GDPR restriction correctly identified across network boundary.\n")

        # -------------------------------------------------------------
        # TEST 4: Distributed Idempotency Verification
        # -------------------------------------------------------------
        print("--- [TEST 4] Idempotency Verification (Replay Protection) ---")
        fixed_key = "idemp_lead_realty_corp_999"
        
        t0 = time.time()
        call_1 = await client.audit_lead(
            company_name="Realty Corp UK",
            country="GB",
            explicit_opt_in=True,
            idempotency_key=fixed_key,
        )
        duration_1 = (time.time() - t0) * 1000

        # Second call with the same idempotency key
        t1 = time.time()
        call_2 = await client.audit_lead(
            company_name="Realty Corp UK",
            country="GB",
            explicit_opt_in=True,
            idempotency_key=fixed_key,
        )
        duration_2 = (time.time() - t1) * 1000

        print(f"Call 1 Duration: {duration_1:.2f} ms")
        print(f"Call 2 Duration: {duration_2:.2f} ms")
        assert call_1.status == call_2.status
        assert call_1.company_name == call_2.company_name
        # Verify that the server's cache contains the exact idempotency key
        assert fixed_key in server._idempotency_cache
        print(f"Verified server idempotency cache keys: {list(server._idempotency_cache.keys())}")
        print("[OK] TEST 4 PASSED: Idempotent replay verified in server cache without duplicate side-effects.\n")

        # -------------------------------------------------------------
        # TEST 5: Network Timeout & Fail-Closed Posture
        # -------------------------------------------------------------
        print("--- [TEST 5] Network Timeout & Fail-Closed Posture ---")
        print("Injecting simulated network freeze on remote server (hang 5.0s)...")
        server.simulate_hang = True

        t_start = time.time()
        # Client has default_timeout=0.5s for this test
        res_timeout = await client.audit_lead(
            company_name="Hanging Partner Ltd",
            country="US",
            custom_timeout=0.5,
        )
        elapsed = time.time() - t_start

        print(f"Client Timeout Triggered In: {elapsed:.2f} s")
        print(f"Fallback Verdict: {res_timeout.status.value} (Risk Score: {res_timeout.risk_score})")
        print(f"Explanation: {res_timeout.explanation}")
        
        # Verify the client didn't hang for 5s and defaulted safely to RESTRICTED
        assert elapsed < 2.0
        assert res_timeout.status == ComplianceAuditStatus.RESTRICTED
        assert res_timeout.risk_score == 10
        assert "Network Timeout" in res_timeout.explanation
        print("[OK] TEST 5 PASSED: Client bounded-wait timed out cleanly and failed-closed.\n")
        server.simulate_hang = False

        # -------------------------------------------------------------
        # TEST 6: Remote 500 Crash Handling
        # -------------------------------------------------------------
        print("--- [TEST 6] Remote Internal Server Crash (500) Handling ---")
        print("Injecting unhandled server crash into remote specialist...")
        server.simulate_internal_crash = True

        res_crash = await client.audit_lead(
            company_name="Crash Test Corp",
            country="US",
        )
        print(f"Verdict on Crash: {res_crash.status.value} (Risk Score: {res_crash.risk_score})")
        print(f"Explanation: {res_crash.explanation}")
        assert res_crash.status == ComplianceAuditStatus.RESTRICTED
        assert res_crash.risk_score == 10
        print("[OK] TEST 6 PASSED: Remote server crash encapsulated and contained safely.\n")

    finally:
        await client.close()
        await server.stop()
        print("[HTTP Server] Remote service stopped cleanly.\n")

    print("=" * 80)
    print("[SUCCESS] ALL 6 A2A RESILIENCE TESTS PASSED (EXIT CODE 0)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_resilience_test_suite())
