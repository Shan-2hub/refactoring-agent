
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.graph.workflow import graph


router = APIRouter(prefix="/api", tags=["Agent API"])


class PullRequestPayload(BaseModel):
    pr_url: HttpUrl


class GitHubWebhookPayload(BaseModel):
    pull_request: dict | None = None
    pr_url: HttpUrl | None = None


class ApprovalPayload(BaseModel):
    approved: bool
    feedback: str = ""


@router.post("/webhooks/github")
def github_webhook(payload: GitHubWebhookPayload):

    pr_url = (
        payload.pull_request.get("html_url")
        if payload.pull_request
        else str(payload.pr_url) if payload.pr_url else None
    )

    if not pr_url:
        raise HTTPException(
            status_code=400,
            detail="Pull Request URL is required"
        )

    thread_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    initial_state = {
        "pr_url": pr_url,
        "branch_name": "",
        "repository": "",
        "code_contents": {},
        "lint_errors": {},
        "refactored_code": {},
        "is_approved": False,
        "reviewer_feedback": "",
        "review_attempts": 0,
        "history": []
    }

    try:
        graph.invoke(initial_state, config)

        snapshot = graph.get_state(config)

        return {
            "thread_id": thread_id,
            "status": "awaiting_approval",
            "proposed_code": snapshot.values.get(
                "refactored_code", {}
            ),
            "history": snapshot.values.get("history", [])
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.post("/reviews/{thread_id}/approve")
def approve_review(
    thread_id: str,
    payload: ApprovalPayload
):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    try:
        snapshot = graph.get_state(config)

        if not snapshot.values:
            raise HTTPException(
                status_code=404,
                detail="Review thread not found"
            )

        if "apply_changes_node" not in snapshot.next:
            raise HTTPException(
                status_code=409,
                detail="Review is not waiting for approval"
            )

        attempts = snapshot.values.get("review_attempts", 0)

        if not payload.approved and attempts >= 5:
            raise HTTPException(
                status_code=409,
                detail="Maximum review attempts reached"
            )

        updates = {
            "is_approved": payload.approved,
            "reviewer_feedback": payload.feedback,
            "review_attempts": attempts + 1,
            "history": [
                *snapshot.values.get("history", []),
                "Reviewer decision: " + (
                    "APPROVED" if payload.approved else "REJECTED"
                )
            ]
        }

        # Approval proceeds to the GitHub write node.
        if payload.approved:
            graph.update_state(
                config,
                updates,
                as_node="propose_refactor_node"
            )

        # Rejection schedules another AI refactoring attempt.
        else:
            if not payload.feedback.strip():
                raise HTTPException(
                    status_code=422,
                    detail="Feedback is required when rejecting"
                )

            graph.update_state(
                config,
                updates,
                as_node="lint_code_node"
            )

        # Resume from the updated checkpoint.
        graph.invoke(None, config)

        updated_snapshot = graph.get_state(config)

        if "apply_changes_node" in updated_snapshot.next:
            status = "awaiting_approval"
        else:
            status = "completed"

        return {
            "thread_id": thread_id,
            "status": status,
            "history": updated_snapshot.values.get("history", [])
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
