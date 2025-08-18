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
from typing import List, Dict, Optional
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from analyze_git_projects.agent import GitHubAgent
from analyze_git_projects.mcp_server_factory import create_read_only_server

# Load environment variablest
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('documentation_analysis.log')
    ]
)
logger = logging.getLogger(__name__)


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
    
    def __init__(self, github_pat: str):
        """
        Initialize the documentation analyzer.
        
        Args:
            github_pat: GitHub Personal Access Token for API access
        """
        self.github_pat = github_pat
        self.mcp_server = None
        self.agent = None
        self._setup_components()
    
    def _setup_components(self) -> None:
        """Initialize MCP server and GitHub agent."""
        try:
            logger.info("Setting up MCP server...")
            self.mcp_server = create_read_only_server(github_pat=self.github_pat)
            
            logger.info("Initializing GitHub agent...")
            self.agent = GitHubAgent(
                model_name="google/gemini-2.5-flash-lite",
                system_prompt="""You are an expert technical documentation analyst. 
Your role is to thoroughly analyze GitHub repository documentation and provide structured insights.

Focus on:
1. Identifying all documentation files (README, docs, guides)
2. Extracting key technical information
3. Summarizing setup and usage instructions
4. Identifying missing documentation areas
5. Providing actionable insights for documentation improvement""",
                output_type=DocumentationAnalysis,
                mcp_servers=[self.mcp_server],
                llm_provider='openrouter'
            )
            
            logger.info("Components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def analyze_repository(self, repo_url: str) -> DocumentationAnalysis:
        """
        Analyze documentation for a single repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            DocumentationAnalysis: Structured analysis results
        """
        logger.info(f"Analyzing repository: {repo_url}")
        
        # Create prompt template
        parser = JsonOutputParser(pydantic_object=DocumentationAnalysis)
        
        prompt_template = PromptTemplate(
            input_variables=["repo_url"],
            template="""Analyze this GitHub repository for resume content: {repo_url}

Focus on extracting resume-relevant information:

1. **Project Overview**: What does this project do and who is it for?
2. **Technical Stack**: List all technologies, languages, frameworks, databases, cloud services
3. **Project Scale**: Is this personal, team-based, or enterprise? How many users?
4. **Key Achievements**: What problems were solved? Any quantifiable results?
5. **Technical Challenges**: What complex technical problems were overcome?
6. **Business Value**: What business need does this address?
7. **Notable Features**: What makes this project technically interesting?
8. **Resume Bullets**: Create 3-5 concise, impactful bullet points for a resume

Be specific and use action verbs. Focus on impact and technical depth.

{format_instructions}""",
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        # Create and execute chain
        chain = prompt_template | self.agent.llm | parser
        
        try:
            result = chain.invoke({"repo_url": repo_url})
            logger.info(f"Analysis completed for {repo_url}")
            
            # Handle both dict and Pydantic object responses
            if isinstance(result, dict):
                # Convert dict to Pydantic object
                return DocumentationAnalysis(**result)
            else:
                # Already a Pydantic object
                return result
            
        except Exception as e:
            logger.error(f"Analysis failed for {repo_url}: {e}")
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
                logger.info(f"Successfully analyzed {repo_url}")
                
            except Exception as e:
                logger.error(f"Failed to analyze {repo_url}: {e}")
                # Create error result
                error_analysis = DocumentationAnalysis(
                    repo_url=repo_url,
                    repo_name=repo_url.split('/')[-1],
                    project_summary=f"Analysis failed: {str(e)}",
                    technical_overview="Unable to analyze due to error",
                    documentation_score=0.0
                )
                results[repo_url] = error_analysis
        
        return results


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
        logger.error("GITHUB_PERSONAL_ACCESS_TOKEN environment variable not set")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        analyzer = DocumentationAnalyzer(github_pat)
        
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
        else:
            for repo_url, analysis in results.items():
                print(format_analysis_output(analysis))
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()