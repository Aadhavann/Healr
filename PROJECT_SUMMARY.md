# Healr - Project Summary

## Overview

Healr is a comprehensive AI-powered code self-healing system that automatically detects and fixes code quality issues using local LLMs. The project is fully implemented with both CLI and web dashboard interfaces, featuring MaterialUI design throughout.

## Project Status: COMPLETE

All core features have been implemented and the system is ready for use.

## Architecture

### Backend (Python)

1. **Core Modules** (`src/`)
   - `repo_parser.py` - Repository file parsing with smart filtering
   - `embedding_index.py` - ChromaDB-based semantic code search
   - `issue_detector.py` - Static analysis using pylint and radon
   - `llm_agent.py` - Local LLM interface (Ollama/LM Studio)
   - `code_editor.py` - Safe code editing with AST validation
   - `commit_manager.py` - Git operations and auto-commits
   - `explanation_logger.py` - JSON-based operation logging
   - `test_generator.py` - Automatic test case generation
   - `main.py` - CLI orchestration with rich output
   - `api_server.py` - FastAPI backend server

2. **Key Features**
   - Supports multiple languages: Python, JavaScript, TypeScript, C++, Java, Go, Rust
   - Configurable quality thresholds
   - Automatic backups before modifications
   - Syntax validation using AST parsing
   - Semantic code search with embeddings
   - Git integration with descriptive commit messages
   - Comprehensive logging of all operations

### Frontend (React + MaterialUI)

1. **Components** (`frontend/src/`)
   - `App.js` - Main application with routing
   - `pages/Dashboard.js` - Main dashboard with analysis and fix controls
   - `pages/Logs.js` - Operation logs viewer with filtering
   - `pages/Commits.js` - Git commit history timeline
   - `services/api.js` - API client for backend communication
   - `theme/theme.js` - MaterialUI theme configuration

2. **Features**
   - Clean, professional MaterialUI design
   - Real-time operation monitoring
   - Interactive charts and statistics
   - Repository analysis and fix workflows
   - Test generation interface
   - Log searching and filtering
   - Commit history visualization

## Technology Stack

### Backend
- Python 3.10+
- FastAPI (REST API)
- ChromaDB (Vector database)
- Sentence Transformers (Embeddings)
- Pylint & Radon (Static analysis)
- GitPython (Git operations)
- Rich (CLI output)
- Ollama/LM Studio (Local LLM)

### Frontend
- React 18
- Material-UI 5
- React Router
- Axios (HTTP client)
- Recharts (Data visualization)

## Directory Structure

```
Healr/
├── src/                      # Python backend source
│   ├── repo_parser.py
│   ├── embedding_index.py
│   ├── issue_detector.py
│   ├── llm_agent.py
│   ├── code_editor.py
│   ├── commit_manager.py
│   ├── explanation_logger.py
│   ├── test_generator.py
│   ├── main.py
│   └── api_server.py
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   ├── theme/           # MaterialUI theme
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   └── package.json
├── config/
│   └── settings.json        # Configuration file
├── logs/                    # Operation logs
├── backups/                 # File backups
├── tests/                   # Unit tests directory
├── examples/
│   └── demo_example.py      # Demo file with issues
├── README.md                # Full documentation
├── QUICKSTART.md           # Quick start guide
├── requirements.txt         # Python dependencies
├── setup.py                # Python package setup
└── .gitignore

```

## Configuration

All settings are managed through `config/settings.json`:

```json
{
  "llm": {
    "provider": "ollama",
    "model": "codellama:7b-instruct",
    "temperature": 0.3
  },
  "code_quality": {
    "max_complexity": 10,
    "min_maintainability_index": 20,
    "pylint_threshold": 7.0
  },
  "repository": {
    "supported_extensions": [".py", ".js", ".ts", ...],
    "exclude_dirs": ["node_modules", "__pycache__", ...]
  }
}
```

## Usage

### Command Line

```bash
# Analyze repository
python src/main.py analyze --repo /path/to/repo

# Fix issues (with dry-run)
python src/main.py fix --repo /path/to/repo --dry-run

# Apply fixes
python src/main.py fix --repo /path/to/repo

# Generate tests
python src/main.py test --repo /path/to/repo

# Generate report
python src/main.py report --repo /path/to/repo
```

### Web Dashboard

```bash
# Start backend
python src/api_server.py

# Start frontend (in another terminal)
cd frontend
npm start
```

Visit http://localhost:3000

## API Endpoints

- `GET /health` - Health check
- `POST /api/analyze` - Analyze repository
- `POST /api/fix` - Fix repository issues
- `POST /api/generate-tests` - Generate tests
- `GET /api/logs` - Get operation logs
- `GET /api/logs/statistics` - Get statistics
- `GET /api/commits` - Get commit history
- `GET /api/metrics` - Get code metrics
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration

## Key Features Implemented

### Analysis
- Multi-language support
- Pylint integration for Python
- Radon complexity analysis
- Maintainability index calculation
- Halstead metrics
- Custom quality thresholds

### Fixing
- LLM-powered code improvements
- Syntax validation before applying
- Automatic backups
- Safe editing with AST parsing
- Configurable fix types:
  - Bug fixes
  - Complexity reduction
  - Code refactoring
  - Adding docstrings
  - Maintainability improvements

### Git Integration
- Automatic staging and commits
- Descriptive commit messages
- Batch commit support
- Commit history tracking
- Repository status monitoring

### Testing
- Automatic test generation
- LLM-powered test cases
- Coverage descriptions
- pytest-compatible output

### Logging & Monitoring
- Comprehensive JSON logging
- Operation statistics
- Search functionality
- Log filtering by type
- Success/failure tracking
- Web dashboard for visualization

### Safety Features
- Automatic file backups
- Syntax validation
- Dry-run mode
- Git rollback capability
- Error handling and recovery

## Installation

See `QUICKSTART.md` for detailed setup instructions.

Quick install:
```bash
# Backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install

# Ollama
ollama pull codellama:7b-instruct
```

## Testing

Run the demo example:
```bash
python src/main.py analyze --repo examples/
python src/main.py fix --repo examples/ --dry-run
```

## Performance

- Supports repositories of any size
- Configurable file size limits
- Efficient embedding indexing with ChromaDB
- Parallel analysis capabilities
- Background job support in API

## Security

- Local LLM execution (no data leaves your machine)
- File backups before modifications
- Syntax validation
- Configurable file exclusions
- Safe git operations

## Future Enhancements

Potential areas for expansion:
1. Support for more programming languages
2. Integration with more LLM providers
3. Advanced metrics and reporting
4. CI/CD integration
5. Team collaboration features
6. Custom rule definitions
7. Machine learning model fine-tuning
8. IDE plugins

## License

MIT License

## Contributing

The project is structured for easy extension:
- Add new issue detectors in `issue_detector.py`
- Add new fix strategies in `llm_agent.py`
- Add new language support in `repo_parser.py`
- Extend the API in `api_server.py`
- Add new UI components in `frontend/src/`

## Support

- Documentation: See README.md and QUICKSTART.md
- Logs: Check `logs/selfheal_log.json`
- Issues: Review error messages in logs
- Configuration: Edit `config/settings.json`

## Acknowledgments

Built with:
- Ollama for local LLM inference
- ChromaDB for vector storage
- MaterialUI for beautiful components
- FastAPI for robust API
- Pylint and Radon for code analysis

---

Project completed: October 11, 2025
Status: Production-ready
Version: 1.0.0
