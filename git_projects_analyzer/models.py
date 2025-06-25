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


class AnalysisResults(BaseModel):
    """Model for repository analysis results"""
    repo_url: str = Field(..., description="Repository URL")
    repo_info: Optional[RepositoryInfo] = None
    structure: Optional[str] = Field(None, description="Repository directory structure")
    files: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Important files content")
    
    # Remove the single analysis field and replace with structured components
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    tools_used: List[str] = Field(default_factory=list, description="MCP tools used in analysis")
    
    # Structured fields for table display and JSON output
    technology_stack: Optional["TechnologyStack"] = None
    project_complexity: Optional["ProjectComplexity"] = None
    code_quality: Optional["CodeQualityMetrics"] = None
    project_purpose: Optional[str] = Field(None, description="Brief description of project purpose")
    key_features: List[str] = Field(default_factory=list, description="Main features of the project")
    architecture_type: Optional[str] = Field(None, description="Type of architecture (e.g., MVC, Pipeline, Microservices)")
    dependencies: List[str] = Field(default_factory=list, description="External dependencies and services")
    development_practices: List[str] = Field(default_factory=list, description="Development practices observed")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.repo_info and self.repo_url:
            self.repo_info = RepositoryInfo.from_url(self.repo_url)
    
    @property
    def has_error(self) -> bool:
        """Check if analysis has errors"""
        return self.error is not None
    
    @property
    def is_complete(self) -> bool:
        """Check if analysis is complete"""
        return (self.technology_stack is not None and 
                self.project_complexity is not None and 
                self.code_quality is not None and 
                not self.has_error)
    
    def to_structured_analysis(self) -> Dict[str, Any]:
        """Convert to structured analysis format for JSON output"""
        return {
            "tech_stack": {
                "primary_language": self.technology_stack.primary_language if self.technology_stack else None,
                "languages": self.technology_stack.languages if self.technology_stack else [],
                "frameworks": self.technology_stack.frameworks if self.technology_stack else [],
                "tools": self.technology_stack.tools if self.technology_stack else [],
                "databases": self.technology_stack.databases if self.technology_stack else [],
                "deployment_tools": self.technology_stack.deployment_tools if self.technology_stack else [],
                "testing_frameworks": self.technology_stack.testing_frameworks if self.technology_stack else []
            },
            "project_purpose": self.project_purpose,
            "architecture": {
                "type": self.architecture_type,
                "description": f"The project follows a {self.architecture_type} architecture" if self.architecture_type else None
            },
            "dependencies": self.dependencies,
            "code_quality": {
                "has_tests": self.code_quality.has_tests if self.code_quality else False,
                "has_documentation": self.code_quality.has_documentation if self.code_quality else False,
                "has_ci_cd": self.code_quality.has_ci_cd if self.code_quality else False,
                "has_linting": self.code_quality.has_linting if self.code_quality else False,
                "has_type_checking": self.code_quality.has_type_checking if self.code_quality else False,
                "test_coverage": self.code_quality.test_coverage if self.code_quality else None,
                "documentation_quality": self.code_quality.documentation_quality if self.code_quality else None,
                "code_organization": self.code_quality.code_organization if self.code_quality else None
            },
            "complexity": {
                "level": self.project_complexity.level if self.project_complexity else "Not assessed",
                "score": self.project_complexity.score if self.project_complexity else None,
                "factors": self.project_complexity.factors if self.project_complexity else [],
                "file_count": self.project_complexity.file_count if self.project_complexity else None,
                "lines_of_code": self.project_complexity.lines_of_code if self.project_complexity else None
            },
            "key_features": self.key_features,
            "development_practices": self.development_practices
        }
    
    def to_table_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format suitable for table display"""
        return {
            "Repository": self.repo_info.name if self.repo_info else "Unknown",
            "Owner": self.repo_info.owner if self.repo_info else "Unknown",
            "Purpose": self.project_purpose or "Not specified",
            "Languages": ", ".join(self.technology_stack.languages) if self.technology_stack else "Not analyzed",
            "Frameworks": ", ".join(self.technology_stack.frameworks) if self.technology_stack else "Not analyzed",
            "Complexity": self.project_complexity.level if self.project_complexity else "Not assessed",
            "Complexity Score": self.project_complexity.score if self.project_complexity else "N/A",
            "Has Tests": self.code_quality.has_tests if self.code_quality else False,
            "Has Documentation": self.code_quality.has_documentation if self.code_quality else False,
            "Has CI/CD": self.code_quality.has_ci_cd if self.code_quality else False,
            "Architecture": self.architecture_type or "Not specified",
            "Key Features": "; ".join(self.key_features) if self.key_features else "Not specified",
            "Status": "Complete" if self.is_complete else "Error" if self.has_error else "Incomplete"
        }


class TechnologyStack(BaseModel):
    """Model for technology stack information"""
    primary_language: Optional[str] = Field(None, description="Primary programming language")
    languages: List[str] = Field(default_factory=list, description="All programming languages detected")
    frameworks: List[str] = Field(default_factory=list, description="Web frameworks and libraries")
    tools: List[str] = Field(default_factory=list, description="Development tools and utilities")
    databases: List[str] = Field(default_factory=list, description="Database systems")
    deployment_tools: List[str] = Field(default_factory=list, description="Deployment and containerization tools")
    testing_frameworks: List[str] = Field(default_factory=list, description="Testing frameworks and tools")


class ProjectComplexity(BaseModel):
    """Model for project complexity assessment"""
    level: str = Field(..., description="Complexity level: Beginner, Intermediate, Advanced")
    score: Optional[int] = Field(None, ge=1, le=10, description="Complexity score 1-10")
    factors: List[str] = Field(default_factory=list, description="Factors contributing to complexity")
    file_count: Optional[int] = Field(None, description="Total number of files")
    lines_of_code: Optional[int] = Field(None, description="Estimated lines of code")


class CodeQualityMetrics(BaseModel):
    """Model for code quality assessment"""
    has_tests: bool = Field(False, description="Whether the project includes tests")
    has_documentation: bool = Field(False, description="Whether the project has documentation")
    has_ci_cd: bool = Field(False, description="Whether CI/CD is configured")
    has_linting: bool = Field(False, description="Whether linting tools are configured")
    has_type_checking: bool = Field(False, description="Whether static type checking is used")
    test_coverage: Optional[str] = Field(None, description="Test coverage level (High/Medium/Low)")
    documentation_quality: Optional[str] = Field(None, description="Documentation quality (Excellent/Good/Fair/Poor)")
    code_organization: Optional[str] = Field(None, description="Code organization quality")