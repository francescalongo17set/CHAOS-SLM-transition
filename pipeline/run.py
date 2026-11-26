"""The only code that composes systems.

question + context -> safety -> orchestrator -> {quick_reply | refuse | lightweight | agentic} -> verification
"""
import sys

import agentic.run
import lightweight.src.run
import orch.run
import quick_reply.run
import safety.run
import verification.run
from contracts.agentic import AgenticIn
from contracts.common import Answer, ContextWindow
from contracts.lightweight import LightweightIn
from contracts.orchestrator import OrchestratorIn
from contracts.quick_reply import QuickReplyIn
from contracts.safety import SafetyIn
from contracts.verification import VerificationIn
from pipeline.context import build_context

REFUSAL = "I can't help with this request."
BRANCHES = {
    "quick_reply": (quick_reply.run, QuickReplyIn),
    "lightweight": (lightweight.src.run, LightweightIn),
    "agentic": (agentic.run, AgenticIn),
}


def run(question: str, context: ContextWindow = ContextWindow()) -> Answer:
    checked = safety.run.run(SafetyIn(question, context))
    if not checked.safety_pass:
        return Answer(checked.user_message or REFUSAL)  # fixed text, nothing to verify

    question, context = checked.question, checked.context
    route = orch.run.run(OrchestratorIn(question, context)).route
    if route == "refuse":
        answer = Answer(REFUSAL)
    else:
        system, in_type = BRANCHES[route]
        answer = system.run(in_type(question, context)).answer
    return verification.run.run(VerificationIn(question, route, answer)).answer


if __name__ == "__main__":
    print(run(" ".join(sys.argv[1:]), build_context()))
