from typing import List, Optional
from pydantic import BaseModel, Field

class SimpleProject(BaseModel):
    name: str = Field(..., description="Project name")
    url: Optional[str] = Field(None, description="Project URL")
    description: str = Field(..., description="Brief description of the project and what it does")
    technologies: List[str] = Field(default_factory=list, description="Key technologies used")
    key_features: List[str] = Field(default_factory=list, description="Notable features")
    highlights: Optional[str] = Field(None, description="Any achievements, usage, measurable outcomes")
