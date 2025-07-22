"""Test suite for SimpleProject integration"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from analyze_git_projects.models.simple_project_schema import SimpleProject
from analyze_git_projects.display import ResultsDisplay


@pytest.fixture
def sample_simple_project():
    """Fixture providing a sample SimpleProject instance"""
    return SimpleProject(
        name="test-project",
        url="https://github.com/test/test-project",
        description="A test project for verification",
        technologies=["Python", "FastAPI", "PostgreSQL"],
        key_features=["User authentication", "REST API", "Database integration"],
        highlights="Used by 1000+ developers"
    )


@pytest.fixture
def minimal_simple_project():
    """Fixture providing a minimal SimpleProject instance"""
    return SimpleProject(
        name="minimal-project",
        description="A minimal project with only required fields"
    )


def test_simple_project_creation(sample_simple_project):
    """Test SimpleProject creation with all fields"""
    assert sample_simple_project.name == "test-project"
    assert sample_simple_project.url == "https://github.com/test/test-project"
    assert sample_simple_project.description == "A test project for verification"
    assert sample_simple_project.technologies == ["Python", "FastAPI", "PostgreSQL"]
    assert sample_simple_project.key_features == ["User authentication", "REST API", "Database integration"]
    assert sample_simple_project.highlights == "Used by 1000+ developers"


def test_minimal_simple_project(minimal_simple_project):
    """Test SimpleProject creation with minimal fields"""
    assert minimal_simple_project.name == "minimal-project"
    assert minimal_simple_project.url is None
    assert minimal_simple_project.description == "A minimal project with only required fields"
    assert minimal_simple_project.technologies == []
    assert minimal_simple_project.key_features == []
    assert minimal_simple_project.highlights is None


def test_simple_project_json_serialization(sample_simple_project):
    """Test JSON serialization of SimpleProject"""
    json_str = sample_simple_project.model_dump_json(indent=2)
    assert isinstance(json_str, str)
    
    # Parse back to dict
    data = json.loads(json_str)
    assert data["name"] == "test-project"
    assert data["url"] == "https://github.com/test/test-project"
    assert data["technologies"] == ["Python", "FastAPI", "PostgreSQL"]


def test_simple_project_dict_serialization(sample_simple_project):
    """Test dict serialization of SimpleProject"""
    data = sample_simple_project.model_dump()
    assert data["name"] == "test-project"
    assert data["url"] == "https://github.com/test/test-project"
    assert data["technologies"] == ["Python", "FastAPI", "PostgreSQL"]


def test_display_results(sample_simple_project, capsys):
    """Test display functionality doesn't crash"""
    ResultsDisplay.display_results(sample_simple_project)
    captured = capsys.readouterr()
    assert "test-project" in captured.out
    assert "Python" in captured.out
    assert "User authentication" in captured.out


def test_save_results_to_file(sample_simple_project):
    """Test file saving functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test_output.json")
        
        # Save file
        saved_path = ResultsDisplay.save_results_to_file(sample_simple_project, output_path)
        assert saved_path == output_path
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["name"] == "test-project"
        assert data["url"] == "https://github.com/test/test-project"
        assert data["technologies"] == ["Python", "FastAPI", "PostgreSQL"]


def test_save_results_default_filename(sample_simple_project):
    """Test file saving with default filename"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            saved_path = ResultsDisplay.save_results_to_file(sample_simple_project)
            assert "test-project" in saved_path
            assert os.path.exists(saved_path)
        finally:
            os.chdir(original_cwd)


def test_display_summary():
    """Test display summary functionality with multiple projects"""
    projects = [
        SimpleProject(name="project1", description="First project"),
        SimpleProject(name="project2", description="Second project"),
        SimpleProject(name="project3", description="Third project")
    ]
    
    # Should not crash
    ResultsDisplay.display_summary(projects)


def test_display_summary_with_failures():
    """Test display summary with some failed projects"""
    projects = [
        SimpleProject(name="success1", description="Successful project"),
        SimpleProject(name="failed1", description="Failed project"),
    ]
    
    # Should not crash
    ResultsDisplay.display_summary(projects)


def test_empty_technologies_and_features():
    """Test SimpleProject with empty lists"""
    project = SimpleProject(
        name="empty-lists",
        description="Project with empty lists",
        technologies=[],
        key_features=[]
    )
    
    assert project.technologies == []
    assert project.key_features == []


def test_optional_url_none():
    """Test SimpleProject with None URL"""
    project = SimpleProject(
        name="no-url",
        description="Project without URL"
    )
    
    assert project.url is None


def test_optional_highlights_none():
    """Test SimpleProject with None highlights"""
    project = SimpleProject(
        name="no-highlights",
        description="Project without highlights"
    )
    
    assert project.highlights is None