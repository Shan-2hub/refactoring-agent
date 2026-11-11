import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.graph.state import ReviewState
from app.graph.nodes import (
    fetch_pr_node,
    lint_code_node,
    propose_refactor_node
)
from app.graph.edges import after_refactor


# -----------------------------------------
# SQLite checkpoint configuration
# -----------------------------------------

connection = sqlite3.connect(
    "checkpoints.sqlite",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)
checkpointer.setup()


# -----------------------------------------
# Build LangGraph workflow
# -----------------------------------------

def build_workflow(checkpointer_override=None):

    builder = StateGraph(ReviewState)

    # Register nodes
    builder.add_node("fetch_pr", fetch_pr_node)
    builder.add_node("lint_code", lint_code_node)
    builder.add_node("propose_refactor", propose_refactor_node)

    # Starting point
    builder.add_edge(START, "fetch_pr")

    # Sequential execution
    builder.add_edge("fetch_pr", "lint_code")
    builder.add_edge("lint_code", "propose_refactor")

    # Conditional routing
    builder.add_conditional_edges(
        "propose_refactor",
        after_refactor,
        {
            "end": END
        }
    )

    # Compile with persistent checkpointing
    active_checkpointer = (
        checkpointer_override
        if checkpointer_override is not None
        else checkpointer
    )

    return builder.compile(checkpointer=active_checkpointer)


# Application workflow
graph = build_workflow()
