import json
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .models import AnalysisResults

console = Console()


class ResultsDisplay:
    """Handles displaying analysis results in a formatted way"""
    
    @staticmethod
    def display_results(results: AnalysisResults) -> None:
        """Display analysis results in a formatted way"""
        console.print(Panel(f"[bold blue]Repository Analysis: {results.repo_url}[/bold blue]"))
        
        if results.has_error:
            console.print(Panel(f"[red]Error: {results.error}[/red]", title="❌ Error"))
            return
        
        # Display repository info
        if results.repo_info:
            repo_info_text = f"Name: {results.repo_info.name}\nOwner: {results.repo_info.owner}"
            console.print(Panel(repo_info_text, title="📋 Repository Info"))
        
        # Display tools used
        if results.tools_used:
            tools_text = ", ".join(results.tools_used)
            console.print(Panel(f"[green]{tools_text}[/green]", title="🔧 MCP Tools Used"))
        
        # Display structure
        if results.structure:
            structure_content = ResultsDisplay._truncate_content(str(results.structure), 2000)
            console.print(Panel(structure_content, title="[green]📁 Repository Structure[/green]"))
        
        # Display files content
        if results.files:
            files_content = ResultsDisplay._truncate_content(str(results.files), 2000)
            console.print(Panel(files_content, title="[yellow]📄 Important Files[/yellow]"))
        
        # Display structured analysis
        if results.is_complete:
            # Create formatted analysis display
            analysis_text = ResultsDisplay._format_structured_analysis(results)
            console.print(Panel(analysis_text, title="[cyan]🤖 AI Analysis[/cyan]"))
        else:
            console.print(Panel("[yellow]Analysis incomplete - missing structured data[/yellow]", title="⚠️ Warning"))

    @staticmethod
    def _format_structured_analysis(results: AnalysisResults) -> str:
        """Format structured analysis for display"""
        sections = []
        
        if results.project_purpose:
            sections.append(f"**Purpose:** {results.project_purpose}")
        
        if results.technology_stack:
            tech_parts = []
            if results.technology_stack.primary_language:
                tech_parts.append(f"Primary: {results.technology_stack.primary_language}")
            if results.technology_stack.frameworks:
                tech_parts.append(f"Frameworks: {', '.join(results.technology_stack.frameworks)}")
            if tech_parts:
                sections.append(f"**Technology:** {' | '.join(tech_parts)}")
        
        if results.project_complexity:
            complexity_text = f"**Complexity:** {results.project_complexity.level}"
            if results.project_complexity.score:
                complexity_text += f" ({results.project_complexity.score}/10)"
            sections.append(complexity_text)
        
        if results.key_features:
            sections.append(f"**Key Features:** {', '.join(results.key_features)}")
        
        if results.architecture_type:
            sections.append(f"**Architecture:** {results.architecture_type}")
        
        if results.code_quality:
            quality_indicators = []
            if results.code_quality.has_tests:
                quality_indicators.append("Tests")
            if results.code_quality.has_documentation:
                quality_indicators.append("Documentation")
            if results.code_quality.has_ci_cd:
                quality_indicators.append("CI/CD")
            if quality_indicators:
                sections.append(f"**Quality Indicators:** {', '.join(quality_indicators)}")
        
        return "\n\n".join(sections) if sections else "No structured analysis available"
    
    @staticmethod
    def _truncate_content(content: str, max_length: int = 2000) -> str:
        """Truncate content if it's too long"""
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content
    
    @staticmethod
    def save_results_to_file(results: AnalysisResults, output_file: str = None) -> str:
        """Save analysis results to JSON file"""
        import os
        
        if not output_file:
            repo_name = results.repo_info.name if results.repo_info else "unknown"
            # Create the processed directory if it doesn't exist
            processed_dir = f"projects/processed"
            os.makedirs(processed_dir, exist_ok=True)
            output_file = f"{processed_dir}/{repo_name}.json"
        
        # Convert results to JSON-serializable format using structured analysis
        json_results = {
            "repo_url": results.repo_url,
            "repo_info": results.repo_info.dict() if results.repo_info else None,
            "tools_used": results.tools_used,
            "structure": results.structure,
            "files": results.files,
            "error": results.error,
            "is_complete": results.is_complete,
            "has_error": results.has_error,
            
            # Include all structured analysis fields
            "technology_stack": results.technology_stack.dict() if results.technology_stack else None,
            "project_complexity": results.project_complexity.dict() if results.project_complexity else None,
            "code_quality": results.code_quality.dict() if results.code_quality else None,
            "project_purpose": results.project_purpose,
            "key_features": results.key_features,
            "architecture_type": results.architecture_type,
            "dependencies": results.dependencies,
            "development_practices": results.development_practices,
            
            # Structured analysis format for easier consumption
            "analysis": results.to_structured_analysis(),
            "table_data": results.to_table_dict()  # Table format for convenience
        }
        
        with open(output_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        console.print(f"[green]✅ Results saved to {output_file}[/green]")
        return output_file
    
    @staticmethod
    def display_summary(results_list: list[AnalysisResults]) -> None:
        """Display summary of multiple analysis results"""
        console.print(Panel("[bold blue]Analysis Summary[/bold blue]"))
        
        total = len(results_list)
        successful = sum(1 for r in results_list if r.is_complete)
        failed = sum(1 for r in results_list if r.has_error)
        
        summary_text = f"""
        Total repositories analyzed: {total}
        Successful analyses: {successful}
        Failed analyses: {failed}
        Success rate: {(successful/total*100):.1f}% if total > 0 else 0
        """
        
        console.print(Panel(summary_text, title="📊 Statistics"))
        
        # Show failed analyses
        if failed > 0:
            failed_repos = [r.repo_url for r in results_list if r.has_error]
            failed_text = "\n".join(f"- {url}" for url in failed_repos)
            console.print(Panel(failed_text, title="❌ Failed Analyses"))