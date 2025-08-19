#!/usr/bin/env python3
"""
Resume Project Analyzer using GitHub MCP Server.

WHY THIS EXISTS: Analyzes GitHub repositories specifically for resume content,
extracting technical skills, project impact, and achievements for resume use.

RESPONSIBILITY:
- Analyze projects for resume-relevant technical information
- Extract technologies, frameworks, and tools used
- Identify project impact and business value
- Generate resume-ready bullet points
- Provide project summaries suitable for resume sections

DOES NOT:
- Modify repository content
- Generate false achievements
- Include non-technical information
"""

import os
import sys
import argparse
import logging
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from analyze_git_projects.agent import GitHubAgent

# Load environment variablest
load_dotenv()

# Configure logging when module is imported
def _setup_logging():
    """Set up logging configuration for the module."""
    import os
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file_path = os.path.join(project_root, 'documentation_analysis.log')
    
    # Create a specific logger for this module
    logger = logging.getLogger('documentation_analysis')
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Set up logging on module import
logger = _setup_logging()


class DocumentationAnalysis(BaseModel):
    """Resume-focused analysis of GitHub repositories."""
    
    repo_url: str = Field(..., description="Full GitHub repository URL")
    repo_name: str = Field(..., description="Repository name extracted from URL")
    
    # Resume-focused project info
    project_title: str = Field(..., description="Clean project name for resume")
    project_category: str = Field(..., description="Category: Web App, API, Tool, Library, etc.")
    project_summary: str = Field(..., description="One-sentence impact-focused description")
    
    # Technical skills and tools
    primary_language: str = Field(..., description="Main programming language")
    technologies: List[str] = Field(default_factory=list, description="Technologies, frameworks, tools")
    databases: List[str] = Field(default_factory=list, description="Databases and data stores")
    cloud_services: List[str] = Field(default_factory=list, description="Cloud platforms and services")
    technical_skills: List[str] = Field(default_factory=list, description="All technical skills demonstrated")
    
    # Project scale and complexity
    project_scale: str = Field(..., description="Scale: Personal, Team, Enterprise")
    user_impact: str = Field(..., description="Who uses this and scale (e.g., '1000+ daily users')")
    code_complexity: str = Field(..., description="Complexity level: Simple, Moderate, Complex")
    
    # Achievements and impact
    key_achievements: List[str] = Field(default_factory=list, description="Quantifiable achievements")
    technical_challenges: List[str] = Field(default_factory=list, description="Complex problems solved")
    business_value: str = Field(..., description="Business impact or problem solved")
    
    # Resume-ready content
    resume_bullet_points: List[str] = Field(default_factory=list, description="Ready-to-use resume bullets")
    notable_features: List[str] = Field(default_factory=list, description="Standout technical features")
    
    # Original documentation info (for reference)
    documentation_files: List[str] = Field(
        default_factory=list,
        description="List of documentation files found"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Project dependencies mentioned in docs"
    )


