"""
FastAPI backend server for the Healr dashboard.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os

from repo_parser import RepoParser
from issue_detector import IssueDetector
from explanation_logger import ExplanationLogger
from commit_manager import CommitManager
from main import SelfHealingOrchestrator


app = FastAPI(
    title="Healr API",
    description="AI-Powered Code Self-Healing System API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = SelfHealingOrchestrator()
logger = ExplanationLogger()
commit_manager = CommitManager()


# Pydantic models
class AnalyzeRequest(BaseModel):
    repo_path: str


class FixRequest(BaseModel):
    repo_path: str
    task_type: str = "all"
    dry_run: bool = False


class TestGenerateRequest(BaseModel):
    repo_path: str
    file_path: Optional[str] = None


class LogFilter(BaseModel):
    operation_type: Optional[str] = None
    file_path: Optional[str] = None
    limit: Optional[int] = 100


# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Healr API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/analyze")
async def analyze_repository(request: AnalyzeRequest):
    """
    Analyze a repository for code quality issues.
    """
    try:
        if not os.path.exists(request.repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        results = orchestrator.analyze_repository(request.repo_path)
        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fix")
async def fix_repository(request: FixRequest, background_tasks: BackgroundTasks):
    """
    Fix issues in a repository.
    """
    try:
        if not os.path.exists(request.repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        # Run fix in background for long-running operations
        results = orchestrator.fix_repository(
            request.repo_path,
            request.task_type,
            request.dry_run
        )

        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-tests")
async def generate_tests(request: TestGenerateRequest):
    """
    Generate tests for repository or specific file.
    """
    try:
        if not os.path.exists(request.repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        results = orchestrator.generate_tests(request.repo_path, request.file_path)

        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(
    operation_type: Optional[str] = None,
    file_path: Optional[str] = None,
    limit: int = 100
):
    """
    Get operation logs with optional filtering.
    """
    try:
        logs = logger.get_logs(
            operation_type=operation_type,
            file_path=file_path,
            limit=limit
        )

        return {
            "success": True,
            "data": logs,
            "count": len(logs)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/statistics")
async def get_log_statistics():
    """
    Get statistics about logged operations.
    """
    try:
        stats = logger.get_statistics()

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/search")
async def search_logs(query: str):
    """
    Search logs for a specific term.
    """
    try:
        results = logger.search_logs(query)

        return {
            "success": True,
            "data": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits")
async def get_commits(repo_path: str, max_count: int = 10):
    """
    Get recent commits from a repository.
    """
    try:
        if not os.path.exists(repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        if not commit_manager.is_git_repo(repo_path):
            raise HTTPException(status_code=400, detail="Not a git repository")

        repo = commit_manager.init_repo(repo_path)
        commits = commit_manager.get_recent_commits(repo, max_count)

        return {
            "success": True,
            "data": commits,
            "count": len(commits)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits/status")
async def get_repo_status(repo_path: str):
    """
    Get current status of files in the repository.
    """
    try:
        if not os.path.exists(repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        if not commit_manager.is_git_repo(repo_path):
            raise HTTPException(status_code=400, detail="Not a git repository")

        repo = commit_manager.init_repo(repo_path)
        status = commit_manager.get_file_status(repo)

        return {
            "success": True,
            "data": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_metrics(repo_path: str):
    """
    Get code quality metrics for a repository.
    """
    try:
        if not os.path.exists(repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        # Parse repository
        parser = RepoParser()
        files = parser.parse_repository(repo_path)

        # Analyze files
        detector = IssueDetector()
        all_metrics = []

        for file_data in files:
            if file_data['extension'] == '.py':
                issues = detector.analyze_file(file_data['path'])
                metrics = issues.get('metrics', {})
                metrics['file'] = file_data['relative_path']
                all_metrics.append(metrics)

        return {
            "success": True,
            "data": all_metrics,
            "count": len(all_metrics)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """
    Get current configuration.
    """
    try:
        with open("config/settings.json", 'r') as f:
            config = json.load(f)

        return {
            "success": True,
            "data": config
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config")
async def update_config(config: Dict[str, Any]):
    """
    Update configuration.
    """
    try:
        with open("config/settings.json", 'w') as f:
            json.dump(config, f, indent=2)

        return {
            "success": True,
            "message": "Configuration updated"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/report")
async def generate_report(repo_path: str):
    """
    Generate a comprehensive report.
    """
    try:
        if not os.path.exists(repo_path):
            raise HTTPException(status_code=404, detail="Repository path not found")

        report = orchestrator.generate_report(repo_path)

        return {
            "success": True,
            "data": {
                "report": report
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    # Load server configuration
    with open("config/settings.json", 'r') as f:
        config = json.load(f)

    server_config = config['server']

    uvicorn.run(
        "api_server:app",
        host=server_config['host'],
        port=server_config['port'],
        reload=server_config['reload']
    )
