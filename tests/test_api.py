
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app
from app.api import routes


client = TestClient(app)


class FakeGraph:
    """Mock LangGraph without calling GitHub or OpenAI."""

    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.invoke_calls = []
        self.update_calls = []

    def invoke(self, state, config):
        self.invoke_calls.append((state, config))

    def get_state(self, config):
        if len(self.snapshots) > 1:
            return self.snapshots.pop(0)
        return self.snapshots[0]

    def update_state(self, config, updates, as_node=None):
        self.update_calls.append((config, updates, as_node))


def make_snapshot(values, next_nodes=()):
    return SimpleNamespace(
        values=values,
        next=next_nodes
    )


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_github_webhook():
    fake = FakeGraph([
        make_snapshot(
            {
                "refactored_code": {
                    "main.py": "print('Hello')"
                },
                "history": ["Refactoring completed"]
            },
            ("apply_changes_node",)
        )
    ])

    routes.graph = fake

    response = client.post(
        "/api/webhooks/github",
        json={
            "pr_url": "https://github.com/test/demo/pull/1"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_approval"
    assert response.json()["proposed_code"]["main.py"] == "print('Hello')"
    assert len(fake.invoke_calls) == 1


def test_approval_endpoint():
    values = {
        "review_attempts": 0,
        "history": ["AI refactoring completed"]
    }

    updated_values = {
        "review_attempts": 1,
        "history": ["AI refactoring completed", "Reviewer decision: APPROVED"]
    }

    fake = FakeGraph([
        make_snapshot(values, ("apply_changes_node",)),
        make_snapshot(updated_values, ())
    ])

    routes.graph = fake

    response = client.post(
        "/api/reviews/test-thread/approve",
        json={
            "approved": True,
            "feedback": "Looks good"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    assert fake.update_calls[0][2] == "propose_refactor_node"
    assert fake.invoke_calls[0][0] is None


def test_rejection_endpoint():
    values = {
        "review_attempts": 0,
        "history": ["AI refactoring completed"]
    }

    updated_values = {
        "review_attempts": 1,
        "history": ["Reviewer decision: REJECTED"]
    }

    fake = FakeGraph([
        make_snapshot(values, ("apply_changes_node",)),
        make_snapshot(updated_values, ("apply_changes_node",))
    ])

    routes.graph = fake

    response = client.post(
        "/api/reviews/test-thread/approve",
        json={
            "approved": False,
            "feedback": "Improve variable names"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_approval"

    assert fake.update_calls[0][2] == "lint_code_node"


def test_rejection_requires_feedback():
    fake = FakeGraph([
        make_snapshot(
            {"review_attempts": 0, "history": []},
            ("apply_changes_node",)
        )
    ])

    routes.graph = fake

    response = client.post(
        "/api/reviews/test-thread/approve",
        json={
            "approved": False,
            "feedback": ""
        }
    )

    assert response.status_code == 422
    assert len(fake.update_calls) == 0


def test_unknown_review_thread():
    fake = FakeGraph([
        make_snapshot({}, ())
    ])

    routes.graph = fake

    response = client.post(
        "/api/reviews/unknown-thread/approve",
        json={
            "approved": True,
            "feedback": ""
        }
    )

    assert response.status_code == 404
