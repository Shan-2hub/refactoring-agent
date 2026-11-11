
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.nodes import lint_code_node


def test_lint_node_with_valid_code():

    state = {
        "pr_url": "",
        "branch_name": "",
        "repository": "",
        "code_contents": {
            "calculator.py": "def add(a, b):\n    return a + b\n"
        },
        "lint_errors": {},
        "refactored_code": {},
        "is_approved": False,
        "reviewer_feedback": "",
        "history": []
    }

    result = lint_code_node(state)

    assert "calculator.py" in result["lint_errors"]
    assert "SYNTAX: PASS" in result["lint_errors"]["calculator.py"]
    assert "BLACK: PASS" in result["lint_errors"]["calculator.py"]
    assert "FLAKE8: PASS" in result["lint_errors"]["calculator.py"]


def test_lint_node_without_code():

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
        lint_code_node(state)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "No source code" in str(error)
