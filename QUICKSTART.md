# Healr Quick Start Guide

Get started with Healr in minutes!

## Prerequisites

1. Python 3.10+
2. Node.js 16+
3. Ollama (download from https://ollama.ai)

## Step 1: Install Ollama and Pull a Model

```bash
# Install Ollama (visit https://ollama.ai for your platform)

# Pull a code model
ollama pull codellama:7b-instruct

# Or use StarCoder2
ollama pull starcoder2:7b

# Verify it's running
ollama list
```

## Step 2: Set Up Backend

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Set Up Frontend (Optional)

```bash
cd frontend
npm install
cd ..
```

## Step 4: Run Your First Analysis

### Command Line

```bash
# Analyze a repository
python src/main.py analyze --repo /path/to/your/repo

# Fix issues (dry run first)
python src/main.py fix --repo /path/to/your/repo --dry-run

# Apply fixes
python src/main.py fix --repo /path/to/your/repo

# Generate tests
python src/main.py test --repo /path/to/your/repo

# Generate report
python src/main.py report --repo /path/to/your/repo
```

### Web Dashboard

```bash
# Terminal 1: Start backend
python src/api_server.py

# Terminal 2: Start frontend
cd frontend
npm start
```

Then visit http://localhost:3000

## Step 5: Try the Example

```bash
# Create a sample Python file with issues
mkdir example_project
cd example_project

# Create a file with intentional issues
cat > example.py << 'EOF'
def calculate(x,y):
    result=x+y
    return result

def complex_function(a, b, c, d, e, f):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            return a + b + c + d + e + f
    return 0
EOF

# Analyze it
python ../src/main.py analyze --repo .

# Fix it
python ../src/main.py fix --repo .

# See the improvements!
cat example.py
```

## Common Issues

### Ollama Not Running

```bash
# Make sure Ollama is running
ollama serve

# In another terminal, test it
ollama run codellama:7b-instruct "Hello"
```

### Module Not Found

```bash
# Make sure virtual environment is activated
pip install -r requirements.txt
```

### Port Already in Use

Edit `config/settings.json` and change the port:

```json
{
  "server": {
    "port": 8001
  }
}
```

## Next Steps

- Read the full README.md for detailed documentation
- Explore the web dashboard at http://localhost:3000
- Check the logs in `logs/selfheal_log.json`
- View backups in `backups/`
- Customize settings in `config/settings.json`

## Example Configuration

Edit `config/settings.json` to customize:

```json
{
  "llm": {
    "model": "codellama:7b-instruct",
    "temperature": 0.3
  },
  "code_quality": {
    "max_complexity": 10,
    "min_maintainability_index": 20
  }
}
```

## Tips

1. **Start with dry-run**: Always use `--dry-run` first to preview changes
2. **Use Git**: Initialize a git repository before running fixes
3. **Check backups**: All original files are backed up in `backups/`
4. **Review logs**: Check `logs/selfheal_log.json` for detailed operation logs
5. **Adjust thresholds**: Customize complexity and quality thresholds in config

## Support

- Check the logs for detailed error messages
- Ensure Ollama is running with `ollama list`
- Verify Python dependencies with `pip list`
- Check the API is running with `curl http://localhost:8000/health`

Happy coding!
