
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langgraph.checkpoint.memory import InMemorySaver

from app.graph.workflow import build_workflow


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

    assert "fetch_pr_node" in nodes
    assert "lint_code_node" in nodes
    assert "propose_refactor_node" in nodes
    assert "apply_changes_node" in nodes
