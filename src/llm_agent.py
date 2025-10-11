"""
LLM agent module for connecting to local LLMs and generating code improvements.
"""

import json
import re
from typing import Dict, List, Optional
import requests


class LLMAgent:
    """Manages interactions with local LLM (Ollama or LM Studio)."""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        Initialize the LLM agent.

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        llm_config = config['llm']
        self.provider = llm_config['provider']
        self.base_url = llm_config['base_url']
        self.model = llm_config['model']
        self.temperature = llm_config['temperature']
        self.max_tokens = llm_config['max_tokens']
        self.timeout = llm_config['timeout']

        # Prompt templates
        self.templates = {
            'code_improvement': """You are an expert code reviewer and improver. Analyze the following code and suggest improvements.

File: {file_path}
Issue: {issue_description}

Current Code:
```{language}
{code}
```

Please provide:
1. A clear explanation of the problem
2. The improved code
3. A brief description of what was changed

Format your response as:
EXPLANATION:
[Your explanation here]

IMPROVED_CODE:
```{language}
[Your improved code here]
```

CHANGES:
[Brief description of changes]
""",

            'bug_fix': """You are an expert debugger. Analyze the following code and fix the identified bug.

File: {file_path}
Bug: {issue_description}

Current Code:
```{language}
{code}
```

Please provide:
1. Root cause analysis
2. The fixed code
3. Explanation of the fix

Format your response as:
ROOT_CAUSE:
[Your analysis here]

FIXED_CODE:
```{language}
[Your fixed code here]
```

FIX_EXPLANATION:
[Explanation of fix]
""",

            'refactor': """You are an expert at code refactoring. Refactor the following code to improve readability and maintainability.

File: {file_path}
Refactoring Goal: {issue_description}

Current Code:
```{language}
{code}
```

Please provide:
1. Refactoring strategy
2. The refactored code
3. Benefits of the refactoring

Format your response as:
STRATEGY:
[Your strategy here]

REFACTORED_CODE:
```{language}
[Your refactored code here]
```

BENEFITS:
[Benefits of refactoring]
""",

            'add_docstrings': """You are an expert at writing clear, concise documentation. Add comprehensive docstrings to the following code.

File: {file_path}

Current Code:
```{language}
{code}
```

Please add:
1. Module-level docstring if missing
2. Function/class docstrings following best practices
3. Parameter and return value documentation

Format your response as:
DOCUMENTED_CODE:
```{language}
[Your documented code here]
```

DOCUMENTATION_NOTES:
[Any additional notes about the documentation]
""",

            'test_generation': """You are an expert at writing comprehensive test cases. Generate test cases for the following code.

File: {file_path}

Code to Test:
```{language}
{code}
```

Please provide:
1. Comprehensive test cases covering edge cases
2. Test setup and fixtures if needed
3. Assertions for expected behavior

Format your response as:
TEST_CODE:
```{language}
[Your test code here]
```

TEST_COVERAGE:
[Description of what the tests cover]
"""
        }

    def query(self, prompt: str, stream: bool = False) -> str:
        """
        Send a query to the local LLM.

        Args:
            prompt: The prompt to send
            stream: Whether to stream the response

        Returns:
            LLM response text
        """
        if self.provider == "ollama":
            return self._query_ollama(prompt, stream)
        elif self.provider == "lm_studio":
            return self._query_lm_studio(prompt, stream)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _query_ollama(self, prompt: str, stream: bool = False) -> str:
        """
        Query Ollama API.

        Args:
            prompt: The prompt to send
            stream: Whether to stream the response

        Returns:
            Response text
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            if stream:
                # Handle streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        full_response += data.get('response', '')
                        if data.get('done', False):
                            break
                return full_response
            else:
                # Handle non-streaming response
                result = response.json()
                return result.get('response', '')

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API error: {str(e)}")

    def _query_lm_studio(self, prompt: str, stream: bool = False) -> str:
        """
        Query LM Studio API (OpenAI-compatible).

        Args:
            prompt: The prompt to send
            stream: Whether to stream the response

        Returns:
            Response text
        """
        url = f"{self.base_url}/v1/completions"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0].get('text', '')
            return ""

        except requests.exceptions.RequestException as e:
            raise Exception(f"LM Studio API error: {str(e)}")

    def improve_code(self, file_path: str, code: str, issue_description: str, language: str = "python") -> Dict[str, str]:
        """
        Generate code improvements based on an issue.

        Args:
            file_path: Path to the file
            code: Current code
            issue_description: Description of the issue
            language: Programming language

        Returns:
            Dictionary with explanation, improved code, and changes
        """
        prompt = self.templates['code_improvement'].format(
            file_path=file_path,
            issue_description=issue_description,
            code=code,
            language=language
        )

        response = self.query(prompt)
        return self._parse_response(response, 'improvement')

    def fix_bug(self, file_path: str, code: str, bug_description: str, language: str = "python") -> Dict[str, str]:
        """
        Generate bug fix.

        Args:
            file_path: Path to the file
            code: Current code
            bug_description: Description of the bug
            language: Programming language

        Returns:
            Dictionary with root cause, fixed code, and explanation
        """
        prompt = self.templates['bug_fix'].format(
            file_path=file_path,
            issue_description=bug_description,
            code=code,
            language=language
        )

        response = self.query(prompt)
        return self._parse_response(response, 'bug_fix')

    def refactor_code(self, file_path: str, code: str, refactoring_goal: str, language: str = "python") -> Dict[str, str]:
        """
        Generate refactored code.

        Args:
            file_path: Path to the file
            code: Current code
            refactoring_goal: Goal of refactoring
            language: Programming language

        Returns:
            Dictionary with strategy, refactored code, and benefits
        """
        prompt = self.templates['refactor'].format(
            file_path=file_path,
            issue_description=refactoring_goal,
            code=code,
            language=language
        )

        response = self.query(prompt)
        return self._parse_response(response, 'refactor')

    def add_docstrings(self, file_path: str, code: str, language: str = "python") -> Dict[str, str]:
        """
        Generate code with added docstrings.

        Args:
            file_path: Path to the file
            code: Current code
            language: Programming language

        Returns:
            Dictionary with documented code and notes
        """
        prompt = self.templates['add_docstrings'].format(
            file_path=file_path,
            code=code,
            language=language
        )

        response = self.query(prompt)
        return self._parse_response(response, 'docstrings')

    def generate_tests(self, file_path: str, code: str, language: str = "python") -> Dict[str, str]:
        """
        Generate test cases for code.

        Args:
            file_path: Path to the file
            code: Code to test
            language: Programming language

        Returns:
            Dictionary with test code and coverage description
        """
        prompt = self.templates['test_generation'].format(
            file_path=file_path,
            code=code,
            language=language
        )

        response = self.query(prompt)
        return self._parse_response(response, 'test')

    def _parse_response(self, response: str, response_type: str) -> Dict[str, str]:
        """
        Parse LLM response into structured format.

        Args:
            response: Raw LLM response
            response_type: Type of response (improvement, bug_fix, refactor, etc.)

        Returns:
            Parsed response dictionary
        """
        result = {
            'raw_response': response,
            'code': '',
            'explanation': ''
        }

        # Extract code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            result['code'] = code_blocks[0].strip()

        # Extract sections based on response type
        if response_type == 'improvement':
            explanation_match = re.search(r'EXPLANATION:(.*?)(?:IMPROVED_CODE:|$)', response, re.DOTALL | re.IGNORECASE)
            if explanation_match:
                result['explanation'] = explanation_match.group(1).strip()

            changes_match = re.search(r'CHANGES:(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if changes_match:
                result['changes'] = changes_match.group(1).strip()

        elif response_type == 'bug_fix':
            root_cause_match = re.search(r'ROOT_CAUSE:(.*?)(?:FIXED_CODE:|$)', response, re.DOTALL | re.IGNORECASE)
            if root_cause_match:
                result['root_cause'] = root_cause_match.group(1).strip()

            fix_match = re.search(r'FIX_EXPLANATION:(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if fix_match:
                result['explanation'] = fix_match.group(1).strip()

        elif response_type == 'refactor':
            strategy_match = re.search(r'STRATEGY:(.*?)(?:REFACTORED_CODE:|$)', response, re.DOTALL | re.IGNORECASE)
            if strategy_match:
                result['strategy'] = strategy_match.group(1).strip()

            benefits_match = re.search(r'BENEFITS:(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if benefits_match:
                result['benefits'] = benefits_match.group(1).strip()

        elif response_type == 'docstrings':
            notes_match = re.search(r'DOCUMENTATION_NOTES:(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if notes_match:
                result['notes'] = notes_match.group(1).strip()

        elif response_type == 'test':
            coverage_match = re.search(r'TEST_COVERAGE:(.*?)$', response, re.DOTALL | re.IGNORECASE)
            if coverage_match:
                result['coverage'] = coverage_match.group(1).strip()

        return result


if __name__ == "__main__":
    # Example usage
    agent = LLMAgent()

    sample_code = """
def calculate(x, y):
    return x + y
"""

    try:
        result = agent.improve_code(
            "example.py",
            sample_code,
            "Add input validation and error handling",
            "python"
        )

        print("Improved Code:")
        print(result.get('code', 'No code generated'))
        print("\nExplanation:")
        print(result.get('explanation', 'No explanation'))

    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure Ollama is running with: ollama serve")
