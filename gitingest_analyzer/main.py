import asyncio
from typing import List
from rich.console import Console

from .analyzer import GitIngestAnalyzer
from .display import ResultsDisplay
from .models import AnalysisResults

console = Console()


async def main():
    """Main function to test the git-ingest analyzer"""
    console.print("[bold blue]🚀 Git-Ingest Repository Analyzer[/bold blue]")
    
    # Initialize analyzer
    try:
        analyzer = GitIngestAnalyzer()
    except Exception as e:
        console.print(f"[red]Failed to initialize analyzer: {str(e)}[/red]")
        return
    
    # Test connection
    console.print("\n🔗 Testing git-ingest MCP server connection...")
    connection_ok = await analyzer.test_connection()
    
    if not connection_ok:
        console.print("[red]Cannot proceed without MCP server connection[/red]")
        console.print("[yellow]Make sure you have 'uvx' installed and the git-ingest package is accessible[/yellow]")
        return
    
    # Test repositories
    test_repos = [
        # "https://github.com/octocat/Hello-World",
        "https://github.com/seszele64/trivia-quiz-builder",
    ]
    
    results_list: List[AnalysisResults] = []
    
    for repo_url in test_repos:
        console.print(f"\n🔍 Analyzing repository: [bold]{repo_url}[/bold]")
        
        try:
            results = await analyzer.analyze_repository(repo_url)
            results_list.append(results)
            
            # Display results
            ResultsDisplay.display_results(results)
            
            # Save results to file
            output_file = ResultsDisplay.save_results_to_file(results)
            
        except Exception as e:
            console.print(f"[red]❌ Failed to analyze {repo_url}: {str(e)}[/red]")
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
            
            # Create error result
            error_result = AnalysisResults(repo_url=repo_url, error=str(e))
            results_list.append(error_result)
    
    # Display summary
    if len(results_list) > 1:
        console.print("\n" + "="*50)
        ResultsDisplay.display_summary(results_list)


if __name__ == "__main__":
    asyncio.run(main())