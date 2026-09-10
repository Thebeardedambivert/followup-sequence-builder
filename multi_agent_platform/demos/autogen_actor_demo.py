import asyncio
from pydantic import BaseModel, Field
from autogen_core import (
    AgentId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    message_handler,
)

# ---------------------------------------------------------------------------
# 1. TYPED MESSAGE CONTRACTS (What goes in, what comes out)
# ---------------------------------------------------------------------------

class LeadAuditRequest(BaseModel):
    company_name: str
    annual_revenue: float = Field(..., ge=0)
    employee_count: int = Field(..., gt=0)


class LeadAuditResponse(BaseModel):
    company_name: str
    is_enterprise: bool
    status_summary: str


# ---------------------------------------------------------------------------
# 2. THE ACTOR (Subclassing Microsoft's RoutedAgent)
# ---------------------------------------------------------------------------

class LeadEvaluatorAgent(RoutedAgent):
    """An autonomous enterprise lead evaluation actor."""

    def __init__(self) -> None:
        super().__init__("An agent that evaluates enterprise lead readiness.")

    @message_handler
    async def handle_lead_audit(
        self, 
        message: LeadAuditRequest, 
        ctx: MessageContext
    ) -> LeadAuditResponse:
        """
        AutoGen automatically routes any LeadAuditRequest message here!
        """
        # Internal Business Logic (Information Hiding)
        is_enterprise = message.annual_revenue >= 1_000_000.0 and message.employee_count >= 20
        
        summary = (
            f"Audit for {message.company_name}: "
            f"{'ENTERPRISE READY' if is_enterprise else 'GROWTH TIER'} "
            f"(Revenue: ${message.annual_revenue:,.2f}, Employees: {message.employee_count})"
        )

        return LeadAuditResponse(
            company_name=message.company_name,
            is_enterprise=is_enterprise,
            status_summary=summary
        )


# ---------------------------------------------------------------------------
# 3. THE RUNTIME ORCHESTRATION LOOP
# ---------------------------------------------------------------------------

async def main():
    # 1. Boot up the Microsoft Agent Runtime
    runtime = SingleThreadedAgentRuntime()

    # 2. Register our Agent class with the runtime under the type 'lead_evaluator'
    await LeadEvaluatorAgent.register(
        runtime, 
        type="lead_evaluator", 
        factory=lambda: LeadEvaluatorAgent()
    )

    # 3. Start the runtime engine
    runtime.start()

    # 4. Construct the target Agent's address (type + key)
    evaluator_address = AgentId(type="lead_evaluator", key="default")

    # 5. Create our typed Pydantic message
    request = LeadAuditRequest(
        company_name="Acme Corporation",
        annual_revenue=2_500_000.0,
        employee_count=45
    )

    # 6. ASYNCHRONOUSLY SEND THE MESSAGE OVER THE RUNTIME BUS
    print("Dispatching request to runtime...")
    response: LeadAuditResponse = await runtime.send_message(request, evaluator_address)

    # 7. Print the strongly-typed response
    print("\n--- Response Received From AutoGen Actor ---")
    print(f"Company: {response.company_name}")
    print(f"Enterprise Ready: {response.is_enterprise}")
    print(f"Summary: {response.status_summary}")

    # 8. Cleanly stop the runtime
    await runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
