"""Custom GitHub Agent using mcp_use for MCP integration."""

import asyncio
import logging
import time
from typing import Optional, Any

from typing import Protocol
from mcp_use import MCPAgent, MCPClient
from dotenv import load_dotenv
from langchain_core.language_models import BaseLanguageModel

# Load environment variables
load_dotenv()

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

class GitHubAgent:
    """GitHub repository analysis agent using mcp_use for MCP integration.
    
    WHY THIS EXISTS: Provides structured GitHub analysis through mcp_use
    with simplified MCP client management and async execution.
    
    RESPONSIBILITY: Orchestrates MCP client and LLM for repository analysis
    DOES: Load MCP config from JSON, manage async execution, provide sync interface
    DOES NOT: LLM configuration (handled externally), Complex tool management (handled by mcp_use)
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        system_prompt: Optional[str] = None,
        config_file: str = "github_mcp.json",
        max_steps: int = 30
    ):
        """
        Initialize GitHubAgent with mcp_use integration.
        
        Args:
            llm: Pre-configured language model instance (required)
            system_prompt: Custom system prompt for the agent
            config_file: Path to MCP configuration JSON file
            max_steps: Maximum steps for agent execution
        """
        start_time = time.time()
        logger.info("Initializing GitHubAgent with mcp_use...")
        
        if llm is None:
            raise ValueError("llm parameter is required")
        
        self.system_prompt = system_prompt or """
        You are a GitHub repository analysis expert. Your job is to analyze GitHub repositories and provide insights about their structure, technologies and development activity.
        """
        
        self.config_file = config_file
        self.max_steps = max_steps
        
        # Initialize MCP client from config file
        self.client = MCPClient.from_config_file(config_file)
        logger.info(f"Loaded MCP client from {config_file}")
        
        # Use provided LLM instance
        self.llm = llm
        logger.info(f"Using provided LLM: {llm.__class__.__name__}")
        
        # Create MCP agent
        self.agent = MCPAgent(
            llm=self.llm,
            client=self.client,
            max_steps=self.max_steps,
            system_prompt=self.system_prompt
        )
        
        init_time = time.time() - start_time
        logger.info(f"GitHubAgent initialized successfully in {init_time:.2f} seconds")

    def run_sync(self, user_prompt: str) -> str:
        """Execute the agent synchronously.
        
        WHY THIS EXISTS: Provides a clean sync interface for async MCP operations
        RESPONSIBILITY: Handle async execution in sync context
        """
        try:
            logger.info(f"Executing agent with prompt: {user_prompt[:100]}...")
            
            # Run the async agent in a sync context
            result = asyncio.run(self._run_async(user_prompt))
            return result
            
        except Exception as e:
            logger.error(f"Error in run_sync: {str(e)}")
            raise

    async def run_async(self, user_prompt: str) -> str:
        """Execute the agent asynchronously.
        
        WHY THIS EXISTS: Provides direct async interface for better performance
        RESPONSIBILITY: Handle async execution directly
        """
        return await self._run_async(user_prompt)

    async def _run_async(self, user_prompt: str) -> str:
        """Internal async execution method."""
        try:
            result = await self.agent.run(user_prompt)
            logger.info("Agent execution completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error in async execution: {str(e)}")
            raise
        finally:
            # Ensure client sessions are properly closed
            await self.client.close_all_sessions()

    def update_config(self, config_file: str) -> None:
        """Update MCP configuration from a new file.
        
        WHY THIS EXISTS: Allows dynamic reconfiguration without recreating agent
        RESPONSIBILITY: Reload MCP client with new configuration
        """
        try:
            logger.info(f"Updating configuration from {config_file}")
            
            # Close existing client sessions
            asyncio.run(self.client.close_all_sessions())
            
            # Load new configuration
            self.client = MCPClient.from_config_file(config_file)
            self.config_file = config_file
            
            # Recreate agent with new client
            self.agent = MCPAgent(
                llm=self.llm,
                client=self.client,
                max_steps=self.max_steps,
                system_prompt=self.system_prompt
            )
            
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            raise

    def get_config_file(self) -> str:
        """Get the current configuration file path."""
        return self.config_file

    def close(self) -> None:
        """Close all MCP client sessions."""
        try:
            asyncio.run(self.client.close_all_sessions())
            logger.info("GitHubAgent closed successfully")
        except Exception as e:
            logger.error(f"Error closing GitHubAgent: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
