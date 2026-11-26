"""Decision model + dispatcher. STUB: always escalates to agentic with zero confidence."""
from contracts.orchestrator import OrchestratorIn, OrchestratorOut


def run(x: OrchestratorIn) -> OrchestratorOut:
    return OrchestratorOut(route="agentic", reason="stub", confidence=0.0)
