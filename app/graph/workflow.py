
import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.graph.state import ReviewState
from app.graph.nodes import (
    fetch_pr_node,
    lint_code_node,
    propose_refactor_node,
    apply_changes_node
)


connection = sqlite3.connect(
    "checkpoints.sqlite",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)
checkpointer.setup()


def build_workflow(checkpointer_override=None):

    builder = StateGraph(ReviewState)

    builder.add_node("fetch_pr_node", fetch_pr_node)
    builder.add_node("lint_code_node", lint_code_node)
    builder.add_node("propose_refactor_node", propose_refactor_node)
    builder.add_node("apply_changes_node", apply_changes_node)

    builder.add_edge(START, "fetch_pr_node")
    builder.add_edge("fetch_pr_node", "lint_code_node")
    builder.add_edge("lint_code_node", "propose_refactor_node")
    builder.add_edge("propose_refactor_node", "apply_changes_node")
    builder.add_edge("apply_changes_node", END)

    active_checkpointer = (
        checkpointer_override
        if checkpointer_override is not None
        else checkpointer
    )

    return builder.compile(
        checkpointer=active_checkpointer,
        interrupt_before=["apply_changes_node"]
    )


graph = build_workflow()
