
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command

from app.graph.state import ReviewState
from app.graph.nodes import human_review_node
from app.graph.workflow import build_workflow
from app.graph.edges import after_review


def test_workflow_compiles():
    workflow = build_workflow(
        checkpointer_override=InMemorySaver()
    )
    assert workflow is not None


def test_workflow_contains_all_nodes():
    workflow = build_workflow(
        checkpointer_override=InMemorySaver()
    )

    nodes = workflow.get_graph().nodes

    assert "fetch_pr" in nodes
    assert "lint_code" in nodes
    assert "propose_refactor" in nodes
    assert "human_review" in nodes
    assert "commit_changes" in nodes


def test_approved_routes_to_commit():
    state = {
        "is_approved": True,
        "review_attempts": 1
    }

    assert after_review(state) == "commit_changes"


def test_rejected_routes_back_to_ai():
    state = {
        "is_approved": False,
        "review_attempts": 1
    }

    assert after_review(state) == "propose_refactor"


def test_maximum_attempts_reached():
    state = {
        "is_approved": False,
        "review_attempts": 3
    }

    assert after_review(state) == "end"


def test_human_review_pause_and_resume():

    builder = StateGraph(ReviewState)

    builder.add_node("human_review", human_review_node)
    builder.add_edge(START, "human_review")
    builder.add_edge("human_review", END)

    workflow = builder.compile(
        checkpointer=InMemorySaver()
    )

    initial_state = {
        "pr_url": "",
        "branch_name": "",
        "repository": "",
        "code_contents": {},
        "lint_errors": {},
        "refactored_code": {
            "example.py": "print('Hello')"
        },
        "is_approved": False,
        "reviewer_feedback": "",
        "review_attempts": 0,
        "history": []
    }

    config = {
        "configurable": {
            "thread_id": "hitl-test-001"
        }
    }

    # First call pauses at interrupt()
    paused = workflow.invoke(initial_state, config)

    assert "__interrupt__" in paused

    # Resume with human approval
    resumed = workflow.invoke(
        Command(
            resume={
                "approved": True,
                "feedback": "Looks good"
            }
        ),
        config
    )

    assert resumed["is_approved"] is True
    assert resumed["reviewer_feedback"] == "Looks good"
    assert resumed["review_attempts"] == 1
