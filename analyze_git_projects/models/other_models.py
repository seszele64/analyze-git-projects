from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    """Repository information model"""
    url: str = Field(..., description="Repository URL")
    name: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")
    
    @classmethod
    def from_url(cls, url: str) -> "RepositoryInfo":
        """Create RepositoryInfo from URL"""
        parts = url.rstrip('/').split('/')
        return cls(
            url=url,
            name=parts[-1],
            owner=parts[-2] if len(parts) >= 2 else "unknown"
        )
