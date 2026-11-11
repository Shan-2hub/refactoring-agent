from typing import TypedDict

class ReviewState(TypedDict):
    # Pull request info
    pr_url: str
    branch_name: str
    repository: str

    # Original source code
    code_contents: dict[str, str]

    # Code quality analysis
    lint_errors: dict[str, str]

    # AI-generated refactoring
    refactored_code: dict[str, str]

    # Human review
    is_approved: bool
    reviewer_feedback: str

    # Workflow tracking
    history: list[str]