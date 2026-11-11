
from typing import Literal

from app.graph.state import ReviewState


def after_review(
    state: ReviewState
) -> Literal["propose_refactor", "commit_changes", "end"]:

    # Approved: proceed to GitHub commit
    if state.get("is_approved"):
        return "commit_changes"

    # Maximum of 3 human review attempts
    if state.get("review_attempts", 0) >= 3:
        return "end"

    # Rejected: send feedback back to the AI
    return "propose_refactor"
