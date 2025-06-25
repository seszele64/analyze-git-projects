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

from .analyzer import GitIngestAnalyzer
from .display import ResultsDisplay
from .models import AnalysisResults


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repositories using git-ingest MCP server"
    )
    
    parser.add_argument(
        "repo_urls",
        nargs="+",
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
        analyzer = GitIngestAnalyzer(openrouter_api_key=args.api_key)
        
        # Test connection if requested
        if args.test_connection:
            connection_ok = await analyzer.test_connection()
            sys.exit(0 if connection_ok else 1)
        
        # Test connection before proceeding
        connection_ok = await analyzer.test_connection()
        if not connection_ok:
            print("❌ Cannot proceed without MCP server connection")
            sys.exit(1)
        
        # Analyze repositories
        results_list: List[AnalysisResults] = []
        
        for repo_url in args.repo_urls:
            print(f"\n🔍 Analyzing repository: {repo_url}")
            
            try:
                results = await analyzer.analyze_repository(repo_url)
                results_list.append(results)
                
                # Display results
                ResultsDisplay.display_results(results)
                
                # Save results to file
                output_file = f"{args.output_dir}/analysis_{results.repo_info.name}.json"
                ResultsDisplay.save_results_to_file(results, output_file)
                
            except Exception as e:
                print(f"❌ Failed to analyze {repo_url}: {e}")
                error_result = AnalysisResults(repo_url=repo_url, error=str(e))
                results_list.append(error_result)
        
        # Display summary if multiple repos
        if len(results_list) > 1:
            print("\n" + "="*50)
            ResultsDisplay.display_summary(results_list)
            
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