class DocumentationAnalyzer:
    """Main class for analyzing GitHub repository documentation."""
    
    def __init__(self, github_pat: str, config_file: str = "github_mcp.json"):
        """
        Initialize the documentation analyzer.
        
        Args:
            github_pat: GitHub Personal Access Token for API access
            config_file: Path to MCP configuration JSON file
        """
        self.github_pat = github_pat
        self.config_file = config_file
        self.agent = None
        self.logger = logging.getLogger(__name__)
        self._setup_components()
    
    def _setup_components(self) -> None:
        """Initialize GitHub agent with MCP configuration."""
        try:
            self.logger.info("Initializing GitHub agent...")
            
            # Update the config file with the provided GitHub PAT
            self._update_config_file()
            
            self.agent = GitHubAgent(
                model_name="google/gemini-2.5-flash-lite",
                system_prompt="""You are an expert technical documentation analyst specializing in resume content extraction.
Your role is to thoroughly analyze GitHub repository documentation and provide structured insights for resume use.

Focus on:
1. **Technical Stack**: Identify all technologies, languages, frameworks, databases, cloud services
2. **Project Scale**: Determine if personal, team-based, or enterprise level
3. **Key Achievements**: Extract quantifiable results and impact metrics
4. **Technical Challenges**: Identify complex problems solved
5. **Business Value**: Understand what business need this addresses
6. **Notable Features**: Highlight technically interesting aspects
7. **Resume Content**: Generate concise, impactful bullet points

Always use your GitHub tools to:
- Read actual file contents (README, package.json, requirements.txt, etc.)
- Analyze repository structure and organization
- Extract real technical information, not assumptions
- Identify actual technologies and frameworks used

Provide detailed, factual analysis based on actual repository content.""",
                config_file=self.config_file,
                max_steps=30
            )
            
            self.logger.info("Components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _update_config_file(self) -> None:
        """Update the MCP config file with the provided GitHub PAT."""
        try:
            # Read existing config
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Update the GitHub PAT
            if 'mcpServers' in config and 'github' in config['mcpServers']:
                config['mcpServers']['github']['env']['GITHUB_PERSONAL_ACCESS_TOKEN'] = self.github_pat
            
            # Write back to file
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info(f"Updated {self.config_file} with provided GitHub PAT")
            
        except Exception as e:
            self.logger.warning(f"Failed to update config file: {e}")
            # Continue without updating - agent might still work
    
    def analyze_repository(self, repo_url: str) -> DocumentationAnalysis:
        """
        Analyze documentation for a single repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            DocumentationAnalysis: Structured analysis results
        """
        self.logger.info(f"Analyzing repository: {repo_url}")
        
        try:
            # Parse owner and repo from URL
            url_parts = repo_url.strip().rstrip('/').split('/')
            if len(url_parts) < 2:
                raise ValueError(f"Invalid GitHub URL format: {repo_url}")
            
            owner = url_parts[-2]
            repo_name = url_parts[-1]
            
            self.logger.info(f"Extracted owner: {owner}, repo: {repo_name}")
            
            # Create comprehensive analysis prompt
            analysis_prompt = f"""Analyze the GitHub repository {repo_url} ({owner}/{repo_name}) for resume content extraction.

Please use your GitHub tools to:

1. **Explore Repository Structure**: List all directories and files, focusing on configuration files
2. **Read Key Files**: Examine README.md, package.json, requirements.txt, pyproject.toml, Cargo.toml, go.mod, Dockerfile, etc.
3. **Analyze Source Code**: Identify main programming languages and frameworks used
4. **Extract Technical Details**: Determine technologies, databases, cloud services, architecture patterns

Based on your analysis, provide a detailed JSON response with the following structure:

{{
  "repo_url": "{repo_url}",
  "repo_name": "{repo_name}",
  "project_title": "Clean project name suitable for resume",
  "project_category": "Category like Web App, API, Library, Tool, etc.",
  "project_summary": "One impactful sentence describing what this project does and its value",
  "primary_language": "Main programming language",
  "technologies": ["list", "of", "technologies", "and", "frameworks"],
  "databases": ["list", "of", "databases", "used"],
  "cloud_services": ["cloud", "platforms", "or", "services"],
  "technical_skills": ["comprehensive", "list", "of", "technical", "skills", "demonstrated"],
  "project_scale": "Personal/Team/Enterprise - assess complexity and scope",
  "user_impact": "Description of who uses this and scale (e.g., '1000+ users')",
  "code_complexity": "Simple/Moderate/Complex - technical complexity assessment",
  "key_achievements": ["quantifiable", "achievements", "and", "impacts"],
  "technical_challenges": ["complex", "technical", "problems", "solved"],
  "business_value": "What business problem this solves or value it provides",
  "resume_bullet_points": ["3-5", "concise", "impactful", "bullet", "points", "for", "resume"],
  "notable_features": ["standout", "technical", "features", "or", "innovations"],
  "documentation_files": ["README.md", "other", "docs", "found"],
  "dependencies": ["key", "project", "dependencies"]
}}

Be specific and factual based on actual file contents. Use action verbs and quantifiable metrics where possible."""

            # Execute analysis using the agent
            result = self.agent.run_sync(analysis_prompt)
            
            # Parse the JSON response
            parser = JsonOutputParser(pydantic_object=DocumentationAnalysis)
            
            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_result = json.loads(json_str)
                else:
                    # If no JSON found, try the whole response
                    parsed_result = json.loads(result)
                
                # Convert to DocumentationAnalysis object
                analysis = DocumentationAnalysis(**parsed_result)
                
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to parse JSON response: {e}")
                self.logger.warning(f"Raw response: {result[:500]}...")
                
                # Create a fallback analysis with what we can extract
                analysis = DocumentationAnalysis(
                    repo_url=repo_url,
                    repo_name=repo_name,
                    project_title=repo_name.replace('-', ' ').replace('_', ' ').title(),
                    project_category="Software Project",
                    project_summary=f"GitHub repository: {repo_name}",
                    primary_language="Unknown",
                    project_scale="Unknown",
                    user_impact="Analysis incomplete",
                    code_complexity="Unknown",
                    business_value=f"Repository analysis failed: {str(e)}"
                )
            
            self.logger.info(f"Analysis completed for {repo_url}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Analysis failed for {repo_url}: {e}")
            raise
    
    def analyze_multiple_repos(self, repo_urls: List[str]) -> Dict[str, DocumentationAnalysis]:
        """
        Analyze documentation for multiple repositories.
        
        Args:
            repo_urls: List of GitHub repository URLs
            
        Returns:
            Dict mapping repository URLs to their analysis results
        """
        results = {}
        
        for repo_url in repo_urls:
            try:
                analysis = self.analyze_repository(repo_url)
                results[repo_url] = analysis
                self.logger.info(f"Successfully analyzed {repo_url}")
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {repo_url}: {e}")
                # Create error result
                error_analysis = DocumentationAnalysis(
                    repo_url=repo_url,
                    repo_name=repo_url.split('/')[-1],
                    project_title=f"Error: {repo_url.split('/')[-1]}",
                    project_category="Analysis Failed",
                    project_summary=f"Analysis failed: {str(e)}",
                    primary_language="Unknown",
                    project_scale="Unknown",
                    user_impact="Analysis failed",
                    code_complexity="Unknown",
                    business_value=f"Unable to analyze due to error: {str(e)}"
                )
                results[repo_url] = error_analysis
        
        return results

    def close(self) -> None:
        """Clean up resources."""
        if self.agent:
            self.agent.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()


def format_analysis_output(analysis: DocumentationAnalysis) -> str:
    """Format analysis results specifically for resume use."""
    
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"🎯 RESUME ANALYSIS: {analysis.project_title}")
    output.append(f"🔗 {analysis.repo_url}")
    output.append(f"{'='*70}")
    
    output.append(f"\n📊 PROJECT OVERVIEW:")
    output.append(f"   Category: {analysis.project_category}")
    output.append(f"   Scale: {analysis.project_scale}")
    output.append(f"   Impact: {analysis.user_impact}")
    output.append(f"   Summary: {analysis.project_summary}")
    
    output.append(f"\n🛠️ TECHNICAL STACK:")
    output.append(f"   Primary Language: {analysis.primary_language}")
    if analysis.technologies:
        output.append(f"   Technologies: {', '.join(analysis.technologies)}")
    if analysis.databases:
        output.append(f"   Databases: {', '.join(analysis.databases)}")
    if analysis.cloud_services:
        output.append(f"   Cloud: {', '.join(analysis.cloud_services)}")
    
    output.append(f"\n💡 KEY ACHIEVEMENTS:")
    for achievement in analysis.key_achievements:
        output.append(f"   • {achievement}")
    
    if analysis.technical_challenges:
        output.append(f"\n🔧 TECHNICAL CHALLENGES:")
        for challenge in analysis.technical_challenges:
            output.append(f"   • {challenge}")
    
    output.append(f"\n💼 BUSINESS VALUE:")
    output.append(f"   {analysis.business_value}")
    
    if analysis.notable_features:
        output.append(f"\n⭐ NOTABLE FEATURES:")
        for feature in analysis.notable_features:
            output.append(f"   • {feature}")
    
    output.append(f"\n📝 RESUME BULLET POINTS:")
    for i, bullet in enumerate(analysis.resume_bullet_points, 1):
        output.append(f"   {i}. {bullet}")
    
    output.append(f"\n📋 TECHNICAL SKILLS DEMONSTRATED:")
    skills_text = ', '.join(analysis.technical_skills[:8])
    if len(analysis.technical_skills) > 8:
        skills_text += f", +{len(analysis.technical_skills) - 8} more"
    output.append(f"   {skills_text}")
    
    return "\n".join(output)


