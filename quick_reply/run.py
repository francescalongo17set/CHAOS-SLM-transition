"""QuickReply. STUB: returns a placeholder answer with no sources."""
from contracts.common import Answer
from contracts.quick_reply import QuickReplyIn, QuickReplyOut


def run(x: QuickReplyIn) -> QuickReplyOut:
    return QuickReplyOut(Answer("[quick_reply stub] not implemented yet"))
