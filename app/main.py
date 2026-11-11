
from fastapi import FastAPI

app = FastAPI(
    title="Autonomous Code Review & Refactoring Agent",
    description="AI-powered code review and refactoring using LangGraph",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Refactoring Agent API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
