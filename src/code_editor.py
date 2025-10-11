"""
Code editor module for safely applying LLM-suggested code changes.
"""

import os
import ast
import shutil
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path


class CodeEditor:
    """Safely edits code files with backup and validation."""

    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize the code editor.

        Args:
            backup_dir: Directory to store file backups
        """
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def create_backup(self, file_path: str) -> str:
        """
        Create a backup of a file before editing.

        Args:
            file_path: Path to the file

        Returns:
            Path to the backup file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create timestamp-based backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.basename(file_path)
        backup_name = f"{file_name}.{timestamp}.bak"

        # Create subdirectory structure in backup dir
        rel_path = os.path.dirname(file_path)
        backup_subdir = os.path.join(self.backup_dir, rel_path.replace(":", "").replace("\\", "_"))
        os.makedirs(backup_subdir, exist_ok=True)

        backup_path = os.path.join(backup_subdir, backup_name)

        # Copy file to backup location
        shutil.copy2(file_path, backup_path)

        return backup_path

    def validate_python_syntax(self, code: str) -> Dict[str, any]:
        """
        Validate Python code syntax using AST.

        Args:
            code: Python code to validate

        Returns:
            Dictionary with validation result
        """
        result = {
            'valid': False,
            'error': None,
            'line': None,
            'offset': None
        }

        try:
            ast.parse(code)
            result['valid'] = True
        except SyntaxError as e:
            result['error'] = str(e.msg)
            result['line'] = e.lineno
            result['offset'] = e.offset
        except Exception as e:
            result['error'] = str(e)

        return result

    def apply_edit(self, file_path: str, new_content: str, validate: bool = True, create_backup: bool = True) -> Dict[str, any]:
        """
        Apply an edit to a file with validation and backup.

        Args:
            file_path: Path to the file to edit
            new_content: New content for the file
            validate: Whether to validate syntax before applying
            create_backup: Whether to create a backup before editing

        Returns:
            Dictionary with edit result
        """
        result = {
            'success': False,
            'backup_path': None,
            'error': None,
            'validation': None
        }

        try:
            # Create backup if requested
            if create_backup:
                result['backup_path'] = self.create_backup(file_path)

            # Validate syntax for Python files
            if validate and file_path.endswith('.py'):
                validation = self.validate_python_syntax(new_content)
                result['validation'] = validation

                if not validation['valid']:
                    result['error'] = f"Syntax validation failed: {validation['error']}"
                    return result

            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

            # Restore from backup if edit failed
            if result['backup_path'] and os.path.exists(result['backup_path']):
                try:
                    shutil.copy2(result['backup_path'], file_path)
                    result['restored'] = True
                except:
                    pass

        return result

    def apply_partial_edit(self, file_path: str, old_code: str, new_code: str,
                          validate: bool = True, create_backup: bool = True) -> Dict[str, any]:
        """
        Apply a partial edit by replacing old code with new code.

        Args:
            file_path: Path to the file to edit
            old_code: Code to replace
            new_code: Replacement code
            validate: Whether to validate syntax after edit
            create_backup: Whether to create a backup

        Returns:
            Dictionary with edit result
        """
        result = {
            'success': False,
            'backup_path': None,
            'error': None,
            'changes_made': False
        }

        try:
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Check if old code exists
            if old_code not in current_content:
                result['error'] = "Old code not found in file"
                return result

            # Replace old code with new code
            new_content = current_content.replace(old_code, new_code, 1)

            # Check if any changes were made
            if new_content == current_content:
                result['error'] = "No changes were made"
                return result

            result['changes_made'] = True

            # Apply the edit
            edit_result = self.apply_edit(file_path, new_content, validate, create_backup)
            result.update(edit_result)

        except Exception as e:
            result['error'] = str(e)

        return result

    def apply_line_edit(self, file_path: str, line_number: int, new_line: str,
                       validate: bool = True, create_backup: bool = True) -> Dict[str, any]:
        """
        Replace a specific line in a file.

        Args:
            file_path: Path to the file
            line_number: Line number to replace (1-indexed)
            new_line: New line content
            validate: Whether to validate syntax
            create_backup: Whether to create backup

        Returns:
            Dictionary with edit result
        """
        result = {
            'success': False,
            'backup_path': None,
            'error': None
        }

        try:
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Check line number validity
            if line_number < 1 or line_number > len(lines):
                result['error'] = f"Invalid line number: {line_number} (file has {len(lines)} lines)"
                return result

            # Replace the line
            lines[line_number - 1] = new_line if new_line.endswith('\n') else new_line + '\n'

            # Join lines and apply edit
            new_content = ''.join(lines)
            edit_result = self.apply_edit(file_path, new_content, validate, create_backup)
            result.update(edit_result)

        except Exception as e:
            result['error'] = str(e)

        return result

    def apply_function_edit(self, file_path: str, function_name: str, new_function_code: str,
                           validate: bool = True, create_backup: bool = True) -> Dict[str, any]:
        """
        Replace an entire function in a Python file.

        Args:
            file_path: Path to the Python file
            function_name: Name of the function to replace
            new_function_code: New function code
            validate: Whether to validate syntax
            create_backup: Whether to create backup

        Returns:
            Dictionary with edit result
        """
        result = {
            'success': False,
            'backup_path': None,
            'error': None
        }

        try:
            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse AST to find function
            tree = ast.parse(content)
            function_node = None

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    function_node = node
                    break

            if not function_node:
                result['error'] = f"Function '{function_name}' not found in file"
                return result

            # Get line numbers of the function
            start_line = function_node.lineno
            end_line = function_node.end_lineno

            # Split content into lines
            lines = content.split('\n')

            # Replace function (adjusting for 0-indexed list)
            new_lines = (
                lines[:start_line - 1] +
                [new_function_code] +
                lines[end_line:]
            )

            new_content = '\n'.join(new_lines)

            # Apply the edit
            edit_result = self.apply_edit(file_path, new_content, validate, create_backup)
            result.update(edit_result)

        except Exception as e:
            result['error'] = str(e)

        return result

    def restore_from_backup(self, file_path: str, backup_path: str) -> bool:
        """
        Restore a file from a backup.

        Args:
            file_path: Path to the file to restore
            backup_path: Path to the backup file

        Returns:
            True if restoration was successful
        """
        try:
            if not os.path.exists(backup_path):
                return False

            shutil.copy2(backup_path, file_path)
            return True

        except Exception:
            return False

    def get_backups(self, file_path: str) -> list:
        """
        Get all backups for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of backup file paths sorted by timestamp (newest first)
        """
        file_name = os.path.basename(file_path)
        rel_path = os.path.dirname(file_path)
        backup_subdir = os.path.join(self.backup_dir, rel_path.replace(":", "").replace("\\", "_"))

        if not os.path.exists(backup_subdir):
            return []

        backups = []
        for backup_file in os.listdir(backup_subdir):
            if backup_file.startswith(file_name) and backup_file.endswith('.bak'):
                backup_path = os.path.join(backup_subdir, backup_file)
                backups.append({
                    'path': backup_path,
                    'timestamp': os.path.getmtime(backup_path),
                    'size': os.path.getsize(backup_path)
                })

        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)

        return backups

    def compare_with_backup(self, file_path: str, backup_path: str) -> Dict[str, any]:
        """
        Compare current file with a backup.

        Args:
            file_path: Path to the current file
            backup_path: Path to the backup file

        Returns:
            Dictionary with comparison info
        """
        result = {
            'identical': False,
            'current_lines': 0,
            'backup_lines': 0,
            'size_difference': 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()

            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()

            result['identical'] = current_content == backup_content
            result['current_lines'] = len(current_content.split('\n'))
            result['backup_lines'] = len(backup_content.split('\n'))
            result['size_difference'] = len(current_content) - len(backup_content)

        except Exception as e:
            result['error'] = str(e)

        return result


if __name__ == "__main__":
    # Example usage
    editor = CodeEditor()

    # Create a test file
    test_file = "test_example.py"
    with open(test_file, 'w') as f:
        f.write("def hello():\n    print('Hello, World!')\n")

    # Apply an edit
    new_content = "def hello():\n    print('Hello, Universe!')\n"
    result = editor.apply_edit(test_file, new_content)

    if result['success']:
        print(f"Edit successful. Backup at: {result['backup_path']}")
    else:
        print(f"Edit failed: {result['error']}")

    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
