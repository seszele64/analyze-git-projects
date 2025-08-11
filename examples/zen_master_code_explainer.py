#!/usr/bin/env python3
"""
Zen Master Code Explainer: Reduces Mental Complexity Through Explicit Relationships

WHY THIS EXISTS: Reading complex codebases creates cognitive overload. This tool
breaks down code into digestible, purpose-driven components with clear relationships.

RESPONSIBILITY: Explain what each object does, why it exists, and how it connects
to other objects - eliminating the mental gymnastics of reverse-engineering intent.
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from analyze_git_projects.agent import GitHubAgent
from analyze_git_projects.mcp_server_factory import create_read_only_server
from pydantic import BaseModel, Field
from dotenv import load_dotenv


# ==============================================================================
# ZEN MASTER DATA STRUCTURES
# ==============================================================================

class RelationshipType(str, Enum):
    """Types of relationships between code objects."""
    CREATES = "creates"
    USES = "uses"
    DEPENDS_ON = "depends_on"
    CONFIGURES = "configures"
    TRANSFORMS = "transforms"
    VALIDATES = "validates"


@dataclass
class CodeObject:
    """
    WHY THIS EXISTS: Raw code objects are just syntax. We need semantic understanding
    of what each piece actually DOES in the system.
    
    RESPONSIBILITY: Capture the essence of a code object - its purpose, boundaries,
    and relationships without implementation noise.
    """
    name: str
    type: str  # class, function, module, etc.
    purpose: str  # WHY this exists - the problem it solves
    responsibility: str  # WHAT it does - single clear responsibility
    boundaries: str  # WHAT it does NOT do - explicit limits
    relationships: List[Dict[str, Any]]  # HOW it connects to others
    
    def explain(self) -> str:
        """Generate human-readable explanation."""
        lines = [
            f"\n🧘 {self.type.upper()}: {self.name}",
            f"├─ PURPOSE: {self.purpose}",
            f"├─ RESPONSIBILITY: {self.responsibility}",
            f"├─ BOUNDARIES: {self.boundaries}",
            f"└─ RELATIONSHIPS:"
        ]
        
        for rel in self.relationships:
            lines.append(f"   • {rel['type']} → {rel['target']} ({rel['reason']})")
            
        return "\n".join(lines)


class CodeExplainer(BaseModel):
    """Structured explanation of code relationships and purpose."""
    objects: List[Dict[str, Any]]
    flow: List[str]
    mental_model: str


# ==============================================================================
# ZEN MASTER PROMPT TEMPLATE
# ==============================================================================

ZEN_MASTER_PROMPT = """
You are a Zen Master Code Explainer. Your mission is to eliminate mental complexity
by making code relationships explicit and purposeful.

ANALYZE the provided code and explain it as if teaching a distracted developer
who needs to understand the system quickly.

For each significant object (class, function, module), provide:

1. **PURPOSE**: Why does this exist? What problem does it solve?
2. **RESPONSIBILITY**: What is its single, clear job?
3. **BOUNDARIES**: What does it explicitly NOT do? (Critical for ADHD brains)
4. **RELATIONSHIPS**: How does it connect to other objects?
5. **MENTAL MODEL**: Simple analogy or metaphor for understanding

FORMAT your response as a structured explanation that reduces cognitive load.

Read the file at {file_url}
use get_file_contents tool to read files

