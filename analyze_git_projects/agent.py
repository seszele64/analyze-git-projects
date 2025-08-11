"""Custom GitHub Agent inheriting from pydantic_ai.Agent."""

import os
import logging
import time
from typing import Optional, Any, List, Type, Dict

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
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

class GitHubAgent(Agent):
    """GitHub analysis agent inheriting from pydantic_ai.Agent."""

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
        mcp_servers: Optional[List[MCPServerStdio]] = None,
        **kwargs
    ):
        """
        Initialize GitHubAgent with enhanced configuration options.
        
        Args:
            system_prompt: Custom system prompt for the agent
            output_type: Output type for structured responses
            model_name: OpenAI model name to use
            mcp_servers: MCP servers to include
            **kwargs: Additional arguments passed to parent Agent
        """
        start_time = time.time()
        logger.info("Initializing GitHubAgent...")
        logger.debug(f"GitHubAgent.__init__ parameters: system_prompt={system_prompt is not None}, result_type={output_type}, model_name={model_name}")
        
        # Create model using the property getter
        logger.info(f"Creating OpenAI model with provider: {model_name}")
        model = OpenAIModel(
            model_name,
            provider=llm_provider
        )
        logger.debug("OpenAI model created successfully")
        
        # Store additional parameters for reuse
        self._result_type = output_type
        self._model_name = model_name
        self._mcp_servers = mcp_servers

        # Initialize parent Agent
        logger.info("Initializing parent Agent...")
        super().__init__(
            model=model,
            mcp_servers=mcp_servers,
            system_prompt=system_prompt,
            output_type=output_type,
            **kwargs
        )
        
        init_time = time.time() - start_time
        logger.info(f"GitHubAgent initialized successfully in {init_time:.2f} seconds")

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