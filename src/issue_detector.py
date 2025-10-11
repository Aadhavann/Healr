"""
Issue detection module using pylint and radon for static code analysis.
"""

import os
import json
import subprocess
import tempfile
from typing import List, Dict, Optional
from io import StringIO
from pylint import epylint as lint
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit


class IssueDetector:
    """Detects code quality issues using static analysis tools."""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        Initialize the issue detector.

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.max_complexity = config['code_quality']['max_complexity']
        self.min_maintainability = config['code_quality']['min_maintainability_index']
        self.pylint_threshold = config['code_quality']['pylint_threshold']
        self.check_unused_imports = config['code_quality']['enable_unused_imports']
        self.check_docstrings = config['code_quality']['enable_missing_docstrings']
        self.check_naming = config['code_quality']['enable_naming_conventions']

    def analyze_file(self, file_path: str) -> Dict[str, any]:
        """
        Analyze a file for code quality issues.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary containing all detected issues
        """
        issues = {
            'file_path': file_path,
            'pylint_issues': [],
            'complexity_issues': [],
            'maintainability_issues': [],
            'metrics': {}
        }

        # Only analyze Python files for now
        if not file_path.endswith('.py'):
            return issues

        try:
            # Run pylint analysis
            issues['pylint_issues'] = self._run_pylint(file_path)

            # Run complexity analysis
            issues['complexity_issues'] = self._analyze_complexity(file_path)

            # Run maintainability analysis
            issues['maintainability_issues'] = self._analyze_maintainability(file_path)

            # Calculate overall metrics
            issues['metrics'] = self._calculate_metrics(file_path)

        except Exception as e:
            issues['error'] = str(e)

        return issues

    def _run_pylint(self, file_path: str) -> List[Dict[str, str]]:
        """
        Run pylint on a file and extract issues.

        Args:
            file_path: Path to the file

        Returns:
            List of pylint issues
        """
        issues = []

        try:
            # Configure pylint options
            pylint_opts = [
                file_path,
                '--output-format=json',
                '--disable=all',
            ]

            # Enable specific checks based on configuration
            enabled_checks = []
            if self.check_unused_imports:
                enabled_checks.extend(['unused-import', 'unused-variable'])
            if self.check_docstrings:
                enabled_checks.extend(['missing-docstring', 'missing-function-docstring'])
            if self.check_naming:
                enabled_checks.extend(['invalid-name', 'bad-classmethod-argument'])

            # Add common important checks
            enabled_checks.extend([
                'syntax-error',
                'undefined-variable',
                'duplicate-key',
                'unreachable',
                'dangerous-default-value',
                'redefined-outer-name'
            ])

            if enabled_checks:
                pylint_opts.append(f"--enable={','.join(enabled_checks)}")

            # Run pylint
            output = StringIO()
            reporter = TextReporter(output)

            # Use subprocess to get JSON output
            result = subprocess.run(
                ['pylint'] + pylint_opts,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Parse JSON output
            if result.stdout:
                try:
                    pylint_results = json.loads(result.stdout)
                    for item in pylint_results:
                        issues.append({
                            'type': 'pylint',
                            'message': item.get('message', ''),
                            'line': item.get('line', 0),
                            'column': item.get('column', 0),
                            'severity': item.get('type', 'warning'),
                            'symbol': item.get('symbol', ''),
                            'message_id': item.get('message-id', '')
                        })
                except json.JSONDecodeError:
                    pass

        except subprocess.TimeoutExpired:
            issues.append({
                'type': 'pylint',
                'message': 'Pylint analysis timed out',
                'severity': 'error'
            })
        except Exception as e:
            issues.append({
                'type': 'pylint',
                'message': f'Pylint error: {str(e)}',
                'severity': 'error'
            })

        return issues

    def _analyze_complexity(self, file_path: str) -> List[Dict[str, any]]:
        """
        Analyze cyclomatic complexity using radon.

        Args:
            file_path: Path to the file

        Returns:
            List of complexity issues
        """
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Calculate complexity for all functions/methods
            complexity_results = cc_visit(code)

            for result in complexity_results:
                if result.complexity > self.max_complexity:
                    issues.append({
                        'type': 'complexity',
                        'function': result.name,
                        'line': result.lineno,
                        'complexity': result.complexity,
                        'max_allowed': self.max_complexity,
                        'message': f"Function '{result.name}' has complexity {result.complexity} (max allowed: {self.max_complexity})",
                        'severity': 'warning' if result.complexity <= self.max_complexity + 5 else 'error'
                    })

        except Exception as e:
            issues.append({
                'type': 'complexity',
                'message': f'Complexity analysis error: {str(e)}',
                'severity': 'error'
            })

        return issues

    def _analyze_maintainability(self, file_path: str) -> List[Dict[str, any]]:
        """
        Analyze maintainability index using radon.

        Args:
            file_path: Path to the file

        Returns:
            List of maintainability issues
        """
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # Calculate maintainability index
            mi_results = mi_visit(code, multi=True)

            for result in mi_results:
                if result.mi < self.min_maintainability:
                    issues.append({
                        'type': 'maintainability',
                        'location': result.name,
                        'line': result.lineno,
                        'mi_score': result.mi,
                        'min_required': self.min_maintainability,
                        'message': f"Low maintainability index: {result.mi:.2f} (minimum: {self.min_maintainability})",
                        'severity': 'warning'
                    })

        except Exception as e:
            issues.append({
                'type': 'maintainability',
                'message': f'Maintainability analysis error: {str(e)}',
                'severity': 'error'
            })

        return issues

    def _calculate_metrics(self, file_path: str) -> Dict[str, any]:
        """
        Calculate overall code metrics.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of metrics
        """
        metrics = {
            'lines_of_code': 0,
            'avg_complexity': 0,
            'avg_maintainability': 0,
            'halstead_metrics': {}
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                lines = code.split('\n')

            # Count lines of code (non-empty, non-comment)
            loc = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
            metrics['lines_of_code'] = loc

            # Average complexity
            complexity_results = cc_visit(code)
            if complexity_results:
                avg_complexity = sum(r.complexity for r in complexity_results) / len(complexity_results)
                metrics['avg_complexity'] = round(avg_complexity, 2)

            # Average maintainability
            mi_results = mi_visit(code, multi=True)
            if mi_results:
                avg_mi = sum(r.mi for r in mi_results) / len(mi_results)
                metrics['avg_maintainability'] = round(avg_mi, 2)

            # Halstead metrics
            try:
                h_results = h_visit(code)
                if h_results:
                    metrics['halstead_metrics'] = {
                        'volume': round(h_results[0].volume, 2) if len(h_results) > 0 else 0,
                        'difficulty': round(h_results[0].difficulty, 2) if len(h_results) > 0 else 0,
                        'effort': round(h_results[0].effort, 2) if len(h_results) > 0 else 0
                    }
            except:
                pass

        except Exception as e:
            metrics['error'] = str(e)

        return metrics

    def summarize_issues(self, issues: Dict[str, any]) -> str:
        """
        Create a human-readable summary of issues.

        Args:
            issues: Issues dictionary from analyze_file

        Returns:
            Formatted summary string
        """
        summary_parts = []

        # File header
        summary_parts.append(f"File: {issues['file_path']}")
        summary_parts.append("=" * 60)

        # Metrics
        if issues.get('metrics'):
            summary_parts.append("\nMetrics:")
            summary_parts.append(f"  Lines of Code: {issues['metrics'].get('lines_of_code', 0)}")
            summary_parts.append(f"  Avg Complexity: {issues['metrics'].get('avg_complexity', 0)}")
            summary_parts.append(f"  Avg Maintainability: {issues['metrics'].get('avg_maintainability', 0)}")

        # Pylint issues
        if issues.get('pylint_issues'):
            summary_parts.append(f"\nPylint Issues ({len(issues['pylint_issues'])}):")
            for issue in issues['pylint_issues'][:10]:  # Limit to 10
                summary_parts.append(
                    f"  Line {issue.get('line', '?')}: [{issue.get('severity', '?')}] {issue.get('message', '')}"
                )

        # Complexity issues
        if issues.get('complexity_issues'):
            summary_parts.append(f"\nComplexity Issues ({len(issues['complexity_issues'])}):")
            for issue in issues['complexity_issues']:
                summary_parts.append(
                    f"  Line {issue.get('line', '?')}: {issue.get('message', '')}"
                )

        # Maintainability issues
        if issues.get('maintainability_issues'):
            summary_parts.append(f"\nMaintainability Issues ({len(issues['maintainability_issues'])}):")
            for issue in issues['maintainability_issues']:
                summary_parts.append(
                    f"  Line {issue.get('line', '?')}: {issue.get('message', '')}"
                )

        return '\n'.join(summary_parts)

    def get_issue_priority(self, issues: Dict[str, any]) -> List[Dict[str, any]]:
        """
        Sort and prioritize issues for fixing.

        Args:
            issues: Issues dictionary from analyze_file

        Returns:
            Sorted list of issues by priority
        """
        all_issues = []

        # Collect all issues with priority scores
        for pylint_issue in issues.get('pylint_issues', []):
            priority = 3 if pylint_issue.get('severity') == 'error' else 2
            all_issues.append({
                **pylint_issue,
                'priority': priority
            })

        for complexity_issue in issues.get('complexity_issues', []):
            all_issues.append({
                **complexity_issue,
                'priority': 2
            })

        for maintainability_issue in issues.get('maintainability_issues', []):
            all_issues.append({
                **maintainability_issue,
                'priority': 1
            })

        # Sort by priority (higher first), then by line number
        all_issues.sort(key=lambda x: (-x['priority'], x.get('line', 0)))

        return all_issues


if __name__ == "__main__":
    # Example usage
    detector = IssueDetector()

    # Analyze a sample file
    sample_file = "src/repo_parser.py"
    if os.path.exists(sample_file):
        issues = detector.analyze_file(sample_file)
        print(detector.summarize_issues(issues))

        # Get prioritized issues
        prioritized = detector.get_issue_priority(issues)
        print(f"\nFound {len(prioritized)} total issues")
