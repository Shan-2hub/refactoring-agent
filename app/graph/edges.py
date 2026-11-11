
from typing import Literal

from app.graph.state import ReviewState


def after_refactor(
    state: ReviewState
) -> Literal["end"]:

    if not state.get("refactored_code"):
        raise ValueError("Refactoring produced no output")

    return "end"
