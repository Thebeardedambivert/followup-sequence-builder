"""
a2a_client.py
=============
Build 5: Resilient Local A2A Client Proxy.

This client encapsulates all remote communication across network boundaries:
1. Translates local calls into JSON-RPC 2.0 requests.
2. Attaches deterministic idempotency keys.
3. Implements bounded-wait timeouts (SLA enforcement).
4. Handles network partitions, timeouts, and 500 errors gracefully with fail-closed security.
"""

import uuid
import asyncio
import httpx
from typing import Dict, Any, Optional

from multi_agent_platform.a2a_contracts import (
    JsonRpcRequest,
    JsonRpcResponse,
    AgentCapabilityCard,
    ComplianceAuditResult,
    ComplianceAuditStatus,
)


class RemoteAgentException(Exception):
    """Raised when the remote agent explicitly returns a JSON-RPC error payload."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Remote Agent Error [{code}]: {message}")


class RemoteComplianceClient:
    """
    Client proxy for communicating with the Remote Compliance Specialist.
    Adheres to the Deep Module principle: narrow, clean interface hiding network mechanics.
    """

    def __init__(self, service_url: str = "http://127.0.0.1:8765/rpc", default_timeout: float = 1.5):
        self.service_url = service_url
        self.default_timeout = default_timeout
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Reuses connection pool across requests."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient()
        return self._http_client

    async def close(self):
        """Closes the underlying HTTP client session cleanly."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_capability_card(self) -> AgentCapabilityCard:
        """Discovers capabilities, methods, and SLA expectations from the remote agent."""
        req_id = f"disc_{uuid.uuid4().hex[:8]}"
        request_envelope = JsonRpcRequest(
            id=req_id,
            idempotency_key=f"idemp_{req_id}",
            method="get_capability_card",
            params={},
        )

        raw_response = await self._dispatch_rpc(request_envelope, timeout=self.default_timeout)
        if raw_response.error:
            raise RemoteAgentException(raw_response.error.code, raw_response.error.message)

        return AgentCapabilityCard(**raw_response.result)

    async def audit_lead(
        self,
        company_name: str,
        country: str,
        explicit_opt_in: bool = False,
        industry: str = "technology",
        idempotency_key: Optional[str] = None,
        custom_timeout: Optional[float] = None,
    ) -> ComplianceAuditResult:
        """
        Submits a lead for remote compliance auditing across the network boundary.
        
        Fail-Closed Invariant:
        If the network drops, times out, or the server crashes, this method does NOT crash
        the caller. Instead, it deterministically returns a RESTRICTED audit with risk_score=10.
        """
        req_id = f"audit_{uuid.uuid4().hex[:8]}"
        key = idempotency_key or f"audit_key_{company_name.lower().replace(' ', '_')}"

        request_envelope = JsonRpcRequest(
            id=req_id,
            idempotency_key=key,
            method="audit_lead_compliance",
            params={
                "company_name": company_name,
                "country": country,
                "explicit_opt_in": explicit_opt_in,
                "industry": industry,
            },
        )

        timeout = custom_timeout or self.default_timeout

        try:
            raw_response = await self._dispatch_rpc(request_envelope, timeout=timeout)
            
            if raw_response.error:
                # The remote agent answered, but rejected with an error
                return ComplianceAuditResult(
                    company_name=company_name,
                    status=ComplianceAuditStatus.RESTRICTED,
                    risk_score=10,
                    gdpr_compliant=False,
                    jurisdiction_restrictions=[country],
                    explanation=f"Remote Agent Error: {raw_response.error.message}",
                )

            return ComplianceAuditResult(**raw_response.result)

        except (httpx.TimeoutException, asyncio.TimeoutError):
            # Network Timeout / Unresponsive Remote Agent
            return ComplianceAuditResult(
                company_name=company_name,
                status=ComplianceAuditStatus.RESTRICTED,
                risk_score=10,
                gdpr_compliant=False,
                jurisdiction_restrictions=[country],
                explanation=f"Network Timeout: Remote compliance service failed to respond within {timeout}s SLA (Fail-Closed).",
            )
        except Exception as ex:
            # Connection Refused, DNS Failure, or Broken Wire
            return ComplianceAuditResult(
                company_name=company_name,
                status=ComplianceAuditStatus.RESTRICTED,
                risk_score=10,
                gdpr_compliant=False,
                jurisdiction_restrictions=[country],
                explanation=f"Network Partition / Service Unavailable: {type(ex).__name__}: {str(ex)} (Fail-Closed).",
            )

    async def _dispatch_rpc(self, request_envelope: JsonRpcRequest, timeout: float) -> JsonRpcResponse:
        """Low-level HTTP transport posting the JSON-RPC envelope over the wire."""
        client = await self._get_client()
        http_response = await client.post(
            self.service_url,
            json=request_envelope.model_dump(),
            timeout=timeout,
        )
        raw_json = http_response.json()
        return JsonRpcResponse(**raw_json)
