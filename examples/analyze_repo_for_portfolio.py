import os
from dotenv import load_dotenv

from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic_ai.usage import UsageLimits

from analyze_git_projects.agent import GitHubAgent
from analyze_git_projects.mcp_server_factory import create_read_only_server


load_dotenv()

# Create MCP server from configuration
mcp_server = create_read_only_server(github_pat=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""))

prompt_template = PromptTemplate(
    input_variables=["repo_url"],
    template="Using GitHub MCP, analyze this repository for resume portfolio: {repo_url}\n\n"
                "Key files to examine: README, main source files, requirements.txt\n"
                "Extract and synthesize:\n"
              "**Tech Analysis:** Primary languages, frameworks, dependencies from package files\n"
              "**Project Metrics:** Commit frequency, file structure complexity, contributor activity\n"
              "**Code Quality:** README quality, documentation, code organization patterns\n"
              "**Standout Elements:** Unique features, problem-solving approaches, technical challenges solved\n\n"
              "Format as:\n"
              "**[Project Name]** | [Primary Tech Stack]\n"
              "*[Compelling 2-line description highlighting impact/complexity]*\n"
              "• [Technical achievement with context]\n"
              "• [Problem solved or skill demonstrated]\n"
              "• [Quantified impact: commits/features/performance]\n\n"
              "{format_instructions}"
              "Max 150 words per repo."
)

from pydantic import BaseModel, Field


class ProjectAnalysis(BaseModel):
    
    project_name: str = Field(
        None,
        description="Name of the project, take it from repo url"
    )
    primary_tech_stack: List[str] = Field(
        None,
        description="Primary technologies used in the project"
    )
    description: str = Field(
        None,
        description="Brief description of the project"
    )
    technical_achievements: List[str] = Field(
        None,
        description="List of technical achievements in the project"
    )
    problems_solved: List[str] = Field(
        None,
        description="List of problems solved by the project"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed=True


parser = JsonOutputParser(pydantic_object=ProjectAnalysis)
prompt_template = PromptTemplate(
    input_variables=["repo_url"],
    template="Read the file at {repo_url} and provide language and framework information. {format_instructions}",
    output_parser=parser,
    partial_variables={"format_instructions": parser.get_format_instructions()}
)


agent1 = GitHubAgent(
    model_name="google/gemini-2.5-flash-lite",
    system_prompt="You are helpful assistant that reads and analyzes GitHub files.",
    mcp_servers=[mcp_server],
    llm_provider='openrouter',
    retries=5,  # Add this
)

print("✅ Typed configuration system ready!")
response = agent1.run_sync(
    user_prompt=prompt_template.format(repo_url="https://github.com/johnbalvin/pyairbnb"),
    output_type=ProjectAnalysis
)

print("Response:", response)
print("Response type:", type(response))