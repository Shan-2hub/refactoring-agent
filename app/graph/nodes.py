
import re
from urllib.parse import urlparse

from github import Github
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import OPENAI_API_KEY, OPENAI_MODEL, GITHUB_TOKEN
from app.graph.state import ReviewState
from app.tools.sandbox_tool import check_python_code


# -----------------------------------------
# Structured output from the AI model
# -----------------------------------------

class RefactorOutput(BaseModel):
    refactored_code: dict[str, str] = Field(
        description="Mapping of filenames to their complete refactored Python source code"
    )
    summary: str = Field(
        description="Short explanation of the improvements"
    )


# -----------------------------------------
# NODE 1: Fetch GitHub Pull Request
# -----------------------------------------

def fetch_pr_node(state: ReviewState) -> dict:

    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is missing in .env")

    pr_url = state["pr_url"]

    parsed_url = urlparse(pr_url)

    if parsed_url.scheme != "https" or parsed_url.netloc != "github.com":
        raise ValueError("Only HTTPS GitHub Pull Request URLs are allowed")

    match = re.fullmatch(
        r"/([^/]+)/([^/]+)/pull/(\d+)/?",
        parsed_url.path
    )

    if not match:
        raise ValueError("Invalid GitHub Pull Request URL")

    owner, repo_name, pr_number = match.groups()

    github = Github(GITHUB_TOKEN)

    try:
        repository = github.get_repo(f"{owner}/{repo_name}")
        pull_request = repository.get_pull(int(pr_number))

        code_contents = {}

        for file in pull_request.get_files():

            # Process Python files only
            if not file.filename.endswith(".py"):
                continue

            # Ignore deleted files
            if file.status == "removed":
                continue

            # Limit the number of files
            if len(code_contents) >= 10:
                break

            content = repository.get_contents(
                file.filename,
                ref=pull_request.head.sha
            )

            if isinstance(content, list):
                continue

            if content.size > 100_000:
                continue

            source_code = content.decoded_content.decode("utf-8")

            code_contents[file.filename] = source_code

        if not code_contents:
            raise ValueError("No eligible Python files found in this PR")

        return {
            "repository": repository.full_name,
            "branch_name": pull_request.head.ref,
            "code_contents": code_contents,
            "history": [
                *state.get("history", []),
                f"Fetched {len(code_contents)} Python files from PR #{pr_number}"
            ]
        }

    finally:
        github.close()


# -----------------------------------------
# NODE 2: Run Python linting
# -----------------------------------------

def lint_code_node(state: ReviewState) -> dict:

    code_contents = state.get("code_contents", {})

    if not code_contents:
        raise ValueError("No source code available for linting")

    lint_errors = {}

    for filename, source_code in code_contents.items():

        result = check_python_code.invoke({
            "source_code": source_code,
            "filename": filename.split("/")[-1]
        })

        lint_errors[filename] = result

    return {
        "lint_errors": lint_errors,
        "history": [
            *state.get("history", []),
            "Completed Black and Flake8 analysis"
        ]
    }


# -----------------------------------------
# NODE 3: AI-powered refactoring
# -----------------------------------------

def propose_refactor_node(state: ReviewState) -> dict:

    code_contents = state.get("code_contents", {})
    lint_errors = state.get("lint_errors", {})

    if not code_contents:
        raise ValueError("No source code available for refactoring")

    total_chars = sum(len(code) for code in code_contents.values())

    if total_chars > 60_000:
        raise ValueError(
            "PR source exceeds the current AI review limit of 60,000 characters"
        )

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0,
        api_key=OPENAI_API_KEY
    )

    structured_llm = llm.with_structured_output(RefactorOutput)

    prompt = f"""
You are a senior Python software engineer.

Your task is to refactor the supplied Python source code.

Requirements:

1. Preserve the original program's functionality.
2. Improve readability and maintainability.
3. Follow PEP 8 conventions.
4. Fix relevant Black and Flake8 issues.
5. Avoid unnecessary changes.
6. Do not introduce new dependencies.
7. Return the complete source code for every supplied file.
8. Never invent missing functionality.

Original Python files:

{code_contents}

Linting results:

{lint_errors}

Return the improved code and a concise explanation.
"""

    response = structured_llm.invoke(prompt)

    refactored_code = response.refactored_code

    # Ensure the model returned every original file
    if set(refactored_code) != set(code_contents):
        raise ValueError(
            "AI response did not contain exactly the original file set"
        )

    return {
        "refactored_code": refactored_code,
        "history": [
            *state.get("history", []),
            "AI-generated refactoring completed: " + response.summary
        ]
    }