def main():
    """Main entry point for the documentation analyzer."""
    
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repository documentation using MCP server"
    )
    parser.add_argument(
        'repos',
        nargs='+',
        help='GitHub repository URLs to analyze'
    )
    parser.add_argument(
        '--config',
        default='github_mcp.json',
        help='MCP configuration file path (default: github_mcp.json)'
    )
    parser.add_argument(
        '--output',
        choices=['console', 'json'],
        default='console',
        help='Output format (default: console)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get GitHub token
    github_pat = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not github_pat:
        logging.getLogger(__name__).error("GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        analyzer = DocumentationAnalyzer(github_pat, config_file=args.config)
        
        # Analyze repositories
        results = analyzer.analyze_multiple_repos(args.repos)
        
        # Output results
        if args.output == 'json':
            import json
            
            def serialize_analysis(analysis):
                """Convert analysis to serializable dict."""
                if hasattr(analysis, 'dict'):
                    return analysis.dict()
                elif isinstance(analysis, dict):
                    return analysis
                else:
                    # Handle Pydantic objects
                    return {k: v for k, v in analysis.__dict__.items() if not k.startswith('_')}
            
            print(json.dumps(
                {url: serialize_analysis(analysis) for url, analysis in results.items()},
                indent=2,
                default=str
            ))
            # for each analysis, save to file, use url
            for url, analysis in results.items():
                with open(f"{url.replace('/', '_')}_analysis.json", 'w') as f:
                    json.dump(serialize_analysis(analysis), f, indent=2)
        else:
            for repo_url, analysis in results.items():
                print(format_analysis_output(analysis))
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()