# Autonomous Code Review & Refactoring Agent

An AI-powered code review and refactoring agent that analyzes Python files in GitHub Pull Requests, identifies code-quality issues, suggests improvements using OpenAI, and applies changes only after human approval.

## Features

- Fetch Python files from GitHub Pull Requests.
- Validate Python syntax using AST.
- Check code formatting using Black.
- Detect code-quality issues using Flake8.
- Generate refactored code using OpenAI.
- Manage the workflow using LangGraph.
- Support Human-in-the-Loop (HITL) approval and rejection.
- Retry refactoring using reviewer feedback.
- Commit approved changes to the GitHub branch.
- Persist workflow checkpoints using SQLite.

## Tech Stack

- Python 3.11
- FastAPI
- LangGraph
- OpenAI API
- PyGithub
- Black
- Flake8
- SQLite
- Pydantic
- Pytest

## Project Structure

```text
refactoring-agent/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── graph/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── edges.py
│   │   └── workflow.py
│   ├── tools/
│   │   └── sandbox_tool.py
│   ├── main.py
│   └── config.py
├── tests/
│   ├── test_api.py
│   ├── test_nodes.py
│   ├── test_sandbox.py
│   └── test_workflow.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Shan-2hub/refactoring-agent.git
cd refactoring-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
GITHUB_TOKEN=your_github_token
OPENAI_MODEL=gpt-4.1-mini
```

Never commit your `.env` file or expose your API keys.

## Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application status |
| GET | `/health` | Health check |
| POST | `/api/webhooks/github` | Start a PR review |
| POST | `/api/reviews/{thread_id}/approve` | Approve or reject proposed changes |

### Start a review

POST `/api/webhooks/github`

Example request:

```json
{
  "pr_url": "https://github.com/owner/repository/pull/1"
}
```

### Approve proposed changes

POST `/api/reviews/{thread_id}/approve`

Example request:

```json
{
  "approved": true,
  "feedback": "Looks good"
}
```

### Reject proposed changes

```json
{
  "approved": false,
  "feedback": "Improve variable names and simplify the logic"
}
```

## Workflow Architecture

1. Fetch Pull Request – retrieves Python source files from GitHub.
2. Code Analysis – checks syntax, formatting, and linting issues.
3. AI Refactoring – generates improved code using OpenAI.
4. Human Approval – pauses the workflow for reviewer feedback.
5. Apply Changes – commits approved changes to the GitHub branch.

Rejected changes are sent back through the refactoring workflow with reviewer feedback.

LangGraph manages the workflow state, execution flow, and checkpoint persistence.

## Run Tests

Run the complete test suite:

```bash
python -m pytest tests/ -v
```

## Security Notes

- Store API credentials in environment variables.
- Do not commit secrets or checkpoint databases.
- The current code-analysis tool validates and lints source code; it does not execute submitted Python code.
- Production deployment should include GitHub webhook signature verification and authentication for approval endpoints.
- GitHub write permissions are required to commit approved changes.

## Future Improvements

- Add Docker-based isolated execution if code execution is required.
- Add authenticated reviewer access.
- Implement GitHub webhook signature verification.
- Support additional programming languages.
- Add a web-based review dashboard.

## Author

Developed as an AI agent engineering project using Python, LangGraph, FastAPI, and OpenAI.