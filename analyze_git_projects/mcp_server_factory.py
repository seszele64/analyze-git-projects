"""Factory for creating MCP server configurations."""

from typing import List, Optional, Dict, Any
from pydantic_ai.mcp import MCPServerStdio
from .config import GitHubMCPServerConfig, GitHubTool, LogLevel, DockerOptions

class GitHubMCPServerFactory:
    """Factory class for creating GitHub MCP server configurations."""
    
    # Default Docker image for GitHub MCP server
    DEFAULT_DOCKER_IMAGE = "ghcr.io/github/github-mcp-server"
    
    @staticmethod
    def create_from_config(config: GitHubMCPServerConfig) -> MCPServerStdio:
        """
        Create a GitHub MCP server from a typed configuration object.
        
        Args:
            config: GitHubMCPServerConfig instance containing configuration options
            
        Returns:
            MCPServerStdio: Configured MCP server
        """
        if not isinstance(config, GitHubMCPServerConfig):
            raise TypeError("config must be a GitHubMCPServerConfig instance")
        
        return GitHubMCPServerFactory._build_server_from_config(config)
    
    @staticmethod
    def create_from_dict(config_dict: Dict[str, Any]) -> MCPServerStdio:
        """
        Create a GitHub MCP server from a configuration dictionary.
        
        Args:
            config_dict: Dictionary containing configuration options
            
        Returns:
            MCPServerStdio: Configured MCP server
        """
        config = GitHubMCPServerConfig(**config_dict)
        return GitHubMCPServerFactory.create_from_config(config)
    
    @staticmethod
    def _build_server_from_config(config: GitHubMCPServerConfig) -> MCPServerStdio:
        """
        Internal method to build the actual MCP server from a validated config.
        
        Args:
            config: Validated GitHubMCPServerConfig instance
            
        Returns:
            MCPServerStdio: Configured MCP server
        """
        env_vars = GitHubMCPServerFactory._build_env_vars(config)
        args = GitHubMCPServerFactory._build_docker_args(config, env_vars)

        return MCPServerStdio(
            command="docker",
            args=args
        )
    
    @staticmethod
    def _build_env_vars(config: GitHubMCPServerConfig) -> Dict[str, str]:
        """
        Build environment variables dictionary from configuration.
        
        Args:
            config: GitHubMCPServerConfig instance
            
        Returns:
            Dict[str, str]: Environment variables for the container
        """
        env_vars = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": config.github_pat,
            "GITHUB_TOOLSETS": ",".join(str(tool) for tool in config.toolsets),
            "GITHUB_READ_ONLY": "1" if config.read_only else "0"
        }
        
        # Add optional environment variables
        if config.base_url:
            env_vars["GITHUB_BASE_URL"] = config.base_url
        if config.log_level:
            env_vars["LOG_LEVEL"] = str(config.log_level)
        
        # Merge custom environment variables
        if config.custom_env_vars:
            env_vars.update(config.custom_env_vars)
        
        return env_vars
    
    @staticmethod
    def _build_docker_args(config: GitHubMCPServerConfig, env_vars: Dict[str, str]) -> List[str]:
        """
        Build Docker command arguments from configuration and environment variables.
        
        Args:
            config: GitHubMCPServerConfig instance
            env_vars: Dictionary of environment variables to pass to container
            
        Returns:
            List[str]: Docker command arguments
        """
        args = ["run", "-i", "--rm"]
        
        # Add environment variables as -e flags
        for key, value in env_vars.items():
            args.extend(["-e", f"{key}={value}"])
        
        # Add Docker options if provided
        if config.docker_options:
            docker_opts = config.docker_options
            
            # Add custom volumes
            if docker_opts.volumes:
                for volume in docker_opts.volumes:
                    args.extend(["-v", volume])
            
            # Add custom ports
            if docker_opts.ports:
                for port in docker_opts.ports:
                    args.extend(["-p", port])
            
            # Add custom network
            if docker_opts.network:
                args.extend(["--network", docker_opts.network])
            
            # Add custom name
            if docker_opts.name:
                args.extend(["--name", docker_opts.name])
            
            # Add memory limit
            if docker_opts.memory:
                args.extend(["--memory", docker_opts.memory])
            
            # Add CPU limit
            if docker_opts.cpus:
                args.extend(["--cpus", str(docker_opts.cpus)])
            
            # Add any additional Docker arguments
            if docker_opts.extra_args:
                args.extend(docker_opts.extra_args)
        
        # Add the Docker image
        args.append(GitHubMCPServerFactory.DEFAULT_DOCKER_IMAGE)
        
        return args

def create_read_only_server(github_pat: str) -> MCPServerStdio:
    """
    Create a read-only GitHub MCP server with default configuration.
    
    Args:
        github_pat: GitHub Personal Access Token

    Returns:
        MCPServerStdio: Configured MCP server
    """

    from .config import create_config_for_reading
    config = create_config_for_reading(github_pat=github_pat)
    return GitHubMCPServerFactory.create_from_config(config)

if __name__ == "__main__":
    """Demonstrate the factory output with sample configurations."""
    import json
    
    print("=== GitHub MCP Server Factory Demo ===\n")
    
    custom_config = GitHubMCPServerConfig(
        github_pat="ghp_xxxxxxxxxxxxxxxxxxxx",
        read_only=True,
        toolsets=[GitHubTool.REPOS, GitHubTool.ISSUES],
        log_level=LogLevel.INFO,
        custom_env_vars={"CUSTOM_VAR": "value"},
        docker_options=DockerOptions(
            name="github-mcp-server",
            memory="512m",
            cpus=1.0,
            network="host",
            volumes=["/host/path:/container/path:ro"],
            ports=["8080:80"],
            extra_args=["--restart=always"]
        )
    )
    
    custom_server = GitHubMCPServerFactory.create_from_config(custom_config)

    # run the example
    print(f"   Command: {custom_server.command}")
    print(f"   Args: {' '.join(custom_server.args)}\n")

    print(type(custom_server))