# Analyze Git Projects

A powerful tool for analyzing GitHub repositories using the official GitHub MCP (Model Context Protocol) server and AI-powered analysis. This tool provides comprehensive insights into repository structure, technology stack, and project characteristics using a clean, simple data model.

## 🚀 Features

- **Automated Repository Analysis**: Analyze any GitHub repository URL
- **MCP Server Integration**: Uses git-ingest MCP server for repository data extraction
- **AI-Powered Insights**: Leverages OpenRouter with structured output parsing
- **Simple Data Model**: Clean, focused Pydantic model for analysis results
- **Rich Console Output**: Beautiful formatted output with Rich library
- **JSON Export**: Save analysis results for later use
- **CLI Interface**: Command-line tool for batch processing
- **Modular Architecture**: Clean, maintainable code structure

## 📋 Requirements

- Python 3.8+
- Docker (for running GitHub MCP server)
- OpenRouter API key (for AI analysis)
- GitHub Personal Access Token (for repository access)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/seszele64/analyze-git-projects.git
   cd analyze-git-projects
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Docker (if not already installed):**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install docker.io
   
   # On macOS
   brew install docker
   ```

4. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "OPENROUTER_API_KEY=your_api_key_here" > .env
   echo "GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here" >> .env
   ```

## 📁 Project Structure

```
analyze_git_projects/
├── __init__.py          # Package initialization
├── models/             # Pydantic data models
│   ├── __init__.py
│   ├── simple_project_schema.py  # SimpleProject model
│   └── other_models.py # Additional models
├── display.py          # Results formatting and display
├── main.py             # Main test runner
├── cli.py              # Command-line interface
└── github_mcp_analyzer.py  # GitHub MCP integration
```

### Core Components

#### 🔍 `analyzer.py` - GitIngestAnalyzer
The main analyzer class that:
- Initializes MCP server connection
- Configures AI agent with OpenRouter and structured output
- Orchestrates repository analysis workflow
- Handles error recovery and logging

#### 📊 `simple_project_schema.py` - SimpleProject Model
Clean, focused Pydantic model for repository analysis:
- `name`: Project name
- `url`: Repository URL (optional)
- `description`: Brief project description
- `technologies`: List of key technologies used
- `key_features`: Notable features and capabilities
- `highlights`: Achievements, usage metrics, or outcomes (optional)

#### 🎨 `display.py` - ResultsDisplay
Handles output formatting and file operations:
- Rich console formatting with panels and colors
- JSON export functionality
- Analysis summaries for multiple repositories
- Clean, focused display of SimpleProject data

#### 🖥️ `cli.py` - Command Line Interface
Full-featured CLI with:
- Multiple repository analysis
- Custom output directories
- Connection testing
- Verbose error reporting

## 🚀 Usage

### 1. Quick Start (Test Mode)
Run the built-in test with sample repository:
```bash
python -m analyze_git_projects.main
```

### 2. Command Line Interface

#### Basic Usage
```bash
# Analyze a single repository
python -m analyze_git_projects.cli https://github.com/microsoft/vscode

# Analyze multiple repositories at once
python -m analyze_git_projects.cli \
  https://github.com/microsoft/vscode \
  https://github.com/facebook/react \
  https://github.com/tensorflow/tensorflow
```

#### Using API Key
```bash
# Provide API key directly (overrides environment variable)
python -m analyze_git_projects.cli \
  --api-key sk-or-v1-your-openrouter-key \
  https://github.com/openai/whisper

# Using environment variable (recommended)
export OPENROUTER_API_KEY="sk-or-v1-your-openrouter-key"
python -m analyze_git_projects.cli https://github.com/openai/whisper
```

#### Custom Output Directory
```bash
# Save results to specific directory
python -m analyze_git_projects.cli \
  --output-dir ./analysis-results \
  https://github.com/vercel/next.js

# Create timestamped results directory
mkdir "analysis-$(date +%Y%m%d-%H%M%S)"
python -m analyze_git_projects.cli \
  --output-dir "./analysis-$(date +%Y%m%d-%H%M%S)" \
  https://github.com/docker/docker
```

#### Connection Testing
```bash
# Test MCP server connection only (no analysis)
python -m analyze_git_projects.cli --test-connection

# Test with specific API key
python -m analyze_git_projects.cli \
  --api-key sk-or-v1-your-key \
  --test-connection
```

#### Verbose Output
```bash
# Enable detailed error reporting and debug info
python -m analyze_git_projects.cli \
  --verbose \
  https://github.com/pytorch/pytorch

# Combine with other options
python -m analyze_git_projects.cli \
  --verbose \
  --output-dir ./detailed-analysis \
  --api-key sk-or-v1-your-key \
  https://github.com/kubernetes/kubernetes
```

