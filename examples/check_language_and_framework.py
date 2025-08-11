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
    """Example output type for GitHub analysis."""
    language: str
    framework: str

# implement langchain prompt
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser(pydantic_object=SimpleProject)
prompt_template = PromptTemplate(
    input_variables=["file_url"],
    template="Read the file at {file_url} and provide language and framework information. {format_instructions}",
    output_parser=parser,
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

agent1 = GitHubAgent(
    model_name="google/gemini-2.5-flash-lite",
    system_prompt="You are helpful assistant that reads and analyzes GitHub files.",
    mcp_servers=[mcp_server],
    llm_provider='openrouter'
)

print("✅ Typed configuration system ready!")
response = agent1.run_sync(
    user_prompt=prompt_template.format(file_url="https://github.com/ranaroussi/yfinance/blob/main/tests/test_cache.py"),
    output_type=SimpleProject
)

print("Response:", response)
print(response.output)
print("Response type:", type(response))

print("language:", response.output.language)
print("framework:", response.output.framework)