import asyncio
from typing import List
from rich.console import Console

from .github_mcp_analyzer import GitHubMCPAnalyzer
from .display import ResultsDisplay
from .models.simple_project_schema import SimpleProject

console = Console()


async def main():
    """Main function to test the git-ingest analyzer"""
    console.print("[bold blue]🚀 Git-Ingest Repository Analyzer[/bold blue]")
    
    # Initialize analyzer
    try:
        analyzer = GitHubMCPAnalyzer()
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
    ]
    
    projects_list: List[SimpleProject] = []
    
    for repo_url in test_repos:
        console.print(f"\n🔍 Analyzing repository: [bold]{repo_url}[/bold]")
        
        try:
            # Use the analyzer to get actual SimpleProject data
            project = await analyzer.analyze_repository(repo_url)
            projects_list.append(project)
            
            # Display results
            ResultsDisplay.display_results(project)
            
            # Save results to file
            output_file = ResultsDisplay.save_results_to_json(project)
            
        except Exception as e:
            console.print(f"[red]❌ Failed to analyze {repo_url}: {str(e)}[/red]")
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
            
            # Create error project
            error_project = SimpleProject(
                name=repo_url.split('/')[-1] if repo_url else "Unknown",
                url=repo_url,
                description=f"Analysis failed: {str(e)}",
                technologies=[],
                key_features=[],
                highlights=None
            )
            projects_list.append(error_project)
    
    # Display summary
    if len(projects_list) > 1:
        console.print("\n" + "="*50)
        ResultsDisplay.display_summary(projects_list)


if __name__ == "__main__":
    asyncio.run(main())
