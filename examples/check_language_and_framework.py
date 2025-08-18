import os
from dotenv import load_dotenv

from analyze_git_projects.agent import GitHubAgent
from analyze_git_projects.mcp_server_factory import create_read_only_server
from pydantic import Field


load_dotenv()

# Create MCP server from configuration
mcp_server = create_read_only_server(github_pat=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""))

from pydantic import BaseModel

class SimpleProject(BaseModel):
    """Example output type for GitHub analysis.
    
    WHY THIS EXISTS: Provides structured analysis results with type safety
    RESPONSIBILITY: Encapsulates language and framework detection results
    """
    language: str = Field(description="Primary programming language used")
    framework: str = Field(description="Main framework/library detected")

agent1 = GitHubAgent(
    model_name="google/gemini-2.5-flash-lite",  # OpenRouter model name format
    system_prompt="Analyze GitHub repositories to detect programming languages and frameworks.",
    mcp_servers=[mcp_server],
    llm_provider='openrouter',
    output_type=SimpleProject,
    base_url="https://openrouter.ai/api/v1",  # Explicit OpenRouter endpoint
    openai_api_key=os.getenv("OPENROUTER_API_KEY")  # Use OpenRouter key
)

print("✅ Typed configuration system ready!")
# Execute the analysis using LangChain's invocation pattern
response = agent1.llm.invoke(
    agent1.prompt.format_prompt(
        query="Analyze the repository at https://github.com/ranaroussi/yfinance/blob/main/tests/test_cache.py"
    )
)
parsed_response = agent1.output_parser.parse(response.content)

print("Response:", response)
print("Response:", parsed_response)
print("Response type:", type(parsed_response))

print("language:", parsed_response.language)
print("framework:", parsed_response.framework)