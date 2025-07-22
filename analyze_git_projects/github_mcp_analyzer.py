from dotenv import load_dotenv
import asyncio
import os
import re
from typing import Dict, List, Any, Optional
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models.simple_project_schema import SimpleProject
from .models import RepositoryInfo

load_dotenv()  
console = Console()


class GitHubMCAnalyzer:
    """Repository analyzer using GitHub MCP server"""
    
    def __init__(self, openrouter_api_key: str = None):
        """
        Initialize the GitHub MCP analyzer
        
        Args:
            openrouter_api_key: OpenRouter API key for LLM analysis
        """
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.github_pat = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        
        if not self.github_pat:
            console.print("[red]Error: GITHUB_PERSONAL_ACCESS_TOKEN not found in environment[/red]")
            raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN is required")
        
        if not self.openrouter_api_key:
            console.print("[yellow]Warning: No OpenRouter API key provided. Using dummy model.[/yellow]")
        
        # Initialize GitHub MCP server using Docker
        try:
            self.github_server = MCPServerStdio(
                command="docker",
                args=[
                    "run", "-i", "--rm",
                    "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={self.github_pat}",
                    "-e", "GITHUB_READ_ONLY=1",
                    "ghcr.io/github/github-mcp-server"
                ]
            )
            console.print("[green]GitHub MCP server configured with Docker[/green]")
        except Exception as e:
            console.print(f"[red]Failed to configure GitHub MCP server: {str(e)}[/red]")
            raise
        
        # Initialize AI model
        if self.openrouter_api_key:
            model = OpenAIModel(
                "qwen/qwen3-235b-a22b",
                provider=OpenRouterProvider(api_key=self.openrouter_api_key),
            )
        else:
            model = "qwen/qwen3-235b-a22b"
        
        # Initialize agent with the MCP server
        self.agent = Agent(
            model=model,
            mcp_servers=[self.github_server],
            system_prompt=self._get_system_prompt(),
            retries=3
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """
        You are a GitHub repository analysis expert. Your job is to analyze GitHub repositories 
        and provide insights about their structure, technologies, and development activity.
        
        When analyzing repositories, use the available MCP tools to:
        - Search repositories using search_repositories
        - Get repository details and file contents using get_file_contents
        - Analyze code patterns using search_code
        - Review commit history using list_commits
        - Examine pull requests using list_pull_requests and get_pull_request
        - List branches using list_branches
        
        Focus on:
        - Repository metadata and statistics
        - Technology stack identification from package files
        - Development activity patterns
        - Contributor information
        - Code quality indicators
        - Project health metrics
        
        Be thorough but concise in your analysis.
        """
    
    async def test_connection(self) -> bool:
        """Test connection to GitHub MCP server"""
        try:
            console.print("[blue]Testing GitHub MCP server connection...[/blue]")
            async with self.agent.run_mcp_servers():
                tools = await self.github_server.list_tools()
                console.print(f"[green]✅ GitHub MCP Server Connected![/green]")
                console.print(f"[blue]Available tools ({len(tools)}):[/blue]")
                
                # Filter for the specific tools we want to use
                target_tools = [
                    "search_users", "search_repositories", "search_code",
                    "list_branches", "list_commits", "list_pull_requests",
                    "get_pull_request", "get_file_contents"
                ]
                
                available_tools = [tool.name for tool in tools]
                for tool in available_tools:
                    if tool in target_tools:
                        console.print(f"  - [cyan]{tool}[/cyan]: ✅ Available")
                    else:
                        console.print(f"  - [gray]{tool}[/gray]: Available")
                
                missing_tools = [t for t in target_tools if t not in available_tools]
                if missing_tools:
                    console.print(f"[yellow]Warning: Missing expected tools: {missing_tools}[/yellow]")
                
                return True
        except Exception as e:
            console.print(f"[red]❌ GitHub MCP Server Connection Failed: {str(e)}[/red]")
            import traceback
            console.print(f"[red]Full traceback: {traceback.format_exc()}[/red]")
            return False
    
    async def analyze_repository(self, repo_url: str) -> SimpleProject:
        """
        Simplified repository analysis returning SimpleProject schema
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            SimpleProject object containing key project information
        """
        repo_info = RepositoryInfo.from_url(repo_url)
        results = SimpleProject(
            name=repo_info.name,
            url=repo_info.url,
            description="No description available",
            technologies=[],
            key_features=[],
            highlights=None
        )
        
        try:
            async with self.agent.run_mcp_servers():
                # Create analysis agent with SimpleProject result type
                analysis_agent = Agent(
                    self.agent.model,
                    mcp_servers=[self.github_server],
                    result_type=SimpleProject,
                    system_prompt=self._get_simple_analysis_prompt()
                )
                
                analysis_prompt = self._build_simple_analysis_prompt(repo_url)
                analysis_result = await analysis_agent.run(analysis_prompt)
                
                if analysis_result.data:
                    results = analysis_result.data
                
                # Augment with direct API data
                search_result = await self.agent.run(
                    f"Use search_repositories with query='repo:{repo_info.owner}/{repo_info.name}'"
                )
                if search_result.output:
                    repo_data = search_result.output[0]
                    if not results.description or results.description == "No description available":
                        results.description = repo_data.get("description", results.description)
                    
        except Exception as e:
            console.print(f"[yellow]Partial analysis failure: {str(e)}[/yellow]")
        
        return results
    
    def _get_simple_analysis_prompt(self) -> str:
        """System prompt for SimpleProject analysis"""
        return """
        You are a technical analyst creating project summaries. Extract these key elements:
        - description: Clear, concise project purpose
        - technologies: Primary languages/frameworks used
        - key_features: 3-5 main capabilities
        - highlights: Notable achievements or metrics
        
        Be factual and focus on information from:
        1. Repository description
        2. README file
        3. Code structure
        """
    
    def _build_simple_analysis_prompt(self, repo_url: str) -> str:
        """Build prompt for SimpleProject analysis"""
        repo_info = RepositoryInfo.from_url(repo_url)
        return f"""
        Analyze the GitHub repository at {repo_url} and provide a structured summary including:
        
        1. A one-sentence description of the project's purpose
        2. The primary technologies used (languages, frameworks, databases)
        3. 3-5 key features or capabilities
        4. The creator's role or contributions (if evident)
        5. Any notable achievements or metrics
        
        Repository: {repo_info.owner}/{repo_info.name}
        """
            

REPOS_TO_ANALYZE = [
    # 'https://github.com/seszele64/sejm-scraper',
    # 'https://github.com/seszele64/dagster-dbt-pipeline',
    # 'https://github.com/seszele64/trivia-quiz-builder',
    'https://github.com/seszele64/llm-analysis-pipeline',
    # 'https://github.com/seszele64/bike-data-flow',
    # 'https://github.com/seszele64/analyze-git-projects'
]

if __name__ == "__main__":
    async def main():
        """Analyze repositories using simple schema"""
        try:
            analyzer = GitHubMCAnalyzer()
            
            console.print("[bold]Testing GitHub MCP connection...[/bold]")
            if await analyzer.test_connection():
                console.print(f"\n[bold]Analyzing {len(REPOS_TO_ANALYZE)} repositories:[/bold]")
                
                for repo_url in REPOS_TO_ANALYZE:
                    try:
                        console.print(f"\n[bold cyan]Analyzing {repo_url}[/bold cyan]")
                        
                        result = await analyzer.analyze_repository(repo_url)
                        console.print(f"[green]Analysis complete for {repo_url}[/green]")
                        console.print(f"[blue]Project:[/blue] {result}")
                        # save result as json file
                        save_path = 'data/projects'
                        result_file = f"analysis_{re.sub(r'[^\w]', '_', repo_url)}.json"
                        with open(os.path.join(save_path, result_file), 'w') as f:
                            f.write(result.model_dump_json(indent=2))
                        console.print(f"[green]Results saved to {result_file}[/green]")

                        
                    except Exception as e:
                        console.print(f"[yellow]Error analyzing {repo_url}: {str(e)}[/yellow]")
                        
                console.print("\n[bold green]Simple analysis complete![/bold green]")
            else:
                console.print("[red]Cannot proceed without MCP connection[/red]")
                
        except Exception as e:
            console.print(f"[red]Fatal error: {str(e)}[/red]")

    asyncio.run(main())
