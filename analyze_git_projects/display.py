import json
from typing import Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .models.simple_project_schema import SimpleProject

console = Console()


class ResultsDisplay:
    """Handles displaying analysis results in a formatted way"""
    
    @staticmethod
    def display_results(project: SimpleProject) -> None:
        """Display analysis results in a formatted way"""
        console.print(Panel(f"[bold blue]Repository Analysis: {project.name}[/bold blue]"))
        
        # Display project info
        if project.url:
            console.print(Panel(f"URL: {project.url}", title="🔗 Repository Info"))
        
        # Display description
        if project.description:
            console.print(Panel(project.description, title="📋 Description"))
        
        # Display technologies
        if project.technologies:
            tech_text = ", ".join(project.technologies)
            console.print(Panel(f"[green]{tech_text}[/green]", title="🔧 Technologies"))
        
        # Display key features
        if project.key_features:
            features_text = "\n".join(f"• {feature}" for feature in project.key_features)
            console.print(Panel(features_text, title="⭐ Key Features"))
        
        # Display highlights
        if project.highlights:
            console.print(Panel(project.highlights, title="🏆 Highlights"))
    
    @staticmethod
    def save_results_to_file(project: SimpleProject, output_file: str = None) -> str:
        """Save analysis results to JSON file"""
        import os
        
        if not output_file:
            # Create the processed directory if it doesn't exist
            processed_dir = f"projects/processed"
            os.makedirs(processed_dir, exist_ok=True)
            output_file = f"{processed_dir}/{project.name}.json"
        
        # Save SimpleProject directly as JSON
        with open(output_file, 'w') as f:
            json.dump(project.model_dump(), f, indent=2)
        
        console.print(f"[green]✅ Results saved to {output_file}[/green]")
        return output_file
    
    @staticmethod
    def display_summary(projects_list: List[SimpleProject]) -> None:
        """Display summary of multiple analysis results"""
        console.print(Panel("[bold blue]Analysis Summary[/bold blue]"))
        
        total = len(projects_list)
        
        summary_text = f"""
        Total repositories analyzed: {total}
        """
        
        console.print(Panel(summary_text, title="📊 Statistics"))
        
        # Display project names
        if projects_list:
            projects_text = "\n".join(f"- {project.name}" for project in projects_list)
            console.print(Panel(projects_text, title="📁 Analyzed Projects"))