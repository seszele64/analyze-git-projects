"""Custom GitHub Agent inheriting from pydantic_ai.Agent."""

import os
import logging
import time
from typing import Optional, Any, List, Type, Dict

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import StructuredTool

from pydantic_ai.mcp import MCPServerStdio

import logfire

from .mcp_server_factory import GitHubMCPServerFactory, create_read_only_server
from .config import GitHubMCPServerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('github_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Configure Logfire (defaults to console output or cloud if token provided)
logfire.configure(scrubbing=False)


# Capture full HTTP request/response (including headers and body)
logfire.instrument_httpx(capture_all=True)

class GitHubAgent:
    """GitHub repository analysis agent using LangChain.
    
    WHY THIS EXISTS: Provides structured GitHub analysis through LangChain
    with type-safe inputs/outputs and configurable tools.
    
    RESPONSIBILITY: Orchestrates LangChain components for repository analysis
    DOES: Prompt engineering, tool management, structured output parsing
    DOES NOT: Direct GitHub API calls (handled by MCP tools)
    """

    system_prompt: str = \
    """
    You are a GitHub repository analysis expert. Your job is to analyze GitHub repositories and provide insights about their structure, technologies and development activity.
    """
    
    def __init__(
        self,
        system_prompt: Optional[str] = system_prompt,
        output_type: Optional[Type[Any]] = None,
        model_name: Optional[str] = None,
        llm_provider: Optional[str] = None,
        mcp_servers: Optional[List[MCPServerStdio]] = None,  # LangChain tools
        **kwargs: Any
    ):
        """
        Initialize GitHubAgent with enhanced configuration options.
        
        Args:
            system_prompt: Custom system prompt for the agent
            output_type: Output type for structured responses
            model_name: OpenAI model name to use
            mcp_servers: MCP servers to include
            **kwargs: Additional configuration arguments
        """
        start_time = time.time()
        logger.info("Initializing GitHubAgent...")
        logger.debug(f"GitHubAgent.__init__ parameters: system_prompt={system_prompt is not None}, result_type={output_type}, model_name={model_name}")
        
        # Create model using the property getter
        logger.info(f"Initializing LangChain model: {model_name}")
        self.system_prompt = system_prompt or self.system_prompt
        
        # Initialize core components with strong typing
        self.llm: BaseChatModel = ChatOpenAI(
            model=model_name,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=kwargs.get("base_url", "https://openrouter.ai/api/v1"),
            temperature=0.7
        )
        
        # Convert MCP servers to LangChain tools
        self.tools: List[StructuredTool] = [
            self._create_mcp_tool(server)  # type: ignore
            for server in (mcp_servers or [])
        ] if mcp_servers else []

        # Configure prompt engineering
        self.system_prompt_template = SystemMessagePromptTemplate.from_template(
            template=system_prompt or self.system_prompt,
            input_types={"query": str}
        )
        
        # Set up structured output parsing
        self.output_parser = PydanticOutputParser(pydantic_object=output_type)
        
        # Full prompt chain
        self.prompt = ChatPromptTemplate.from_messages([
            self.system_prompt_template,
            HumanMessagePromptTemplate.from_template("{query}\n{format_instructions}"),
        ]).partial(
            format_instructions=self.output_parser.get_format_instructions()
        )

        logger.debug("LangChain components initialized successfully")
        
        # Remove parent class initialization
        init_time = time.time() - start_time
        logger.info(f"GitHubAgent initialized successfully in {init_time:.2f} seconds")

    def run_sync(self, user_prompt: str) -> Any:
        """Execute the agent synchronously with proper LangChain integration.
        
        WHY THIS EXISTS: Provides a clean interface for synchronous execution
        RESPONSIBILITY: Orchestrates prompt formatting, LLM invocation, and output parsing
        """
        formatted_prompt = self.prompt.format_prompt(query=user_prompt)
        response = self.llm.invoke(formatted_prompt.to_messages())
        return self.output_parser.parse(response.content)

    def _create_mcp_tool(self, server: Any) -> StructuredTool:
        """Convert MCP server to LangChain tool with type safety.
        
        WHY THIS EXISTS: Bridges legacy MCP servers to LangChain's tool interface
        RESPONSIBILITY: Standardize tool inputs/outputs while preserving functionality
        """
        """Convert MCP server to LangChain tool with fallback values."""
        return StructuredTool(
            name=getattr(server, 'name', 'mcp_server'),
            description=getattr(server, 'description', f"Tool for {getattr(server, 'name', 'MCP')} operations"),
            func=lambda *args, **kwargs: server.run(*args, **kwargs),  # Proper callable wrapper
            args_schema=getattr(server, 'args_schema', None)
        )

    def update_github_config(self, config: GitHubMCPServerConfig) -> None:
        """Update GitHub MCP server configuration."""
        self._github_config = config
        # Reset mcp_servers to force recreation with new config
        if hasattr(self, '_mcp_servers'):
            delattr(self, '_mcp_servers')
        logger.info("GitHub MCP server configuration updated")

    def update_github_config_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update GitHub MCP server configuration from dictionary."""
        config = GitHubMCPServerConfig(**config_dict)
        self.update_github_config(config)
    
    def get_current_config(self) -> Optional[GitHubMCPServerConfig]:
        """Get the current GitHub MCP server configuration."""
        return self._github_config