import asyncio
import os
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import AnalysisResults, RepositoryInfo, TechnologyStack, ProjectComplexity, CodeQualityMetrics, StructuredAnalysis

load_dotenv()
console = Console()


class GitIngestAnalyzer:
    """Repository analyzer using git-ingest MCP server"""
    
    def __init__(self, openrouter_api_key: str = None):
        """
        Initialize the git-ingest analyzer
        
        Args:
            openrouter_api_key: OpenRouter API key for LLM analysis
        """
        self.openrouter_api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        
        if not self.openrouter_api_key:
            console.print("[yellow]Warning: No OpenRouter API key provided. Using dummy model.[/yellow]")
        
        # Initialize git-ingest MCP server using stdio
        try:
            self.git_ingest_server = MCPServerStdio(
                command="uvx",
                args=["--from", "git+https://github.com/adhikasp/mcp-git-ingest", "mcp-git-ingest"]
            )
            console.print("[green]Git-ingest MCP server configured with uvx[/green]")
        except Exception as e:
            console.print(f"[red]Failed to configure git-ingest MCP server: {str(e)}[/red]")
            raise
        
        # Initialize AI model
        if self.openrouter_api_key:
            model = OpenAIModel(
                "google/gemini-2.0-flash-001",
                provider=OpenRouterProvider(api_key=self.openrouter_api_key),
            )
        else:
            model = "google/gemini-2.0-flash-001"
        
        # Initialize agent with the MCP server
        self.agent = Agent(
            model=model,
            mcp_servers=[self.git_ingest_server],
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """
        You are a repository analysis expert. Your job is to analyze code repositories 
        and provide insights about their structure, technologies, and complexity.
        
        When analyzing repositories, use the available MCP tools to:
        - Get directory structure using git_directory_structure
        - Read important files using git_read_important_files
        
        Focus on:
        - Technology stack identification
        - Project architecture patterns
        - Code quality indicators
        - Dependencies and frameworks
        - Development practices
        
        Be thorough but concise in your analysis.
        """
    
    async def test_connection(self) -> bool:
        """Test connection to git-ingest MCP server"""
        try:
            console.print("[blue]Testing git-ingest MCP server connection...[/blue]")
            async with self.agent.run_mcp_servers():
                tools = await self.git_ingest_server.list_tools()
                console.print(f"[green]✅ Git-ingest MCP Server Connected![/green]")
                console.print(f"[blue]Available tools ({len(tools)}):[/blue]")
                for tool in tools:
                    console.print(f"  - [cyan]{tool.name}[/cyan]: {tool.description}")
                return True
        except Exception as e:
            console.print(f"[red]❌ Git-ingest MCP Server Connection Failed: {str(e)}[/red]")
            import traceback
            console.print(f"[red]Full traceback: {traceback.format_exc()}[/red]")
            return False
    
    async def analyze_repository(self, repo_url: str) -> AnalysisResults:
        """
        Analyze a repository using git-ingest MCP server
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            AnalysisResults object containing analysis results
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Analyzing repository: {repo_url}", total=None)
            
            results = AnalysisResults(repo_url=repo_url)
            
            try:
                async with self.agent.run_mcp_servers():
                    # Discover available tools
                    tools = await self.git_ingest_server.list_tools()
                    tool_names = [tool.name for tool in tools]
                    console.print(f"[blue]Available tools: {tool_names}[/blue]")
                    
                    # Get directory structure
                    if 'git_directory_structure' in tool_names:
                        console.print("[blue]Getting repository structure...[/blue]")
                        structure_result = await self.agent.run(
                            f"Use the git_directory_structure tool to get the directory structure of {repo_url}. "
                            f"Show me the file and folder organization of this repository."
                        )
                        results.structure = structure_result.output
                        results.tools_used.append("git_directory_structure")
                    
                    # Read important files
                    if 'git_read_important_files' in tool_names:
                        console.print("[blue]Reading important files...[/blue]")
                        files_result = await self.agent.run(
                            f"Use the git_read_important_files tool to read key files from {repo_url}. "
                            f"Focus on files like README.md, package.json, requirements.txt, pyproject.toml, "
                            f"Dockerfile, and other configuration files that reveal the project's technology stack."
                        )
                        results.files = {"content": files_result.output}
                        results.tools_used.append("git_read_important_files")
                    
                    # Generate structured analysis using Pydantic AI result_type
                    console.print("[blue]Generating structured analysis...[/blue]")
                    
                    # Create a new agent with structured output for analysis
                    analysis_agent = Agent(
                        self.agent.model,
                        mcp_servers=[self.git_ingest_server],
                        result_type=StructuredAnalysis,
                        system_prompt=self._get_structured_analysis_prompt()
                    )
                    
                    analysis_prompt = self._build_structured_analysis_prompt(repo_url, results)
                    
                    analysis_result = await analysis_agent.run(analysis_prompt)
                    
                    # Directly assign structured data from the parsed response
                    structured_analysis = analysis_result.data
                    results.technology_stack = structured_analysis.technology_stack
                    results.project_purpose = structured_analysis.project_purpose
                    results.architecture_type = structured_analysis.architecture_type
                    results.key_features = structured_analysis.key_features
                    results.dependencies = structured_analysis.dependencies
                    results.code_quality = structured_analysis.code_quality
                    results.project_complexity = structured_analysis.project_complexity
                    results.development_practices = structured_analysis.development_practices
                    
                    progress.update(task, completed=True)
                    
            except Exception as e:
                results.error = str(e)
                console.print(f"[red]Error analyzing repository: {str(e)}[/red]")
                import traceback
                console.print(f"[red]Full traceback: {traceback.format_exc()}[/red]")
                progress.update(task, completed=True)
            
            return results
    
    def _get_structured_analysis_prompt(self) -> str:
        """Get the system prompt for structured analysis"""
        return """
        You are a repository analysis expert. Your job is to analyze code repositories 
        and provide structured insights about their architecture, technologies, and complexity.
        
        When analyzing repositories, use the available MCP tools to:
        - Get directory structure using git_directory_structure
        - Read important files using git_read_important_files
        
        Focus on providing accurate, factual information extracted from the actual repository content.
        Fill all fields in the structured response with specific information found in the repository.
        
        Be thorough but concise in your analysis.
        """
    
    def _build_structured_analysis_prompt(self, repo_url: str, results: AnalysisResults) -> str:
        """Build structured analysis prompt for Pydantic AI result_type"""
        return f"""
        Analyze the GitHub repository at {repo_url} based on the following information and provide a comprehensive structured analysis:
        
        Repository Structure:
        {results.structure or 'No structure information available'}
        
        Important Files Content:
        {results.files.get('content', 'No files information available') if results.files else 'No files information available'}
        
        Please analyze this repository and provide structured information about:
        
        1. **Technology Stack**: Identify the primary language, all languages used, frameworks, tools, databases, deployment tools, and testing frameworks based on actual files found.
        
        2. **Project Purpose**: Write a clear, concise description of what this project does based on README and code structure.
        
        3. **Architecture Type**: Determine the architectural pattern (e.g., MVC, Microservices, Pipeline, Monolithic, etc.) from the code organization.
        
        4. **Key Features**: List the main functional features of the project based on the code and documentation.
        
        5. **Dependencies**: Identify external libraries, services, and dependencies from package files and configuration.
        
        6. **Code Quality**: Assess whether the project has tests, documentation, CI/CD, linting, type checking, and estimate the quality levels.
        
        7. **Project Complexity**: Evaluate the complexity level (Beginner/Intermediate/Advanced), assign a score (1-10), and identify complexity factors.
        
        8. **Development Practices**: Identify good development practices observed in the repository.
        
        Base your analysis on the actual repository content provided. Be specific and factual.
        """