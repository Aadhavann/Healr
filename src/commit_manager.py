"""
Git commit manager module for automating commits with descriptive messages.
"""

import os
import json
from typing import List, Dict, Optional
from git import Repo, GitCommandError


class CommitManager:
    """Manages Git operations for the self-healing system."""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        Initialize the commit manager.

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        git_config = config['git']
        self.auto_commit = git_config['auto_commit']
        self.commit_message_template = git_config['commit_message_template']
        self.max_changes_per_commit = git_config['max_changes_per_commit']

    def init_repo(self, repo_path: str) -> Optional[Repo]:
        """
        Initialize or get a Git repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Repo object or None if not a git repository
        """
        try:
            repo = Repo(repo_path)
            return repo
        except Exception:
            return None

    def is_git_repo(self, repo_path: str) -> bool:
        """
        Check if a directory is a Git repository.

        Args:
            repo_path: Path to check

        Returns:
            True if it's a Git repository
        """
        return self.init_repo(repo_path) is not None

    def stage_file(self, repo: Repo, file_path: str) -> Dict[str, any]:
        """
        Stage a file for commit.

        Args:
            repo: Git repository object
            file_path: Path to the file to stage

        Returns:
            Dictionary with result
        """
        result = {
            'success': False,
            'error': None
        }

        try:
            repo.index.add([file_path])
            result['success'] = True
        except GitCommandError as e:
            result['error'] = str(e)

        return result

    def stage_files(self, repo: Repo, file_paths: List[str]) -> Dict[str, any]:
        """
        Stage multiple files for commit.

        Args:
            repo: Git repository object
            file_paths: List of file paths to stage

        Returns:
            Dictionary with result
        """
        result = {
            'success': False,
            'staged_files': [],
            'failed_files': [],
            'error': None
        }

        for file_path in file_paths:
            stage_result = self.stage_file(repo, file_path)
            if stage_result['success']:
                result['staged_files'].append(file_path)
            else:
                result['failed_files'].append(file_path)

        result['success'] = len(result['failed_files']) == 0

        return result

    def create_commit(self, repo: Repo, message: str, author: Optional[str] = None) -> Dict[str, any]:
        """
        Create a commit with staged files.

        Args:
            repo: Git repository object
            message: Commit message
            author: Optional author string

        Returns:
            Dictionary with commit result
        """
        result = {
            'success': False,
            'commit_hash': None,
            'error': None
        }

        try:
            # Check if there are changes to commit
            if not repo.is_dirty() and len(repo.untracked_files) == 0:
                result['error'] = "No changes to commit"
                return result

            # Create commit
            commit = repo.index.commit(message, author=author)
            result['success'] = True
            result['commit_hash'] = commit.hexsha
            result['commit_message'] = message

        except GitCommandError as e:
            result['error'] = str(e)

        return result

    def generate_commit_message(self, file_path: str, action: str, details: Optional[str] = None) -> str:
        """
        Generate a descriptive commit message.

        Args:
            file_path: Path to the modified file
            action: Action performed (e.g., "Fix bug", "Refactor", "Add docstrings")
            details: Optional additional details

        Returns:
            Formatted commit message
        """
        file_name = os.path.basename(file_path)

        # Use template if available
        message = self.commit_message_template.format(
            action=action,
            file=file_name
        )

        # Add details if provided
        if details:
            message += f"\n\n{details}"

        # Add footer
        message += "\n\nGenerated with Healr - AI-Powered Code Self-Healing System"

        return message

    def commit_fix(self, repo: Repo, file_path: str, issue_type: str,
                   issue_description: str, fix_summary: Optional[str] = None) -> Dict[str, any]:
        """
        Commit a code fix with a descriptive message.

        Args:
            repo: Git repository object
            file_path: Path to the fixed file
            issue_type: Type of issue (e.g., "bug", "complexity", "style")
            issue_description: Description of the issue
            fix_summary: Optional summary of the fix

        Returns:
            Dictionary with commit result
        """
        # Stage the file
        stage_result = self.stage_file(repo, file_path)
        if not stage_result['success']:
            return stage_result

        # Generate commit message
        action_map = {
            'bug': 'Fix bug',
            'complexity': 'Reduce complexity',
            'style': 'Improve code style',
            'docstring': 'Add docstrings',
            'refactor': 'Refactor code',
            'maintainability': 'Improve maintainability'
        }

        action = action_map.get(issue_type, 'Improve code')
        details = f"Issue: {issue_description}"

        if fix_summary:
            details += f"\nFix: {fix_summary}"

        message = self.generate_commit_message(file_path, action, details)

        # Create commit
        return self.create_commit(repo, message)

    def commit_batch_fixes(self, repo: Repo, fixes: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """
        Commit multiple fixes, grouping them according to max_changes_per_commit.

        Args:
            repo: Git repository object
            fixes: List of fix dictionaries with file_path, issue_type, etc.

        Returns:
            List of commit results
        """
        results = []

        # Group fixes by max_changes_per_commit
        for i in range(0, len(fixes), self.max_changes_per_commit):
            batch = fixes[i:i + self.max_changes_per_commit]

            # Stage all files in batch
            file_paths = [fix['file_path'] for fix in batch]
            stage_result = self.stage_files(repo, file_paths)

            if not stage_result['success']:
                results.append(stage_result)
                continue

            # Generate batch commit message
            if len(batch) == 1:
                fix = batch[0]
                message = self.generate_commit_message(
                    fix['file_path'],
                    fix.get('action', 'Improve code'),
                    fix.get('description')
                )
            else:
                message = f"Fix {len(batch)} code quality issues\n\n"
                for fix in batch:
                    file_name = os.path.basename(fix['file_path'])
                    message += f"- {file_name}: {fix.get('description', 'Improved')}\n"
                message += "\nGenerated with Healr - AI-Powered Code Self-Healing System"

            # Create commit
            commit_result = self.create_commit(repo, message)
            results.append(commit_result)

        return results

    def get_recent_commits(self, repo: Repo, max_count: int = 10) -> List[Dict[str, any]]:
        """
        Get recent commits from the repository.

        Args:
            repo: Git repository object
            max_count: Maximum number of commits to retrieve

        Returns:
            List of commit information dictionaries
        """
        commits = []

        try:
            for commit in repo.iter_commits(max_count=max_count):
                commits.append({
                    'hash': commit.hexsha,
                    'short_hash': commit.hexsha[:7],
                    'message': commit.message,
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'files_changed': len(commit.stats.files)
                })
        except Exception as e:
            return []

        return commits

    def get_file_status(self, repo: Repo) -> Dict[str, List[str]]:
        """
        Get the current status of files in the repository.

        Args:
            repo: Git repository object

        Returns:
            Dictionary with categorized file lists
        """
        status = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }

        try:
            # Get modified and staged files
            changed_files = repo.index.diff(None)
            for item in changed_files:
                if item.change_type == 'M':
                    status['modified'].append(item.a_path)
                elif item.change_type == 'D':
                    status['deleted'].append(item.a_path)

            # Get untracked files
            status['untracked'] = repo.untracked_files

        except Exception:
            pass

        return status

    def get_diff(self, repo: Repo, file_path: Optional[str] = None) -> str:
        """
        Get git diff for the repository or a specific file.

        Args:
            repo: Git repository object
            file_path: Optional path to specific file

        Returns:
            Diff output as string
        """
        try:
            if file_path:
                return repo.git.diff(file_path)
            else:
                return repo.git.diff()
        except Exception:
            return ""

    def rollback_commit(self, repo: Repo, commit_hash: str) -> Dict[str, any]:
        """
        Rollback a specific commit.

        Args:
            repo: Git repository object
            commit_hash: Hash of commit to rollback

        Returns:
            Dictionary with result
        """
        result = {
            'success': False,
            'error': None
        }

        try:
            repo.git.revert(commit_hash, no_edit=True)
            result['success'] = True
        except GitCommandError as e:
            result['error'] = str(e)

        return result


if __name__ == "__main__":
    # Example usage
    manager = CommitManager()

    # Check if current directory is a git repo
    current_dir = "."
    if manager.is_git_repo(current_dir):
        repo = manager.init_repo(current_dir)

        # Get status
        status = manager.get_file_status(repo)
        print(f"Modified files: {status['modified']}")
        print(f"Untracked files: {status['untracked']}")

        # Get recent commits
        commits = manager.get_recent_commits(repo, max_count=5)
        print(f"\nRecent commits:")
        for commit in commits:
            print(f"  {commit['short_hash']}: {commit['message'].split()[0]}")
    else:
        print("Not a git repository")
