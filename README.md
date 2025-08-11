# Analyze Git Projects

A powerful tool for analyzing GitHub repositories using MCP (Model Context Protocol) servers and AI-powered analysis with Pydantic AI agents. This tool provides comprehensive insights into repository structure, technology stack, and project characteristics using structured output parsing.

## 🚀 Features

- **GitHub Repository Analysis**: Analyze GitHub repositories using MCP servers
- **MCP Server Integration**: Uses GitHub MCP server for repository data extraction
- **AI-Powered Insights**: Leverages OpenRouter with Pydantic AI agents and structured output
- **Structured Output**: Type-safe analysis results using Pydantic models
- **Rich Console Output**: Beautiful formatted output with Rich library
- **Example Use Cases**: Multiple examples for different analysis scenarios
- **Modular Architecture**: Clean, maintainable code structure with configurable agents

## 📋 Requirements

- Python 3.12+
- OpenRouter API key (for AI analysis)
- GitHub Personal Access Token (for repository access)
- MCP server dependencies (automatically managed)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/seszele64/analyze-git-projects.git
   cd analyze-git-projects
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or using pip install -e . for development
   ```

3. **Set up environment variables:**
   ```bash
   # Create .env file in the root directory
   echo "OPENROUTER_API_KEY=your_api_key_here" > .env
   echo "GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here" >> .env
   ```

## 📁 Project Structure

```
analyze_git_projects/
├── __init__.py          # Package initialization
├── agent.py             # GitHubAgent class inheriting from pydantic_ai.Agent
├── config.py            # Configuration models for MCP servers
├── logging.py           # Logging utilities and configuration
├── mcp_server_factory.py # Factory for creating MCP servers
└── examples/            # Example scripts demonstrating different use cases
    ├── check_language_and_framework.py  # Simple language detection
    ├── zen_master_code_explainer.py     # Code explanation system
    ├── analyze_repo_for_portfolio.py    # Portfolio analysis
    └── ...
```

### Core Components

#### 🤖 `agent.py` - GitHubAgent
The main agent class that:
- Inherits from pydantic_ai.Agent for structured AI interactions
- Configures MCP server connections for GitHub data access
- Provides flexible model and provider configuration
- Handles structured output parsing with Pydantic models
- Supports both sync and async operations

#### 🏭 `mcp_server_factory.py` - MCP Server Factory
Factory for creating MCP servers:
- GitHub MCP server configuration and creation
- Read-only server instances for safe repository access
- Configurable authentication and permissions
- Server lifecycle management

#### ⚙️ `config.py` - Configuration Management
Configuration models for:
- GitHub MCP server settings
- API credentials and authentication
- Server parameters and options
- Type-safe configuration handling

#### 🗂️ `examples/` - Use Case Demonstrations
Multiple examples showing:
- **Language/Framework Detection**: Simple analysis for tech stack identification
- **Code Explanation**: Deep code understanding and documentation
- **Portfolio Analysis**: Repository evaluation for professional portfolios
- **Zen Master**: Philosophy-driven code analysis with clear relationships

## 🚀 Usage

### 1. Quick Start (Test Mode)
Run a simple test example:
```bash
python -m examples.check_language_and_framework
```

### 2. Using Examples
The project includes several examples demonstrating different use cases:

#### Language and Framework Detection
```bash
python -m examples.check_language_and_framework
```
This example shows how to:
- Create a structured output model (`SimpleProject`)
- Use GitHub MCP server to read repository files
- Extract language and framework information

#### Code Explanation (Zen Master)
```bash
python -m examples.zen_master_code_explainer
```
This example demonstrates:
- Complex code analysis with relationship mapping
- Structured breakdown of code components
- Purpose-driven code understanding

#### Portfolio Analysis
```bash
python -m examples.analyze_repo_for_portfolio
```
For analyzing repositories for portfolio purposes:
- Technology stack identification
- Project complexity assessment
- Key features extraction

### 3. Python API
Use as a library in your own code:
```python
import os
from dotenv import load_dotenv
from analyze_git_projects.agent import GitHubAgent
from analyze_git_projects.mcp_server_factory import create_read_only_server
from pydantic import BaseModel

load_dotenv()

# Define your output structure
class ProjectAnalysis(BaseModel):
    language: str
    framework: str
    description: str

# Create MCP server
mcp_server = create_read_only_server(
    github_pat=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
)

# Initialize agent
agent = GitHubAgent(
    model_name="google/gemini-2.5-flash-lite",
    system_prompt="You are helpful assistant that analyzes GitHub repositories.",
    mcp_servers=[mcp_server],
    llm_provider='openrouter'
)

# Run analysis
response = agent.run_sync(
    user_prompt="Analyze https://github.com/user/repo",
    output_type=ProjectAnalysis
)

print(response.output)
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

Run the available tests:
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_agent_prompt.py -v
python -m pytest tests/test_mcp_server_factory.py -v
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for AI analysis
OPENROUTER_API_KEY=your_openrouter_api_key

# Required for GitHub repository access
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token

# Optional: Configure logging level
LOG_LEVEL=INFO
```

## � Analysis Output

The analyzer provides flexible, structured output based on your Pydantic models:

### 🏗️ Architecture Patterns
The project supports different analysis patterns:

- **Simple Analysis**: Basic language and framework detection
- **Complex Analysis**: Detailed code relationship mapping
- **Portfolio Analysis**: Project evaluation for professional presentation
- **Code Explanation**: In-depth understanding of code structure and purpose

### � Example Output Structures

#### SimpleProject Model (from examples)
```python
class SimpleProject(BaseModel):
    language: str
    framework: str
```

#### CodeExplanation Model (from zen_master example)
```python
class CodeObject(BaseModel):
    name: str
    type: str  # class, function, module, etc.
    purpose: str  # WHY this exists
    responsibility: str  # WHAT it does
    boundaries: str  # WHAT it does NOT do
```
  "url": "https://github.com/user/awesome-project",
  "description": "A modern web application built with FastAPI and React",
  "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
  "key_features": ["User authentication", "REST API", "Real-time updates", "Database integration"],
  "highlights": "Used by 1000+ developers, deployed in production environments"
}
```

### 🎯 Output Features
- **Type Safety**: All outputs are validated with Pydantic models
- **Flexibility**: Define custom output structures for your use case
- **Rich Formatting**: Console output with syntax highlighting and panels
- **Structured Data**: Easy to process results programmatically

## 🔍 Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```bash
   # Check that required environment variables are set
   echo $OPENROUTER_API_KEY
   echo $GITHUB_PERSONAL_ACCESS_TOKEN
   
   # If missing, add them to your .env file
   echo "OPENROUTER_API_KEY=your_key_here" >> .env
   echo "GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here" >> .env
   ```

2. **GitHub Personal Access Token Issues**
   ```bash
   # Create a GitHub token at https://github.com/settings/tokens
   # Required scopes: public_repo (or repo for private repos)
   ```

3. **OpenRouter API Key Issues**
   ```bash
   # Verify API key format (should start with 'sk-or-v1-')
   # Get your API key from https://openrouter.ai/
   ```

4. **Module Import Errors**
   ```bash
   # Ensure you're running from the project root directory
   cd /path/to/analyze-git-projects
   python -m examples.check_language_and_framework
   ```

### Debug Mode
Enable verbose output in examples by modifying the logging configuration or adding print statements for debugging.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers) - MCP server for GitHub repository access
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
