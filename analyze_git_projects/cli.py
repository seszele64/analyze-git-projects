#!/usr/bin/env python3
"""
CLI entry point for the Git-Ingest Repository Analyzer

Usage:
    python -m gitingest_analyzer.cli <repo_url>
    python -m gitingest_analyzer.cli --help
"""

import argparse
import asyncio
import sys
from typing import List

from .github_mcp_analyzer import GitHubMCPAnalyzer
from .display import ResultsDisplay
from .models.simple_project_schema import SimpleProject


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repositories using git-ingest MCP server"
    )
    
    parser.add_argument(
        "repo_urls",
        nargs="*",
        help="GitHub repository URLs to analyze"
    )
    
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save analysis results (default: current directory)"
    )
    
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test MCP server connection and exit"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


async def cli_main():
    """Main CLI function"""
    args = parse_args()
    
    try:
        # Initialize analyzer
        analyzer = GitHubMCPAnalyzer(openrouter_api_key=args.api_key)
        
        # Test connection if requested
        if args.test_connection:
            connection_ok = await analyzer.test_connection()
            sys.exit(0 if connection_ok else 1)
        
        # Skip repo analysis if test connection was requested
        if args.test_connection:
            return
        
        # Test connection before proceeding (unless already tested)
        if not args.test_connection:
            connection_ok = await analyzer.test_connection()
            if not connection_ok:
                print("❌ Cannot proceed without MCP server connection")
                sys.exit(1)
        
        # Skip analysis if test connection was requested
        if args.test_connection:
            return
            
        # Check if we have repo URLs to analyze
        if not args.repo_urls:
            print("❌ No repository URLs provided")
            sys.exit(1)
        
        # Analyze repositories
        projects_list: List[SimpleProject] = []
        
        for repo_url in args.repo_urls:
            print(f"\n🔍 Analyzing repository: {repo_url}")
            
            try:
                project = await analyzer.analyze_repository(repo_url)
                projects_list.append(project)
                
                # Display results
                ResultsDisplay.display_results(project)
                
                # Save results to file
                repo_name = project.name or "unknown"
                output_file = f"{args.output_dir}/analysis_{repo_name}.json"
                with open(output_file, 'w') as f:
                    f.write(SimpleProject.to_json(project))
                
            except Exception as e:
                print(f"❌ Failed to analyze {repo_url}: {e}")
                error_project = SimpleProject(
                    name=repo_url.split('/')[-1] if repo_url else "Unknown",
                    url=repo_url,
                    description=f"Analysis failed: {str(e)}",
                    technologies=[],
                    key_features=[],
                    highlights=None
                )
                projects_list.append(error_project)
        
        # Display summary if multiple repos
        if len(projects_list) > 1:
            print("\n" + "="*50)
            ResultsDisplay.display_summary(projects_list)
            
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(cli_main())
