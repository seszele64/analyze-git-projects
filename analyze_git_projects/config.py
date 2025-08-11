"""Typed configuration models for MCP server settings."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    """Valid log levels for the MCP server."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"

class GitHubTool(str, Enum):
    """Available GitHub toolsets."""
    CONTEXT = "context"
    ACTIONS = "actions"
    CODE_SECURITY = "code_security"
    DEPENDABOT = "dependabot"
    DISCUSSIONS = "discussions"
    EXPERIMENTS = "experiments"
    GISTS = "gists"
    ISSUES = "issues"
    NOTIFICATIONS = "notifications"
    ORGS = "orgs"
    PULL_REQUESTS = "pull_requests"
    REPOS = "repos"
    SECRET_PROTECTION = "secret_protection"
    USERS = "users"

class DockerOptions(BaseModel):
    """Docker container configuration options."""
    name: Optional[str] = Field(
        None,
        description="Name of the Docker container"
    )

    memory: Optional[str] = Field(
        None,
        description="Memory limit for the container",
        examples=["256m", "1g", "512m"]
    )
    cpus: Optional[float] = Field(
        None,
        description="CPU limit for the container",
        examples=[0.5, 2.0]
    )
    network: Optional[str] = Field(
        None,
        description="Network mode for the container"
    )
    volumes: Optional[List[str]] = Field(
        None,
        description="Volume mounts in format 'host:container[:mode]'"
    )
    ports: Optional[List[str]] = Field(
        None,
        description="Port mappings in format 'host:container'"
    )
    extra_args: Optional[List[str]] = Field(
        None,
        description="Additional Docker run arguments"
    )

    def add_volume(self, host_path: str, container_path: str, mode: str = "ro") -> None:
        """Add a volume mount to the container."""
        if not self.volumes:
            self.volumes = []
        volume_spec = f"{host_path}:{container_path}:{mode}"
        self.volumes.append(volume_spec)

    def add_port(self, host_port: int, container_port: int) -> None:
        """Add a port mapping to the container."""
        if not self.ports:
            self.ports = []
        port_spec = f"{host_port}:{container_port}"
        self.ports.append(port_spec)


from pydantic import RootModel

class GitHubMCPServerConfig(BaseModel):
    """Typed configuration for GitHub MCP server."""
    
    github_pat: str = Field(
        ...,
        description="GitHub Personal Access Token for authentication",
        min_length=1,
        title="GitHub Personal Access Token",
        example="ghp_xxx123"
    )
    read_only: bool = Field(
        True,
        description="Whether to create a read-only MCP server"
    )
    toolsets: List[GitHubTool] = Field(
        default_factory=list,
        description="List of GitHub toolsets to enable"
    )
    base_url: Optional[str] = Field(
        None,
        description="Custom GitHub API base URL (for GitHub Enterprise)"
    )
    log_level: Optional[LogLevel] = Field(
        None,
        description="Logging level for the MCP server"
    )
    custom_env_vars: Optional[Dict[str, str]] = Field(
        None,
        description="Additional environment variables to pass to the container"
    )
    docker_options: Optional[DockerOptions] = Field(
        None,
        description="Docker container configuration options"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True

# Factory functions for common configurations
def create_basic_config(github_pat: str) -> GitHubMCPServerConfig:
    """Create a basic read-only configuration."""
    return GitHubMCPServerConfig(
        github_pat=github_pat,
        toolsets=[GitHubTool.REPOS]
    )

def create_config_for_reading(github_pat: str) -> GitHubMCPServerConfig:
    """Create a configuration for reading repositories."""
    return GitHubMCPServerConfig(
        github_pat=github_pat,
        read_only=True,
        toolsets=[GitHubTool.REPOS],
        log_level="info",
        docker_options={
            "memory": "512m",
            "cpus": 1.0
        }
    )
