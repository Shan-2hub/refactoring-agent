
import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.graph.state import ReviewState
from app.graph.nodes import (
    fetch_pr_node,
    lint_code_node,
    propose_refactor_node,
    human_review_node,
    commit_approved_changes_node
)
from app.graph.edges import after_review


connection = sqlite3.connect(
    "checkpoints.sqlite",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)
checkpointer.setup()


def build_workflow(checkpointer_override=None):

    builder = StateGraph(ReviewState)

    # Register nodes
    builder.add_node("fetch_pr", fetch_pr_node)
    builder.add_node("lint_code", lint_code_node)
    builder.add_node("propose_refactor", propose_refactor_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("commit_changes", commit_approved_changes_node)

    # Initial execution
    builder.add_edge(START, "fetch_pr")

    builder.add_edge("fetch_pr", "lint_code")
    builder.add_edge("lint_code", "propose_refactor")
    builder.add_edge("propose_refactor", "human_review")

    # Human approval routing
    builder.add_conditional_edges(
        "human_review",
        after_review,
        {
            "propose_refactor": "propose_refactor",
            "commit_changes": "commit_changes",
            "end": END
        }
    )

    # Finish after approved commit
    builder.add_edge("commit_changes", END)

    active_checkpointer = (
        checkpointer_override
        if checkpointer_override is not None
        else checkpointer
    )

    return builder.compile(
        checkpointer=active_checkpointer
    )


graph = build_workflow()
