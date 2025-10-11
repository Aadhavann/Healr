"""
Test generator module for creating automated test cases using LLM.
"""

import os
import ast
from typing import Dict, List, Optional
from llm_agent import LLMAgent
from code_editor import CodeEditor


class TestGenerator:
    """Generates test cases for code using LLM."""

    def __init__(self):
        """Initialize the test generator."""
        self.llm_agent = LLMAgent()
        self.code_editor = CodeEditor()

    def generate_tests_for_file(self, file_path: str) -> Dict[str, any]:
        """
        Generate test cases for an entire file.

        Args:
            file_path: Path to the file to generate tests for

        Returns:
            Dictionary with test generation results
        """
        result = {
            'success': False,
            'test_file_path': None,
            'test_code': None,
            'error': None
        }

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Generate language extension
            extension = os.path.splitext(file_path)[1]
            language = self._get_language(extension)

            # Generate tests using LLM
            test_result = self.llm_agent.generate_tests(file_path, code, language)

            if not test_result.get('code'):
                result['error'] = "LLM did not generate test code"
                return result

            # Determine test file path
            test_file_path = self._get_test_file_path(file_path)

            result['test_code'] = test_result.get('code')
            result['test_file_path'] = test_file_path
            result['coverage'] = test_result.get('coverage', '')
            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def generate_tests_for_function(self, file_path: str, function_name: str) -> Dict[str, any]:
        """
        Generate test cases for a specific function.

        Args:
            file_path: Path to the file containing the function
            function_name: Name of the function to test

        Returns:
            Dictionary with test generation results
        """
        result = {
            'success': False,
            'test_code': None,
            'error': None
        }

        try:
            # Extract function code
            function_code = self._extract_function(file_path, function_name)

            if not function_code:
                result['error'] = f"Function '{function_name}' not found"
                return result

            # Generate language
            extension = os.path.splitext(file_path)[1]
            language = self._get_language(extension)

            # Generate tests using LLM
            test_result = self.llm_agent.generate_tests(
                f"{file_path}:{function_name}",
                function_code,
                language
            )

            result['test_code'] = test_result.get('code')
            result['coverage'] = test_result.get('coverage', '')
            result['success'] = bool(test_result.get('code'))

        except Exception as e:
            result['error'] = str(e)

        return result

    def save_tests(self, test_file_path: str, test_code: str, append: bool = False) -> Dict[str, any]:
        """
        Save generated test code to a file.

        Args:
            test_file_path: Path to the test file
            test_code: Test code to save
            append: Whether to append to existing file

        Returns:
            Dictionary with save result
        """
        result = {
            'success': False,
            'error': None
        }

        try:
            # Ensure test directory exists
            os.makedirs(os.path.dirname(test_file_path), exist_ok=True)

            if append and os.path.exists(test_file_path):
                # Append to existing file
                with open(test_file_path, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + test_code)
            else:
                # Create new file
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(test_code)

            result['success'] = True
            result['file_path'] = test_file_path

        except Exception as e:
            result['error'] = str(e)

        return result

    def _extract_function(self, file_path: str, function_name: str) -> Optional[str]:
        """
        Extract a specific function from a Python file.

        Args:
            file_path: Path to the file
            function_name: Name of the function

        Returns:
            Function code as string or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Get function code
                    lines = content.split('\n')
                    function_lines = lines[node.lineno - 1:node.end_lineno]
                    return '\n'.join(function_lines)

            return None

        except Exception:
            return None

    def _get_test_file_path(self, file_path: str) -> str:
        """
        Determine the appropriate test file path.

        Args:
            file_path: Path to the source file

        Returns:
            Path to the test file
        """
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)

        # Create tests directory in parent directory
        parent_dir = os.path.dirname(directory) if directory else '.'
        tests_dir = os.path.join(parent_dir, 'tests')

        # Generate test filename
        test_filename = f"test_{name}{ext}"
        test_file_path = os.path.join(tests_dir, test_filename)

        return test_file_path

    def _get_language(self, extension: str) -> str:
        """
        Get programming language from file extension.

        Args:
            extension: File extension

        Returns:
            Language name
        """
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }

        return language_map.get(extension, 'python')

    def generate_and_save_tests(self, file_path: str, append: bool = False) -> Dict[str, any]:
        """
        Generate and save tests for a file in one operation.

        Args:
            file_path: Path to the file
            append: Whether to append to existing test file

        Returns:
            Dictionary with operation result
        """
        # Generate tests
        gen_result = self.generate_tests_for_file(file_path)

        if not gen_result['success']:
            return gen_result

        # Save tests
        save_result = self.save_tests(
            gen_result['test_file_path'],
            gen_result['test_code'],
            append
        )

        # Combine results
        return {
            'success': save_result['success'],
            'test_file_path': gen_result['test_file_path'],
            'test_code': gen_result['test_code'],
            'coverage': gen_result.get('coverage'),
            'error': save_result.get('error') or gen_result.get('error')
        }

    def list_testable_functions(self, file_path: str) -> List[str]:
        """
        List all functions in a file that can be tested.

        Args:
            file_path: Path to the Python file

        Returns:
            List of function names
        """
        functions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Skip private functions (starting with _) unless they're magic methods
                    if not node.name.startswith('_') or node.name.startswith('__'):
                        functions.append(node.name)

        except Exception:
            pass

        return functions


if __name__ == "__main__":
    # Example usage
    generator = TestGenerator()

    # Generate tests for a file
    result = generator.generate_tests_for_file("src/repo_parser.py")

    if result['success']:
        print(f"Generated tests:")
        print(result['test_code'][:500])
        print(f"\nTest file path: {result['test_file_path']}")
        print(f"Coverage: {result.get('coverage', 'N/A')}")
    else:
        print(f"Error: {result['error']}")
