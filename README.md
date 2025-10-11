# Healr - AI-Powered Code Self-Healing System

An intelligent code analysis and auto-repair system that uses local LLMs to detect and fix code quality issues automatically.

## Features

- **Automatic Code Analysis**: Detects code quality issues using pylint and radon
- **AI-Powered Fixes**: Uses local LLMs (Ollama/LM Studio) to generate intelligent fixes
- **Semantic Search**: ChromaDB-based embedding index for context-aware code understanding
- **Safe Editing**: AST-based code modifications with automatic backups
- **Git Integration**: Automatic commits with descriptive messages
- **Web Dashboard**: Real-time monitoring via FastAPI + React MaterialUI interface
- **Offline Operation**: Fully functional with local models

## Prerequisites

- Python 3.10 or higher
- Ollama or LM Studio
- Git
- Node.js 16+ (for the web dashboard)

## Installation

### 1. Install Ollama and Pull a Model

```bash
# Install Ollama (visit https://ollama.ai)
# Pull a code model
ollama pull codellama:7b-instruct
# Or use starcoder2
ollama pull starcoder2:7b
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Frontend (Optional)

```bash
cd frontend
npm install
```

## Configuration

Edit `config/settings.json` to customize:

- LLM provider and model selection
- Code quality thresholds
- Supported file extensions
- Git commit behavior
- Server settings

## Usage

### Command Line Interface

```bash
# Analyze a repository
python src/main.py analyze --repo /path/to/repo

# Fix detected issues
python src/main.py fix --repo /path/to/repo

# Generate test cases
python src/main.py test --repo /path/to/repo --file src/example.py

# Generate report
python src/main.py report --repo /path/to/repo
```

### Web Dashboard

```bash
# Start the FastAPI backend
python src/api_server.py

# In another terminal, start the React frontend
cd frontend
npm start
```

Visit `http://localhost:3000` to access the dashboard.

## Project Structure

```
Healr/
├── src/
│   ├── repo_parser.py          # Repository file parsing
│   ├── embedding_index.py      # ChromaDB semantic search
│   ├── issue_detector.py       # Static analysis (pylint/radon)
│   ├── llm_agent.py           # Local LLM integration
│   ├── code_editor.py         # Safe code editing with AST
│   ├── commit_manager.py      # Git operations
│   ├── explanation_logger.py  # JSON logging system
│   ├── test_generator.py      # Automatic test generation
│   ├── main.py               # CLI orchestration
│   └── api_server.py         # FastAPI backend
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── theme/           # MaterialUI theme
│   └── package.json
├── config/
│   └── settings.json         # Configuration
├── logs/                     # Operation logs
├── tests/                    # Unit tests
├── backups/                  # Code backups
└── requirements.txt
```

## How It Works

1. **Repository Parsing**: Scans the target repository for supported file types
2. **Issue Detection**: Runs static analysis to identify code quality issues
3. **Embedding Index**: Creates semantic embeddings for context retrieval
4. **LLM Analysis**: For each issue, queries the local LLM with relevant context
5. **Code Editing**: Applies suggested fixes using AST-based editing
6. **Verification**: Validates syntax and runs tests if available
7. **Git Commit**: Automatically commits changes with descriptive messages
8. **Logging**: Records all operations and LLM responses

## Example Tasks

### Refactoring
```bash
python src/main.py fix --repo ./my_project --task refactor
```

### Fix Bugs
```bash
python src/main.py fix --repo ./my_project --task fix_bugs
```

### Add Docstrings
```bash
python src/main.py fix --repo ./my_project --task add_docstrings
```

## Code Quality Metrics

The system tracks:
- Cyclomatic complexity
- Maintainability index
- Pylint scores
- Lines of code
- Issue counts by type

## Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Evaluation

Test on open-source repositories:

```bash
# Clone a test repository
git clone https://github.com/example/repo test_repo

# Record before metrics
python src/main.py analyze --repo test_repo --output before_metrics.json

# Run fixes
python src/main.py fix --repo test_repo

# Record after metrics
python src/main.py analyze --repo test_repo --output after_metrics.json

# Compare results
python src/compare_metrics.py before_metrics.json after_metrics.json
```

## Safety Features

- **Automatic Backups**: Original files are backed up before modification
- **Syntax Validation**: All changes are validated before saving
- **Git Integration**: Easy rollback via git history
- **Dry Run Mode**: Preview changes without applying them

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Test the API
curl http://localhost:11434/api/generate -d '{"model": "codellama:7b-instruct", "prompt": "Hello"}'
```

### ChromaDB Issues
```bash
# Clear the database
rm -rf chroma_db/
```

### Python Environment
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Acknowledgments

- Ollama for local LLM inference
- ChromaDB for vector storage
- Pylint and Radon for static analysis
- FastAPI and React for the web interface
