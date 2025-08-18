#!/usr/bin/env python3
"""
Example usage of the documentation analyzer.

This script demonstrates how to use the documentation analyzer
with a few popular repositories.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from examples
sys.path.insert(0, str(Path(__file__).parent))

from analyze_documentation import DocumentationAnalyzer, format_analysis_output

# Example repositories to analyze
EXAMPLE_REPOS = [
    "https://github.com/johnbalvin/pyairbnb"
]

def main():
    """Run example analysis on popular repositories."""
    
    github_pat = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not github_pat:
        print("Please set GITHUB_PERSONAL_ACCESS_TOKEN environment variable")
        return
    
    analyzer = DocumentationAnalyzer(github_pat)
    
    print("🔍 Analyzing documentation for example repositories...")
    print("=" * 60)
    
    for repo_url in EXAMPLE_REPOS:
        try:
            print(f"\n📊 Analyzing: {repo_url}")
            analysis = analyzer.analyze_repository(repo_url)
            print(format_analysis_output(analysis))
        except Exception as e:
            print(f"❌ Failed to analyze {repo_url}: {e}")
            print("-" * 60)

if __name__ == "__main__":
    main()