#### Advanced Examples

**Batch Analysis with Custom Settings:**
```bash
# Analyze multiple popular Python projects
python -m analyze_git_projects.cli \
  --output-dir ./python-projects \
  --verbose \
  https://github.com/psf/requests \
  https://github.com/pallets/flask \
  https://github.com/django/django \
  https://github.com/fastapi/fastapi
```

**Portfolio Analysis:**
```bash
# Analyze your own repositories
python -m analyze_git_projects.cli \
  --output-dir ./my-portfolio \
  https://github.com/yourusername/project1 \
  https://github.com/yourusername/project2 \
  https://github.com/yourusername/project3
```

### 3. Python API
Use as a library in your own code:
```python
import asyncio
from analyze_git_projects import GitHubMCAnalyzer, ResultsDisplay

async def analyze_repo():
    # Initialize analyzer
    analyzer = GitHubMCAnalyzer(openrouter_api_key="your_key")
    
    # Test connection
    if not await analyzer.test_connection():
        print("MCP server connection failed")
        return
    
    # Analyze repository
    project = await analyzer.analyze_repository(
        "https://github.com/user/repo"
    )
    
    # Display results
    ResultsDisplay.display_results(project)
    
    # Save to file
    ResultsDisplay.save_results_to_file(project)

# Run analysis
asyncio.run(analyze_repo())
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Run all tests
python -m pytest tests/test_simple_project.py -v

# Run with coverage
python -m pytest tests/test_simple_project.py --cov=analyze_git_projects
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for AI analysis
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional: Custom MCP server configuration
GIT_INGEST_SERVER_COMMAND=uvx
GIT_INGEST_SERVER_ARGS=--from,git+https://github.com/adhikasp/mcp-git-ingest,mcp-git-ingest
```

### 📖 CLI Arguments Reference

```bash
python -m analyze_git_projects.cli [OPTIONS] REPO_URLS...
```

#### Positional Arguments
| Argument | Description | Example |
|----------|-------------|---------|
| `repo_urls` | One or more GitHub repository URLs to analyze | `https://github.com/user/repo` |

#### Options
| Flag | Long Form | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `-h` | `--help` | - | - | Show help message and exit |
| | `--api-key` | `TEXT` | `$OPENROUTER_API_KEY` | OpenRouter API key (overrides env var) |
| | `--output-dir` | `TEXT` | `.` | Directory to save analysis results |
| | `--test-connection` | `FLAG` | `False` | Test MCP server connection and exit |
| `-v` | `--verbose` | `FLAG` | `False` | Enable verbose output and debug info |

## 📈 Analysis Output

The analyzer provides focused insights using the SimpleProject model:

### 📊 SimpleProject Data Structure
```json
{
  "name": "awesome-project",
  "url": "https://github.com/user/awesome-project",
  "description": "A modern web application built with FastAPI and React",
  "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
  "key_features": ["User authentication", "REST API", "Real-time updates", "Database integration"],
  "highlights": "Used by 1000+ developers, deployed in production environments"
}
```

### Console Output
Rich-formatted panels with color coding:
- 🔗 Repository Info (name and URL)
- 📋 Project Description
- 🔧 Technologies Used
- ⭐ Key Features
- 🏆 Highlights and Achievements

### JSON Export
Clean, structured JSON files saved to `projects/processed/` directory with the project name.

## 🔍 Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```bash
   # Ensure Docker is installed and running
   docker --version
   docker run hello-world
   
   # Check Docker permissions
   sudo usermod -aG docker $USER  # Add user to docker group
   ```

2. **GitHub Personal Access Token Issues**
   ```bash
   # Check environment variable
   echo $GITHUB_PERSONAL_ACCESS_TOKEN
   
   # Create a GitHub token at https://github.com/settings/tokens
   # Required scopes: public_repo (or repo for private repos)
   ```

3. **OpenRouter API Key Issues**
   ```bash
   # Check environment variable
   echo $OPENROUTER_API_KEY
   
   # Verify API key format
   # Should start with 'sk-or-v1-'
   ```

4. **Module Import Errors**
   ```bash
   # Run from project root directory
   cd /path/to/analyze-git-projects
   python -m analyze_git_projects.main
   ```

### Debug Mode
Enable verbose output for detailed error information:
```bash
python -m analyze_git_projects.cli --verbose <repo_url>
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [git-ingest](https://github.com/adhikasp/mcp-git-ingest) - MCP server for repository analysis
- [pydantic-ai](https://github.com/pydantic/pydantic-ai) - AI agent framework with structured outputs
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [OpenRouter](https://openrouter.ai/) - AI model provider

## 📞 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Happy Repository Analyzing! 🚀**