Focus on making the implicit explicit. Transform confusing abstractions into
clear, purposeful components with obvious relationships.
"""

# ==============================================================================
# EXPLANATION ENGINE
# ==============================================================================

class ZenMasterExplainer:
    """
    WHY THIS EXISTS: Code analysis tools focus on syntax and structure. We need
    semantic understanding that reduces mental complexity for ADHD developers.
    
    RESPONSIBILITY: Transform complex code into digestible, purpose-driven explanations
    with explicit relationships between components.
    
    BOUNDARIES: Explains code relationships only. Does not modify or optimize code.
    """
    
    def __init__(self):
        load_dotenv()
        
        # Create MCP server for GitHub access
        self.mcp_server = create_read_only_server(
            github_pat=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        )
        
        # Initialize agent with zen master persona
        self.agent = GitHubAgent(
            model_name="google/gemini-2.5-flash-lite",
            system_prompt=ZEN_MASTER_PROMPT,
            mcp_servers=[self.mcp_server],
            llm_provider='openrouter'
        )
    
    def explain_file(self, file_url: str) -> CodeExplainer:
        """
        WHY THIS EXISTS: Reading a file in isolation creates confusion about
        how it fits into the larger system. We need context and relationships.
        
        RESPONSIBILITY: Generate complete explanation of a file's purpose,
        objects, and relationships within the codebase.
        
        Args:
            file_url: GitHub URL to the file to analyze
            
        Returns:
            CodeExplainer: Structured explanation with relationships
        """
        
        # Create prompt for zen master analysis
        from langchain_core.prompts import PromptTemplate
        
        # First, get the actual file content using the agent
        content_response = self.agent.run_sync(
            user_prompt=f"Read the file at {file_url} and provide the complete code content",
            output_type=str
        )
        
        prompt_template = PromptTemplate(
            input_variables=["file_url"],
            template=ZEN_MASTER_PROMPT,
        )
        
        # Run zen master analysis on the content
        response = self.agent.run_sync(
            user_prompt=prompt_template.format(file_url=content_response.output),
            output_type=CodeExplainer
        )
        
        return response.output
    
    def explain_relationships(self, objects: List[Dict[str, Any]]) -> str:
        """
        WHY THIS EXISTS: Objects in isolation are meaningless. Relationships
        create the system. We need to visualize these connections.
        
        RESPONSIBILITY: Create human-readable explanation of how objects
        work together to form the complete system.
        
        Args:
            objects: List of code objects with their relationships
            
        Returns:
            str: Formatted explanation of system relationships
        """
        
        if not objects:
            return "No objects found in analysis."
        
        explanations = []
        
        for obj_data in objects:
            # Handle flexible response structure from AI
            try:
                # Handle both nested dict and direct string formats
                if isinstance(obj_data, dict):
                    name = obj_data.get('name', 'Unnamed Object')
                    obj_type = obj_data.get('type', 'unknown')
                    purpose = obj_data.get('purpose', 'Purpose not specified')
                    responsibility = obj_data.get('responsibility', 'Responsibility not defined')
                    boundaries = obj_data.get('boundaries', 'Boundaries not specified')
                    
                    # Handle relationships in different formats
                    relationships = []
                    rel_data = obj_data.get('relationships', [])
                    
                    if isinstance(rel_data, list):
                        for rel in rel_data:
                            if isinstance(rel, dict):
                                relationships.append(rel)
                            elif isinstance(rel, str):
                                relationships.append({
                                    'type': 'relates_to',
                                    'target': str(rel),
                                    'reason': 'Connected component'
                                })
                    elif isinstance(rel_data, str):
                        relationships.append({
                            'type': 'relates_to',
                            'target': rel_data,
                            'reason': 'System component'
                        })
                else:
                    # Handle string format
                    name = str(obj_data)
                    obj_type = 'component'
                    purpose = f'Part of {name} system'
                    responsibility = 'Contributes to overall functionality'
                    boundaries = 'Specific to its role'
                    relationships = []
                
                obj = CodeObject(
                    name=name,
                    type=obj_type,
                    purpose=purpose,
                    responsibility=responsibility,
                    boundaries=boundaries,
                    relationships=relationships
                )
                explanations.append(obj.explain())
            except Exception as e:
                # Fallback for malformed object data
                explanations.append(f"⚠️ Could not parse object: {obj_data} - {str(e)}")
        
        return "\n".join(explanations)


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================

def save_analysis_to_json(explanation: CodeExplainer, filename: str) -> str:
    """
    WHY THIS EXISTS: Analysis results need to be saved for later reference
    and sharing with team members.
    
    RESPONSIBILITY: Save the complete analysis to a JSON file with proper formatting.
    
    Args:
        explanation: The CodeExplainer object to save
        filename: Output filename (without extension)
        
    Returns:
        str: Path to the saved JSON file
    """
    import json
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    output_dir = "zen_analysis_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_filename = f"{output_dir}/{filename}_{timestamp}.json"
    
    # Convert to serializable format
    analysis_data = {
        "metadata": {
            "analyzed_at": datetime.now().isoformat(),
            "tool": "zen_master_code_explainer",
            "version": "1.0"
        },
        "analysis": {
            "mental_model": explanation.mental_model,
            "flow": explanation.flow,
            "objects": explanation.objects
        }
    }
    
    # Save to JSON file
    with open(full_filename, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    return full_filename

def demonstrate_zen_master_explainer():
    """
    Demonstrates how to use the Zen Master Explainer to understand code.

    WHY THIS EXISTS: Developers need concrete examples of how to reduce
    mental complexity when approaching new codebases.
    """

    explainer = ZenMasterExplainer()

    # Example: Explain the check_language_and_framework.py file
    example_url = "https://github.com/ranaroussi/yfinance/blob/main/tests/test_cache.py"

    print("🧘 ZEN MASTER: Analyzing code complexity...")
    print("=" * 60)

    try:
        explanation = explainer.explain_file(example_url)
        
        print("\n📋 SYSTEM FLOW:")
        for step in explanation.flow:
            print(f"  → {step}")
        
        print("\n🧠 MENTAL MODEL:")
        print(explanation.mental_model)
        
        print("\n🔍 OBJECT RELATIONSHIPS:")
        relationship_explanation = explainer.explain_relationships(explanation.objects)
        print(relationship_explanation)
        
        # Save to JSON file
        json_file = save_analysis_to_json(explanation, "yfinance_test_cache")
        print(f"\n💾 Analysis saved to: {json_file}")
        
        return explanation
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return None


if __name__ == "__main__":
    demonstrate_zen_master_explainer()