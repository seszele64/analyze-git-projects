"""
Git-Ingest Repository Analyzer

A tool for analyzing GitHub repositories using git-ingest MCP server and AI analysis.
"""

__version__ = "1.0.0"

# Import main classes - handle import errors gracefully for development
try:
    from .analyzer import GitIngestAnalyzer
    from .models import AnalysisResults, RepositoryInfo
    from .display import ResultsDisplay
    
    __all__ = ["GitIngestAnalyzer", "AnalysisResults", "RepositoryInfo", "ResultsDisplay"]
except ImportError as e:
    # During development, modules might not be complete yet
    print(f"Warning: Some modules not yet available: {e}")
    __all__ = []