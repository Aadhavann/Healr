"""
Repository parser module for walking through code repositories and collecting source files.
"""

import os
from pathlib import Path
from typing import List, Dict, Set
import json


class RepoParser:
    """Parses a repository and collects relevant source files."""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        Initialize the repository parser.

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.supported_extensions: Set[str] = set(config['repository']['supported_extensions'])
        self.exclude_dirs: Set[str] = set(config['repository']['exclude_dirs'])
        self.exclude_files: List[str] = config['repository']['exclude_files']
        self.max_file_size_kb: int = config['repository']['max_file_size_kb']

    def parse_repository(self, repo_path: str) -> List[Dict[str, str]]:
        """
        Walk through repository and collect all relevant source files.

        Args:
            repo_path: Path to the repository

        Returns:
            List of dictionaries containing file paths and content
        """
        if not os.path.exists(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")

        files_data = []
        repo_path = os.path.abspath(repo_path)

        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]

            for file in files:
                file_path = os.path.join(root, file)

                if self._should_include_file(file_path):
                    try:
                        content = self._read_file(file_path)
                        relative_path = os.path.relpath(file_path, repo_path)

                        files_data.append({
                            'path': file_path,
                            'relative_path': relative_path,
                            'content': content,
                            'extension': Path(file_path).suffix,
                            'size_kb': os.path.getsize(file_path) / 1024
                        })
                    except Exception as e:
                        print(f"Warning: Could not read {file_path}: {str(e)}")

        return files_data

    def _should_exclude_dir(self, dirname: str) -> bool:
        """
        Check if directory should be excluded.

        Args:
            dirname: Directory name

        Returns:
            True if directory should be excluded
        """
        return dirname in self.exclude_dirs or dirname.startswith('.')

    def _should_include_file(self, file_path: str) -> bool:
        """
        Check if file should be included based on extension, size, and exclusion patterns.

        Args:
            file_path: Full path to file

        Returns:
            True if file should be included
        """
        # Check extension
        extension = Path(file_path).suffix
        if extension not in self.supported_extensions:
            return False

        # Check file size
        try:
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb > self.max_file_size_kb:
                return False
        except OSError:
            return False

        # Check exclusion patterns
        filename = os.path.basename(file_path)
        for pattern in self.exclude_files:
            if self._matches_pattern(filename, pattern):
                return False

        return True

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """
        Check if filename matches exclusion pattern.

        Args:
            filename: Name of the file
            pattern: Exclusion pattern (supports * wildcard)

        Returns:
            True if filename matches pattern
        """
        if '*' in pattern:
            parts = pattern.split('*')
            if len(parts) == 2:
                prefix, suffix = parts
                return filename.startswith(prefix) and filename.endswith(suffix)
        return filename == pattern

    def _read_file(self, file_path: str) -> str:
        """
        Read file content with proper encoding handling.

        Args:
            file_path: Path to file

        Returns:
            File content as string
        """
        encodings = ['utf-8', 'latin-1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError(f"Could not decode file {file_path} with any supported encoding")

    def get_files_by_extension(self, files_data: List[Dict[str, str]], extension: str) -> List[Dict[str, str]]:
        """
        Filter files by extension.

        Args:
            files_data: List of file data dictionaries
            extension: File extension to filter by

        Returns:
            Filtered list of files
        """
        return [f for f in files_data if f['extension'] == extension]

    def get_file_statistics(self, files_data: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Generate statistics about parsed files.

        Args:
            files_data: List of file data dictionaries

        Returns:
            Dictionary containing statistics
        """
        stats = {
            'total_files': len(files_data),
            'total_size_kb': sum(f['size_kb'] for f in files_data),
            'files_by_extension': {},
            'largest_files': sorted(files_data, key=lambda x: x['size_kb'], reverse=True)[:5]
        }

        for file_data in files_data:
            ext = file_data['extension']
            if ext not in stats['files_by_extension']:
                stats['files_by_extension'][ext] = 0
            stats['files_by_extension'][ext] += 1

        return stats


if __name__ == "__main__":
    # Example usage
    parser = RepoParser()

    # Parse current directory
    files = parser.parse_repository(".")
    stats = parser.get_file_statistics(files)

    print(f"Found {stats['total_files']} files")
    print(f"Total size: {stats['total_size_kb']:.2f} KB")
    print(f"Files by extension: {stats['files_by_extension']}")
