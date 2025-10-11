"""
Explanation logger module for recording all operations and LLM responses.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class ExplanationLogger:
    """Logs all self-healing operations and LLM interactions."""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        Initialize the explanation logger.

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        log_config = config['logging']
        self.log_file = log_config['log_file']
        self.max_log_entries = log_config['max_log_entries']

        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        # Initialize log file if it doesn't exist
        if not os.path.exists(self.log_file):
            self._save_logs([])

    def _load_logs(self) -> List[Dict[str, Any]]:
        """
        Load existing logs from file.

        Returns:
            List of log entries
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_logs(self, logs: List[Dict[str, Any]]) -> None:
        """
        Save logs to file.

        Args:
            logs: List of log entries
        """
        # Limit number of logs
        if len(logs) > self.max_log_entries:
            logs = logs[-self.max_log_entries:]

        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    def log_operation(self, operation_type: str, file_path: str,
                     details: Dict[str, Any]) -> str:
        """
        Log a self-healing operation.

        Args:
            operation_type: Type of operation (e.g., "fix_bug", "refactor", "add_docstrings")
            file_path: Path to the affected file
            details: Operation details

        Returns:
            Log entry ID
        """
        logs = self._load_logs()

        log_entry = {
            'id': self._generate_log_id(),
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'file_path': file_path,
            'details': details
        }

        logs.append(log_entry)
        self._save_logs(logs)

        return log_entry['id']

    def log_issue_detection(self, file_path: str, issues: Dict[str, Any]) -> str:
        """
        Log detected issues in a file.

        Args:
            file_path: Path to the file
            issues: Issues dictionary from IssueDetector

        Returns:
            Log entry ID
        """
        details = {
            'total_issues': sum([
                len(issues.get('pylint_issues', [])),
                len(issues.get('complexity_issues', [])),
                len(issues.get('maintainability_issues', []))
            ]),
            'pylint_count': len(issues.get('pylint_issues', [])),
            'complexity_count': len(issues.get('complexity_issues', [])),
            'maintainability_count': len(issues.get('maintainability_issues', [])),
            'metrics': issues.get('metrics', {})
        }

        return self.log_operation('issue_detection', file_path, details)

    def log_llm_interaction(self, file_path: str, task_type: str,
                           prompt: str, response: Dict[str, str]) -> str:
        """
        Log an LLM interaction.

        Args:
            file_path: Path to the file
            task_type: Type of task (e.g., "improve_code", "fix_bug")
            prompt: Prompt sent to LLM
            response: LLM response

        Returns:
            Log entry ID
        """
        details = {
            'task_type': task_type,
            'prompt_length': len(prompt),
            'response': response,
            'has_code': bool(response.get('code')),
            'has_explanation': bool(response.get('explanation'))
        }

        return self.log_operation('llm_interaction', file_path, details)

    def log_code_edit(self, file_path: str, edit_result: Dict[str, Any],
                     backup_path: Optional[str] = None) -> str:
        """
        Log a code edit operation.

        Args:
            file_path: Path to the edited file
            edit_result: Result from CodeEditor
            backup_path: Path to backup file

        Returns:
            Log entry ID
        """
        details = {
            'success': edit_result.get('success', False),
            'backup_path': backup_path or edit_result.get('backup_path'),
            'validation': edit_result.get('validation'),
            'error': edit_result.get('error')
        }

        return self.log_operation('code_edit', file_path, details)

    def log_commit(self, commit_result: Dict[str, Any], files: List[str]) -> str:
        """
        Log a git commit.

        Args:
            commit_result: Result from CommitManager
            files: List of files in the commit

        Returns:
            Log entry ID
        """
        details = {
            'success': commit_result.get('success', False),
            'commit_hash': commit_result.get('commit_hash'),
            'commit_message': commit_result.get('commit_message'),
            'files': files,
            'file_count': len(files),
            'error': commit_result.get('error')
        }

        return self.log_operation('git_commit', '', details)

    def log_fix_summary(self, file_path: str, issue_description: str,
                       fix_summary: str, success: bool) -> str:
        """
        Log a complete fix operation summary.

        Args:
            file_path: Path to the fixed file
            issue_description: Description of the issue
            fix_summary: Summary of the fix
            success: Whether the fix was successful

        Returns:
            Log entry ID
        """
        details = {
            'issue_description': issue_description,
            'fix_summary': fix_summary,
            'success': success
        }

        return self.log_operation('fix_summary', file_path, details)

    def get_logs(self, operation_type: Optional[str] = None,
                file_path: Optional[str] = None,
                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve logs with optional filtering.

        Args:
            operation_type: Filter by operation type
            file_path: Filter by file path
            limit: Maximum number of logs to return

        Returns:
            List of matching log entries
        """
        logs = self._load_logs()

        # Apply filters
        if operation_type:
            logs = [log for log in logs if log.get('operation_type') == operation_type]

        if file_path:
            logs = [log for log in logs if log.get('file_path') == file_path]

        # Apply limit
        if limit:
            logs = logs[-limit:]

        return logs

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about logged operations.

        Returns:
            Dictionary with statistics
        """
        logs = self._load_logs()

        stats = {
            'total_operations': len(logs),
            'operations_by_type': {},
            'files_modified': set(),
            'successful_operations': 0,
            'failed_operations': 0,
            'recent_operations': []
        }

        for log in logs:
            # Count by type
            op_type = log.get('operation_type', 'unknown')
            if op_type not in stats['operations_by_type']:
                stats['operations_by_type'][op_type] = 0
            stats['operations_by_type'][op_type] += 1

            # Track modified files
            if log.get('file_path'):
                stats['files_modified'].add(log.get('file_path'))

            # Count success/failure
            details = log.get('details', {})
            if details.get('success') is True:
                stats['successful_operations'] += 1
            elif details.get('success') is False:
                stats['failed_operations'] += 1

        # Convert set to list for JSON serialization
        stats['files_modified'] = list(stats['files_modified'])
        stats['files_modified_count'] = len(stats['files_modified'])

        # Get recent operations
        stats['recent_operations'] = logs[-10:] if logs else []

        return stats

    def search_logs(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search logs for a specific term.

        Args:
            search_term: Term to search for

        Returns:
            List of matching log entries
        """
        logs = self._load_logs()
        matching_logs = []

        search_term_lower = search_term.lower()

        for log in logs:
            # Convert log to string for searching
            log_str = json.dumps(log).lower()

            if search_term_lower in log_str:
                matching_logs.append(log)

        return matching_logs

    def export_logs(self, output_path: str, operation_type: Optional[str] = None) -> bool:
        """
        Export logs to a separate file.

        Args:
            output_path: Path to export file
            operation_type: Optional filter by operation type

        Returns:
            True if export was successful
        """
        try:
            logs = self.get_logs(operation_type=operation_type)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def clear_logs(self) -> None:
        """Clear all logs."""
        self._save_logs([])

    def _generate_log_id(self) -> str:
        """
        Generate a unique log entry ID.

        Returns:
            Log ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"log_{timestamp}"

    def get_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific log entry by ID.

        Args:
            log_id: Log entry ID

        Returns:
            Log entry or None if not found
        """
        logs = self._load_logs()

        for log in logs:
            if log.get('id') == log_id:
                return log

        return None

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a human-readable report of operations.

        Args:
            output_path: Optional path to save report

        Returns:
            Report text
        """
        stats = self.get_statistics()
        logs = self._load_logs()

        report_lines = [
            "=" * 80,
            "HEALR - Self-Healing Operations Report",
            "=" * 80,
            "",
            f"Total Operations: {stats['total_operations']}",
            f"Successful: {stats['successful_operations']}",
            f"Failed: {stats['failed_operations']}",
            f"Files Modified: {stats['files_modified_count']}",
            "",
            "Operations by Type:",
        ]

        for op_type, count in stats['operations_by_type'].items():
            report_lines.append(f"  - {op_type}: {count}")

        report_lines.extend([
            "",
            "Recent Operations:",
            ""
        ])

        for log in stats['recent_operations'][-10:]:
            timestamp = log.get('timestamp', '')
            op_type = log.get('operation_type', 'unknown')
            file_path = log.get('file_path', 'N/A')
            report_lines.append(f"  [{timestamp}] {op_type}: {file_path}")

        report_text = '\n'.join(report_lines)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)

        return report_text


if __name__ == "__main__":
    # Example usage
    logger = ExplanationLogger()

    # Log an issue detection
    issues = {
        'pylint_issues': [{'message': 'unused import'}],
        'complexity_issues': [],
        'maintainability_issues': []
    }
    logger.log_issue_detection("example.py", issues)

    # Get statistics
    stats = logger.get_statistics()
    print(f"Total operations: {stats['total_operations']}")

    # Generate report
    report = logger.generate_report()
    print(report)
