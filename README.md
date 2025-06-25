# Git-Ingest Repository Analyzer

A powerful tool for analyzing GitHub repositories using the git-ingest MCP (Model Context Protocol) server and AI-powered analysis. This tool provides comprehensive insights into repository structure, technology stack, code quality, and complexity.

## 🚀 Features

- **Automated Repository Analysis**: Analyze any GitHub repository URL
- **MCP Server Integration**: Uses git-ingest MCP server for repository data extraction
- **AI-Powered Insights**: Leverages OpenRouter for intelligent analysis
- **Structured Data Models**: Type-safe Pydantic models for analysis results
- **Rich Console Output**: Beautiful formatted output with Rich library
- **JSON Export**: Save analysis results for later use
- **CLI Interface**: Command-line tool for batch processing
- **Modular Architecture**: Clean, maintainable code structure

## 📋 Requirements

- Python 3.8+
- `uvx` (for running git-ingest MCP server)
- OpenRouter API key (for AI analysis)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd portfolio-search
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install uvx (if not already installed):**
   ```bash
   pip install uvx
   ```

4. **Set up environment variables:**
   ```bash
   # Create .env file
   echo "OPENROUTER_API_KEY=your_api_key_here" > .env
   ```

## 📁 Project Structure

```
gitingest_analyzer/
├── __init__.py          # Package initialization
├── analyzer.py          # Core GitIngestAnalyzer class
├── models.py           # Pydantic data models
├── display.py          # Results formatting and display
├── main.py             # Main test runner
└── cli.py              # Command-line interface
```

### Core Components

#### 🔍 `analyzer.py` - GitIngestAnalyzer
The main analyzer class that:
- Initializes MCP server connection
- Configures AI agent with OpenRouter
- Orchestrates repository analysis workflow
- Handles error recovery and logging

#### 📊 `models.py` - Data Models
Pydantic models for type-safe data handling:
- `AnalysisResults`: Main container for analysis output
- `RepositoryInfo`: Repository metadata (name, owner, URL)
- `TechnologyStack`: Languages, frameworks, tools
- `ProjectComplexity`: Complexity assessment with scoring
- `CodeQualityMetrics`: Quality indicators and scores

#### 🎨 `display.py` - ResultsDisplay
Handles output formatting and file operations:
- Rich console formatting with panels and colors
- JSON export functionality
- Analysis summaries for multiple repositories
- Content truncation for readability

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
python -m gitingest_analyzer.main
```

### 2. Command Line Interface
Analyze specific repositories:
```bash
# Single repository
python -m gitingest_analyzer.cli https://github.com/user/repo

# Multiple repositories
python -m gitingest_analyzer.cli \
  https://github.com/user/repo1 \
  https://github.com/user/repo2

# With custom options
python -m gitingest_analyzer.cli \
  --api-key your_key \
  --output-dir ./results \
  --verbose \
  https://github.com/user/repo
```

### 3. Python API
Use as a library in your own code:
```python
import asyncio
from gitingest_analyzer import GitIngestAnalyzer, ResultsDisplay

async def analyze_repo():
    # Initialize analyzer
    analyzer = GitIngestAnalyzer(openrouter_api_key="your_key")
    
    # Test connection
    if not await analyzer.test_connection():
        print("MCP server connection failed")
        return
    
    # Analyze repository
    results = await analyzer.analyze_repository(
        "https://github.com/user/repo"
    )
    
    # Display results
    ResultsDisplay.display_results(results)
    
    # Save to file
    ResultsDisplay.save_results_to_file(results)

# Run analysis
asyncio.run(analyze_repo())
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

### CLI Options
```bash
python -m gitingest_analyzer.cli --help

Options:
  --api-key TEXT        OpenRouter API key
  --output-dir TEXT     Output directory for results (default: .)
  --test-connection     Test MCP server connection only
  --verbose, -v         Enable verbose output
```

## 📈 Analysis Output

The analyzer provides comprehensive insights including:

### 🔬 Technology Stack Analysis
- Programming languages detected
- Frameworks and libraries used
- Development tools and build systems
- Database technologies

### 🏗️ Architecture Assessment
- Project structure patterns
- Code organization principles
- Design patterns usage
- Modular architecture analysis

### ✅ Code Quality Metrics
- Documentation coverage
- Testing practices
- CI/CD implementation
- Code style adherence

### 📊 Complexity Scoring
- Beginner/Intermediate/Advanced classification
- Complexity factors identification
- Learning curve assessment
- Technical debt indicators

## 📄 Output Formats

### Console Output
Rich-formatted panels with color coding:
- 🔧 MCP Tools Used
- 📁 Repository Structure
- 📄 Important Files
- 🤖 AI Analysis

### JSON Export
Structured data export with:
```json
{
  "repo_url": "https://github.com/user/repo",
  "repo_info": {
    "name": "repo",
    "owner": "user",
    "url": "https://github.com/user/repo"
  },
  "tools_used": ["git_directory_structure", "git_read_important_files"],
  "structure": "...",
  "files": {...},
  "analysis": "...",
  "is_complete": true,
  "has_error": false
}
```

## 🔍 Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```bash
   # Ensure uvx is installed
   pip install uvx
   
   # Test uvx installation
   uvx --help
   ```

2. **OpenRouter API Key Issues**
   ```bash
   # Check environment variable
   echo $OPENROUTER_API_KEY
   
   # Verify API key format
   # Should start with 'sk-or-v1-'
   ```

3. **Module Import Errors**
   ```bash
   # Run from project root directory
   cd /path/to/portfolio-search
   python -m gitingest_analyzer.main
   ```

### Debug Mode
Enable verbose output for detailed error information:
```bash
python -m gitingest_analyzer.cli --verbose <repo_url>
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
- [pydantic-ai](https://github.com/pydantic/pydantic-ai) - AI agent framework
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [OpenRouter](https://openrouter.ai/) - AI model provider

## 📞 Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Happy Repository Analyzing! 🚀**
