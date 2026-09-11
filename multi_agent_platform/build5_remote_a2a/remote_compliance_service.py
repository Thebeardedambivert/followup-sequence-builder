"""
remote_compliance_service.py
============================
Build 5: Standalone Remote Compliance Specialist Service.

This service acts as an independent A2A agent exposing its capabilities over HTTP
using JSON-RPC 2.0 envelopes.

Invariants Implemented:
1. Idempotency Gate: Caches responses by idempotency_key to prevent duplicate executions.
2. Capability Discovery: Serves an AgentCapabilityCard describing its SLA and methods.
3. Bounded Processing: Evaluates compliance deterministically and rejects invalid parameters.
4. Simulates Network Latency & Fault Injection for resilient testing.
"""

import asyncio
from typing import Dict, Any, Optional
from aiohttp import web

from multi_agent_platform.build5_remote_a2a.a2a_contracts import (
    JsonRpcRequest,
    JsonRpcResponse,
    JsonRpcError,
    JsonRpcErrorCode,
    AgentCapabilityCard,
    ComplianceAuditResult,
    ComplianceAuditStatus,
)


class RemoteComplianceSpecialist:
    """The domain intelligence for legal & GDPR compliance auditing."""

    def __init__(self):
        self.capability_card = AgentCapabilityCard(
            agent_id="agent_compliance_eu_01",
            agent_name="Regulatory & GDPR Compliance Specialist",
            version="1.0.0",
            description="Performs jurisdiction, GDPR, and trade restriction compliance audits on outbound lead campaigns.",
            supported_methods=["get_capability_card", "audit_lead_compliance"],
            sla_timeout_seconds=2.0,
        )

    async def audit_lead(self, params: Dict[str, Any]) -> ComplianceAuditResult:
        """
        Audits a lead based on company name, country, and outreach opt-in status.
        Simulates realistic processing latency (e.g. 200ms).
        """
        company_name = params.get("company_name", "Unknown Corp")
        country = params.get("country", "US").upper()
        explicit_opt_in = params.get("explicit_opt_in", False)
        industry = params.get("industry", "Technology").lower()

        # Simulate micro-deliberation latency
        await asyncio.sleep(0.2)

        # Invariant 1: Prohibited Sanctioned/High-Risk Jurisdictions
        sanctioned_regions = ["IRAN", "NORTH KOREA", "SYRIA", "CUBA"]
        if country in sanctioned_regions:
            return ComplianceAuditResult(
                company_name=company_name,
                status=ComplianceAuditStatus.PROHIBITED,
                risk_score=10,
                gdpr_compliant=False,
                jurisdiction_restrictions=[country],
                explanation=f"Outreach to {country} is strictly prohibited under international sanctions.",
            )

        # Invariant 2: EU GDPR Rules (Strict opt-in required for certain domains)
        eu_countries = ["DE", "FR", "NL", "IE", "ES", "IT", "SE"]
        if country in eu_countries and not explicit_opt_in:
            return ComplianceAuditResult(
                company_name=company_name,
                status=ComplianceAuditStatus.RESTRICTED,
                risk_score=7,
                gdpr_compliant=False,
                jurisdiction_restrictions=[country],
                explanation=f"GDPR Article 6 violation: B2B outreach in {country} requires verified legitimate interest or opt-in evidence.",
            )

        # Invariant 3: High-Risk Industries (Gambling / Crypto / High Leverage)
        if "crypto" in industry or "gambling" in industry:
            return ComplianceAuditResult(
                company_name=company_name,
                status=ComplianceAuditStatus.RESTRICTED,
                risk_score=6,
                gdpr_compliant=True,
                jurisdiction_restrictions=[],
                explanation=f"High-risk industry category ({industry}) requires manual compliance officer sign-off before campaign dispatch.",
            )

        # Clean Clearance Path
        return ComplianceAuditResult(
            company_name=company_name,
            status=ComplianceAuditStatus.CLEARED,
            risk_score=1,
            gdpr_compliant=True,
            jurisdiction_restrictions=[],
            explanation="Lead satisfies standard B2B legitimate interest requirements with low compliance risk.",
        )


