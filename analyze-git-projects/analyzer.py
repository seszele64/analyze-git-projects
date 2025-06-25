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

from .models import AnalysisResults, RepositoryInfo, TechnologyStack, ProjectComplexity, CodeQualityMetrics

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
                    
                    # Generate structured analysis
                    console.print("[blue]Generating structured analysis...[/blue]")
                    analysis_prompt = self._build_structured_analysis_prompt(repo_url, results)
                    
                    analysis_result = await self.agent.run(analysis_prompt)
                    
                    # Parse the AI response and populate structured fields
                    await self._parse_and_populate_analysis(analysis_result.output, results)
                    
                    progress.update(task, completed=True)
                    
            except Exception as e:
                results.error = str(e)
                console.print(f"[red]Error analyzing repository: {str(e)}[/red]")
                import traceback
                console.print(f"[red]Full traceback: {traceback.format_exc()}[/red]")
                progress.update(task, completed=True)
            
            return results
    
    def _build_structured_analysis_prompt(self, repo_url: str, results: AnalysisResults) -> str:
        """Build structured analysis prompt"""
        return f"""
        Analyze the GitHub repository at {repo_url} based on the following information:
        
        Repository Structure:
        {results.structure or 'No structure information available'}
        
        Important Files Content:
        {results.files.get('content', 'No files information available') if results.files else 'No files information available'}
        
        Please provide a structured analysis in the following format. Be specific and extract actual information from the repository:

        **TECHNOLOGY STACK:**
        Primary Language: [main programming language]
        Languages: [comma-separated list of all languages]
        Frameworks: [comma-separated list of frameworks/libraries]
        Tools: [development tools, build tools, etc.]
        Databases: [database systems if any]
        Deployment Tools: [Docker, Kubernetes, etc.]
        Testing Frameworks: [testing tools/frameworks]

        **PROJECT PURPOSE:**
        [Brief 1-2 sentence description of what the project does]

        **ARCHITECTURE TYPE:**
        [e.g., MVC, Pipeline, Microservices, Monolithic, etc.]

        **KEY FEATURES:**
        - [Feature 1]
        - [Feature 2]
        - [Feature 3]

        **DEPENDENCIES:**
        - [External service/library 1]
        - [External service/library 2]

        **CODE QUALITY:**
        Has Tests: [Yes/No]
        Has Documentation: [Yes/No]
        Has CI/CD: [Yes/No]
        Has Linting: [Yes/No]
        Has Type Checking: [Yes/No]
        Test Coverage: [High/Medium/Low/Unknown]
        Documentation Quality: [Excellent/Good/Fair/Poor]
        Code Organization: [Well-structured/Moderate/Needs improvement]

        **PROJECT COMPLEXITY:**
        Level: [Beginner/Intermediate/Advanced]
        Score: [1-10]
        Complexity Factors:
        - [Factor 1]
        - [Factor 2]

        **DEVELOPMENT PRACTICES:**
        - [Practice 1]
        - [Practice 2]

        Provide specific, factual information based on the actual repository content.
        """
    
    async def _parse_and_populate_analysis(self, analysis_text: str, results: AnalysisResults):
        """Parse AI analysis and populate structured fields"""
        try:
            # Extract technology stack
            tech_stack = TechnologyStack()
            
            # Parse primary language
            primary_lang_match = re.search(r'Primary Language:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if primary_lang_match:
                tech_stack.primary_language = primary_lang_match.group(1).strip()
            
            # Parse languages
            languages_match = re.search(r'Languages:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if languages_match:
                tech_stack.languages = [lang.strip() for lang in languages_match.group(1).split(',')]
            
            # Parse frameworks
            frameworks_match = re.search(r'Frameworks:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if frameworks_match:
                tech_stack.frameworks = [fw.strip() for fw in frameworks_match.group(1).split(',')]
            
            # Parse tools
            tools_match = re.search(r'Tools:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if tools_match:
                tech_stack.tools = [tool.strip() for tool in tools_match.group(1).split(',')]
            
            # Parse databases
            databases_match = re.search(r'Databases:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if databases_match:
                tech_stack.databases = [db.strip() for db in databases_match.group(1).split(',')]
            
            # Parse deployment tools
            deployment_match = re.search(r'Deployment Tools:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if deployment_match:
                tech_stack.deployment_tools = [tool.strip() for tool in deployment_match.group(1).split(',')]
            
            # Parse testing frameworks
            testing_match = re.search(r'Testing Frameworks:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if testing_match:
                tech_stack.testing_frameworks = [fw.strip() for fw in testing_match.group(1).split(',')]
            
            results.technology_stack = tech_stack
            
            # Extract project purpose
            purpose_match = re.search(r'\*\*PROJECT PURPOSE:\*\*\s*([^\n]+(?:\n[^*]+)*)', analysis_text, re.IGNORECASE)
            if purpose_match:
                results.project_purpose = purpose_match.group(1).strip()
            
            # Extract architecture type
            arch_match = re.search(r'\*\*ARCHITECTURE TYPE:\*\*\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if arch_match:
                results.architecture_type = arch_match.group(1).strip()
            
            # Extract key features
            features_section = re.search(r'\*\*KEY FEATURES:\*\*(.*?)(?=\*\*|$)', analysis_text, re.IGNORECASE | re.DOTALL)
            if features_section:
                features = re.findall(r'-\s*([^\n]+)', features_section.group(1))
                results.key_features = [feature.strip() for feature in features]
            
            # Extract dependencies
            deps_section = re.search(r'\*\*DEPENDENCIES:\*\*(.*?)(?=\*\*|$)', analysis_text, re.IGNORECASE | re.DOTALL)
            if deps_section:
                deps = re.findall(r'-\s*([^\n]+)', deps_section.group(1))
                results.dependencies = [dep.strip() for dep in deps]
            
            # Extract code quality
            code_quality = CodeQualityMetrics()
            
            has_tests_match = re.search(r'Has Tests:\s*(Yes|No)', analysis_text, re.IGNORECASE)
            if has_tests_match:
                code_quality.has_tests = has_tests_match.group(1).lower() == 'yes'
            
            has_docs_match = re.search(r'Has Documentation:\s*(Yes|No)', analysis_text, re.IGNORECASE)
            if has_docs_match:
                code_quality.has_documentation = has_docs_match.group(1).lower() == 'yes'
            
            has_cicd_match = re.search(r'Has CI/CD:\s*(Yes|No)', analysis_text, re.IGNORECASE)
            if has_cicd_match:
                code_quality.has_ci_cd = has_cicd_match.group(1).lower() == 'yes'
            
            has_linting_match = re.search(r'Has Linting:\s*(Yes|No)', analysis_text, re.IGNORECASE)
            if has_linting_match:
                code_quality.has_linting = has_linting_match.group(1).lower() == 'yes'
            
            has_typing_match = re.search(r'Has Type Checking:\s*(Yes|No)', analysis_text, re.IGNORECASE)
            if has_typing_match:
                code_quality.has_type_checking = has_typing_match.group(1).lower() == 'yes'
            
            test_coverage_match = re.search(r'Test Coverage:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if test_coverage_match:
                code_quality.test_coverage = test_coverage_match.group(1).strip()
            
            doc_quality_match = re.search(r'Documentation Quality:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if doc_quality_match:
                code_quality.documentation_quality = doc_quality_match.group(1).strip()
            
            code_org_match = re.search(r'Code Organization:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if code_org_match:
                code_quality.code_organization = code_org_match.group(1).strip()
            
            results.code_quality = code_quality
            
            # Extract project complexity
            complexity_level_match = re.search(r'Level:\s*([^\n]+)', analysis_text, re.IGNORECASE)
            if complexity_level_match:
                level = complexity_level_match.group(1).strip()
                
                score_match = re.search(r'Score:\s*(\d+)', analysis_text, re.IGNORECASE)
                score = int(score_match.group(1)) if score_match else None
                
                factors_section = re.search(r'Complexity Factors:(.*?)(?=\*\*|$)', analysis_text, re.IGNORECASE | re.DOTALL)
                factors = []
                if factors_section:
                    factors = re.findall(r'-\s*([^\n]+)', factors_section.group(1))
                    factors = [factor.strip() for factor in factors]
                
                results.project_complexity = ProjectComplexity(
                    level=level,
                    score=score,
                    factors=factors
                )
            
            # Extract development practices
            practices_section = re.search(r'\*\*DEVELOPMENT PRACTICES:\*\*(.*?)(?=\*\*|$)', analysis_text, re.IGNORECASE | re.DOTALL)
            if practices_section:
                practices = re.findall(r'-\s*([^\n]+)', practices_section.group(1))
                results.development_practices = [practice.strip() for practice in practices]
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse all analysis fields: {str(e)}[/yellow]")
            # Set basic fallback values
            results.technology_stack = TechnologyStack()
            results.project_complexity = ProjectComplexity(level="Unknown")
            results.code_quality = CodeQualityMetrics()