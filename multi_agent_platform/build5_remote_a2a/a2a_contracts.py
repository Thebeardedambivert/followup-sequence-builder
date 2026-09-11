"""
a2a_contracts.py
================
Build 5: Remote Agent-to-Agent (A2A) Contract Specification.

This module defines the explicit wire envelopes for crossing network boundaries:
1. JSON-RPC 2.0 Request Envelope (with mandatory Idempotency Key)
2. JSON-RPC 2.0 Error and Response Envelopes (with mutual exclusion invariant)
3. AgentCapabilityCard (A2A Discovery Specification)
4. Domain Payloads for Remote Compliance Auditing
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class JsonRpcErrorCode(int, Enum):
    """Standard JSON-RPC 2.0 error codes plus application-specific error extensions."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # Application-specific extensions (-32000 to -32099)
    TIMEOUT_EXCEEDED = -32001
    RATE_LIMIT_EXCEEDED = -32002
    IDEMPOTENCY_COLLISION = -32003


class JsonRpcRequest(BaseModel):
    """
    Standard JSON-RPC 2.0 Request Envelope.
    
    Invariants:
    - jsonrpc must be explicitly '2.0'.
    - id tracks the request for asynchronous response correlation.
    - idempotency_key prevents duplicate side effects during retries.
    """
    jsonrpc: Literal["2.0"] = "2.0"
    id: str = Field(..., description="Unique correlation ID for tracking response matching.")
    idempotency_key: str = Field(..., description="Deterministic key preventing duplicate replay execution.")
    method: str = Field(..., min_length=1, description="Target remote agent capability or tool name.")
    params: Dict[str, Any] = Field(default_factory=dict, description="Domain arguments for the target capability.")


class JsonRpcError(BaseModel):
    """Standard JSON-RPC 2.0 Error Envelope."""
    code: int = Field(..., description="Deterministic numeric error code.")
    message: str = Field(..., description="Human-readable summary of the error condition.")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Optional diagnostic context.")


class JsonRpcResponse(BaseModel):
    """
    Standard JSON-RPC 2.0 Response Envelope.
    
    Hard Invariant:
    A response MUST contain either 'result' or 'error', NEVER both, and NEVER neither.
    """
    jsonrpc: Literal["2.0"] = "2.0"
    id: str = Field(..., description="Matches the request ID that prompted this response.")
    result: Optional[Any] = Field(default=None, description="Successful execution payload.")
    error: Optional[JsonRpcError] = Field(default=None, description="Failure diagnostic payload.")

    @model_validator(mode="after")
    def validate_mutual_exclusion(self) -> "JsonRpcResponse":
        """Deterministic gate enforcing that result and error cannot co-exist or both be absent."""
        has_result = self.result is not None
        has_error = self.error is not None

        if has_result and has_error:
            raise ValueError("Invalid JSON-RPC Response: Cannot contain both 'result' and 'error'.")
        if not has_result and not has_error:
            raise ValueError("Invalid JSON-RPC Response: Must contain either 'result' or 'error'.")
        return self


class AgentCapabilityCard(BaseModel):
    """
    A2A Discovery Card.
    
    Published by remote agents so coordinators can discover capabilities,
    schemas, and SLA expectations before dispatching network calls.
    """
    agent_id: str = Field(..., description="Unique identifier of the remote specialist agent.")
    agent_name: str = Field(..., description="Human-readable title of the agent.")
    version: str = Field(..., description="Semantic version of the agent service (e.g. '1.0.0').")
    description: str = Field(..., description="Functional mandate of this agent.")
    supported_methods: List[str] = Field(..., min_length=1, description="List of JSON-RPC methods exposed.")
    sla_timeout_seconds: float = Field(..., gt=0.0, description="Expected maximum processing time for SLA planning.")


class ComplianceAuditStatus(str, Enum):
    CLEARED = "CLEARED"
    RESTRICTED = "RESTRICTED"
    PROHIBITED = "PROHIBITED"


class ComplianceAuditResult(BaseModel):
    """Structured domain payload returned by the Remote Compliance Specialist."""
    company_name: str = Field(..., description="Target company evaluated.")
    status: ComplianceAuditStatus = Field(..., description="Overall compliance judgment.")
    risk_score: int = Field(..., ge=0, le=10, description="Audit risk score from 0 (safest) to 10 (prohibited).")
    gdpr_compliant: bool = Field(..., description="Flag indicating strict GDPR data-processing clearance.")
    jurisdiction_restrictions: List[str] = Field(default_factory=list, description="List of blocked jurisdictions.")
    explanation: str = Field(..., min_length=10, description="Defensible legal rationale.")