class RemoteComplianceServer:
    """
    HTTP Server wrapping the RemoteComplianceSpecialist with JSON-RPC 2.0 handling.
    Maintains an in-memory Idempotency Cache.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.specialist = RemoteComplianceSpecialist()
        # Idempotency Cache: Maps idempotency_key -> JsonRpcResponse dict
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}
        # Fault injection controls
        self.simulate_hang: bool = False
        self.simulate_internal_crash: bool = False

        self.app = web.Application()
        self.app.router.add_post("/rpc", self.handle_rpc)
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None

    async def handle_rpc(self, request: web.Request) -> web.Response:
        """Core JSON-RPC 2.0 dispatcher with Idempotency verification."""
        try:
            raw_body = await request.json()
        except Exception:
            err_resp = JsonRpcResponse(
                id="null",
                error=JsonRpcError(
                    code=JsonRpcErrorCode.PARSE_ERROR.value,
                    message="Parse error: Invalid JSON received.",
                ),
            )
            return web.json_response(err_resp.model_dump(), status=400)

        # Validate incoming request envelope
        try:
            rpc_req = JsonRpcRequest(**raw_body)
        except Exception as ve:
            err_resp = JsonRpcResponse(
                id=str(raw_body.get("id", "null")),
                error=JsonRpcError(
                    code=JsonRpcErrorCode.INVALID_REQUEST.value,
                    message=f"Invalid Request: {str(ve)}",
                ),
            )
            return web.json_response(err_resp.model_dump(), status=400)

        # 1. Idempotency Check: Did we already process this exact request?
        if rpc_req.idempotency_key in self._idempotency_cache:
            # Replay cached response without re-executing logic or side-effects!
            cached_data = dict(self._idempotency_cache[rpc_req.idempotency_key])
            # Override response ID to match current request ticket
            cached_data["id"] = rpc_req.id
            resp = web.json_response(cached_data, status=200)
            resp.headers["X-Idempotency-Status"] = "HIT"
            return resp

        # Fault Injection: Simulating an unresponsive hanging server (network timeout)
        if self.simulate_hang:
            await asyncio.sleep(5.0)

        # Fault Injection: Simulating unhandled 500 internal server crash
        if self.simulate_internal_crash:
            err_resp = JsonRpcResponse(
                id=rpc_req.id,
                error=JsonRpcError(
                    code=JsonRpcErrorCode.INTERNAL_ERROR.value,
                    message="Internal Error: Specialist process encountered an unhandled exception.",
                ),
            )
            return web.json_response(err_resp.model_dump(), status=500)

        # 2. Method Dispatcher
        if rpc_req.method == "get_capability_card":
            result_payload = self.specialist.capability_card.model_dump()
            resp = JsonRpcResponse(id=rpc_req.id, result=result_payload)
            self._idempotency_cache[rpc_req.idempotency_key] = resp.model_dump()
            return web.json_response(resp.model_dump(), status=200)

        elif rpc_req.method == "audit_lead_compliance":
            try:
                audit_result = await self.specialist.audit_lead(rpc_req.params)
                resp = JsonRpcResponse(id=rpc_req.id, result=audit_result.model_dump())
                self._idempotency_cache[rpc_req.idempotency_key] = resp.model_dump()
                return web.json_response(resp.model_dump(), status=200)
            except Exception as e:
                err_resp = JsonRpcResponse(
                    id=rpc_req.id,
                    error=JsonRpcError(
                        code=JsonRpcErrorCode.INTERNAL_ERROR.value,
                        message=f"Internal audit processing failure: {str(e)}",
                    ),
                )
                return web.json_response(err_resp.model_dump(), status=500)

        else:
            # Method Not Found
            err_resp = JsonRpcResponse(
                id=rpc_req.id,
                error=JsonRpcError(
                    code=JsonRpcErrorCode.METHOD_NOT_FOUND.value,
                    message=f"Method '{rpc_req.method}' not supported by this agent.",
                ),
            )
            return web.json_response(err_resp.model_dump(), status=404)

    async def start(self):
        """Starts the local HTTP server in the running async event loop."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()

    async def stop(self):
        """Shuts down the HTTP server cleanly."""
        if self._runner:
            await self._runner.cleanup()
