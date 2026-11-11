import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1])
)

from langgraph.checkpoint.memory import InMemorySaver

from app.graph.workflow import build_workflow
from app.graph.edges import after_refactor


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


def test_after_refactor_routes_to_end():

    state = {
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
        "history": []
    }

    assert after_refactor(state) == "end"


def test_after_refactor_rejects_empty_output():

    state = {
        "pr_url": "",
        "branch_name": "",
        "repository": "",
        "code_contents": {},
        "lint_errors": {},
        "refactored_code": {},
        "is_approved": False,
        "reviewer_feedback": "",
        "history": []
    }

    try:
        after_refactor(state)
        assert False, "Expected ValueError"
    except ValueError:
        pass
