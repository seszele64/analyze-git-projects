"""
Git-Ingest Repository Analyzer

A tool for analyzing GitHub repositories using git-ingest MCP server and AI analysis.
"""

__version__ = "1.0.0"

# Import main classes - handle import errors gracefully for development
try:
    from .github_mcp_analyzer import GitHubMCAnalyzer
    from .models.simple_project_schema import SimpleProject
    from .display import ResultsDisplay
    
    __all__ = ["GitHubMCAnalyzer", "SimpleProject", "ResultsDisplay"]
except ImportError as e:
    # During development, modules might not be complete yet
    print(f"Warning: Some modules not yet available: {e}")
    __all__ = []
