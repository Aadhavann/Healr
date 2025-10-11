"""
Main orchestration module for the self-healing code system.
"""

import os
import sys
import argparse
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from repo_parser import RepoParser
from embedding_index import EmbeddingIndex
from issue_detector import IssueDetector
from llm_agent import LLMAgent
from code_editor import CodeEditor
from commit_manager import CommitManager
from explanation_logger import ExplanationLogger
from test_generator import TestGenerator


console = Console()


class SelfHealingOrchestrator:
    """Main orchestrator for the self-healing system."""

    def __init__(self, config_path: str = "config/settings.json"):
        """
        Initialize the orchestrator.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path

        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Initialize components
        self.repo_parser = RepoParser(config_path)
        self.embedding_index = EmbeddingIndex(config_path)
        self.issue_detector = IssueDetector(config_path)
        self.llm_agent = LLMAgent(config_path)
        self.code_editor = CodeEditor()
        self.commit_manager = CommitManager(config_path)
        self.logger = ExplanationLogger(config_path)
        self.test_generator = TestGenerator()

    def analyze_repository(self, repo_path: str) -> dict:
        """
        Analyze a repository for code quality issues.

        Args:
            repo_path: Path to the repository

        Returns:
            Dictionary with analysis results
        """
        console.print(f"\n[bold blue]Analyzing repository:[/bold blue] {repo_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Parse repository
            task = progress.add_task("Parsing repository...", total=None)
            files = self.repo_parser.parse_repository(repo_path)
            progress.update(task, completed=True)

            # Build embedding index
            task = progress.add_task("Building embedding index...", total=None)
            self.embedding_index.add_files(files)
            progress.update(task, completed=True)

            # Analyze each file
            task = progress.add_task("Detecting issues...", total=len(files))
            all_issues = []

            for file_data in files:
                issues = self.issue_detector.analyze_file(file_data['path'])

                # Log issue detection
                self.logger.log_issue_detection(file_data['path'], issues)

                # Get prioritized issues
                prioritized = self.issue_detector.get_issue_priority(issues)

                if prioritized:
                    all_issues.append({
                        'file': file_data['path'],
                        'issues': prioritized,
                        'metrics': issues.get('metrics', {})
                    })

                progress.advance(task)

        # Display results
        self._display_analysis_results(files, all_issues)

        return {
            'files_analyzed': len(files),
            'files_with_issues': len(all_issues),
            'total_issues': sum(len(f['issues']) for f in all_issues),
            'issues': all_issues
        }

    def fix_repository(self, repo_path: str, task_type: str = "all", dry_run: bool = False) -> dict:
        """
        Fix issues in a repository.

        Args:
            repo_path: Path to the repository
            task_type: Type of fixes to apply
            dry_run: If True, don't actually apply fixes

        Returns:
            Dictionary with fix results
        """
        console.print(f"\n[bold green]Fixing repository:[/bold green] {repo_path}")
        console.print(f"Task type: {task_type}")
        console.print(f"Dry run: {dry_run}\n")

        # First analyze
        analysis = self.analyze_repository(repo_path)

        if analysis['total_issues'] == 0:
            console.print("[green]No issues found! Repository is clean.[/green]")
            return {'fixes_applied': 0, 'success': True}

        # Initialize git repo if it exists
        repo = None
        if self.commit_manager.is_git_repo(repo_path):
            repo = self.commit_manager.init_repo(repo_path)

        fixes_applied = []
        fixes_failed = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Applying fixes...", total=analysis['total_issues'])

            for file_issues in analysis['issues']:
                file_path = file_issues['file']

                for issue in file_issues['issues'][:5]:  # Limit issues per file
                    try:
                        # Read file content
                        with open(file_path, 'r') as f:
                            code = f.read()

                        # Get context from embedding index
                        context = self.embedding_index.get_file_context(
                            file_path,
                            issue.get('line', 1)
                        )

                        # Generate fix using LLM
                        issue_desc = issue.get('message', str(issue))
                        llm_response = self.llm_agent.improve_code(
                            file_path,
                            context or code[:2000],  # Limit context size
                            issue_desc
                        )

                        # Log LLM interaction
                        self.logger.log_llm_interaction(
                            file_path,
                            'improve_code',
                            issue_desc,
                            llm_response
                        )

                        if not dry_run and llm_response.get('code'):
                            # Apply the fix
                            edit_result = self.code_editor.apply_edit(
                                file_path,
                                llm_response['code'],
                                validate=True,
                                create_backup=True
                            )

                            # Log edit
                            self.logger.log_code_edit(file_path, edit_result)

                            if edit_result['success']:
                                fixes_applied.append({
                                    'file': file_path,
                                    'issue': issue_desc,
                                    'backup': edit_result.get('backup_path')
                                })

                                # Log fix summary
                                self.logger.log_fix_summary(
                                    file_path,
                                    issue_desc,
                                    llm_response.get('explanation', ''),
                                    True
                                )
                            else:
                                fixes_failed.append({
                                    'file': file_path,
                                    'issue': issue_desc,
                                    'error': edit_result.get('error')
                                })
                        else:
                            # Dry run - just log
                            console.print(f"[yellow]Would fix:[/yellow] {file_path} - {issue_desc}")

                    except Exception as e:
                        fixes_failed.append({
                            'file': file_path,
                            'issue': issue.get('message', 'Unknown'),
                            'error': str(e)
                        })

                    progress.advance(task)

        # Commit changes if git repo
        if repo and fixes_applied and not dry_run:
            console.print("\n[bold]Committing changes...[/bold]")
            commit_fixes = [
                {
                    'file_path': fix['file'],
                    'action': 'Fix code quality issue',
                    'description': fix['issue']
                }
                for fix in fixes_applied
            ]
            commit_results = self.commit_manager.commit_batch_fixes(repo, commit_fixes)

            for result in commit_results:
                if result.get('success'):
                    console.print(f"[green]Committed:[/green] {result.get('commit_hash', '')[:7]}")
                    self.logger.log_commit(result, [f['file'] for f in commit_fixes])

        # Display summary
        self._display_fix_summary(fixes_applied, fixes_failed, dry_run)

        return {
            'fixes_applied': len(fixes_applied),
            'fixes_failed': len(fixes_failed),
            'success': len(fixes_failed) == 0
        }

    def generate_tests(self, repo_path: str, file_path: Optional[str] = None) -> dict:
        """
        Generate tests for repository or specific file.

        Args:
            repo_path: Path to the repository
            file_path: Optional specific file path

        Returns:
            Dictionary with results
        """
        console.print(f"\n[bold cyan]Generating tests[/bold cyan]")

        if file_path:
            # Generate tests for specific file
            result = self.test_generator.generate_and_save_tests(file_path)

            if result['success']:
                console.print(f"[green]Tests generated:[/green] {result['test_file_path']}")
            else:
                console.print(f"[red]Failed:[/red] {result['error']}")

            return result
        else:
            # Generate tests for all files
            files = self.repo_parser.parse_repository(repo_path)
            python_files = [f for f in files if f['extension'] == '.py']

            results = []
            for file_data in python_files:
                result = self.test_generator.generate_and_save_tests(file_data['path'])
                results.append(result)

                if result['success']:
                    console.print(f"[green]Generated:[/green] {result['test_file_path']}")

            return {
                'total_files': len(python_files),
                'success_count': sum(1 for r in results if r['success']),
                'results': results
            }

    def generate_report(self, repo_path: str, output_path: Optional[str] = None) -> str:
        """
        Generate a comprehensive report.

        Args:
            repo_path: Path to the repository
            output_path: Optional path to save report

        Returns:
            Report text
        """
        console.print("\n[bold magenta]Generating report...[/bold magenta]")

        # Get statistics
        stats = self.logger.get_statistics()

        # Generate report
        report = self.logger.generate_report(output_path)

        console.print(report)

        if output_path:
            console.print(f"\n[green]Report saved to:[/green] {output_path}")

        return report

    def _display_analysis_results(self, files, issues):
        """Display analysis results in a table."""
        console.print(f"\n[bold]Analysis Results[/bold]")
        console.print(f"Files analyzed: {len(files)}")
        console.print(f"Files with issues: {len(issues)}")
        console.print(f"Total issues: {sum(len(f['issues']) for f in issues)}\n")

        if issues:
            table = Table(title="Issues Found")
            table.add_column("File", style="cyan")
            table.add_column("Issues", style="yellow")
            table.add_column("Complexity", style="magenta")
            table.add_column("Maintainability", style="green")

            for file_issue in issues[:10]:  # Show top 10
                metrics = file_issue.get('metrics', {})
                table.add_row(
                    os.path.basename(file_issue['file']),
                    str(len(file_issue['issues'])),
                    str(metrics.get('avg_complexity', 'N/A')),
                    str(metrics.get('avg_maintainability', 'N/A'))
                )

            console.print(table)

    def _display_fix_summary(self, fixes_applied, fixes_failed, dry_run):
        """Display fix summary."""
        console.print(f"\n[bold]Fix Summary[/bold]")

        if dry_run:
            console.print("[yellow]DRY RUN - No changes were made[/yellow]")

        console.print(f"Fixes applied: {len(fixes_applied)}")
        console.print(f"Fixes failed: {len(fixes_failed)}\n")

        if fixes_failed:
            console.print("[red]Failed fixes:[/red]")
            for fix in fixes_failed[:5]:
                console.print(f"  - {fix['file']}: {fix['error']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Healr - AI-Powered Code Self-Healing System"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze repository for issues')
    analyze_parser.add_argument('--repo', required=True, help='Path to repository')
    analyze_parser.add_argument('--output', help='Output file for results')

    # Fix command
    fix_parser = subparsers.add_parser('fix', help='Fix issues in repository')
    fix_parser.add_argument('--repo', required=True, help='Path to repository')
    fix_parser.add_argument('--task', default='all', help='Task type')
    fix_parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')

    # Test command
    test_parser = subparsers.add_parser('test', help='Generate tests')
    test_parser.add_argument('--repo', required=True, help='Path to repository')
    test_parser.add_argument('--file', help='Specific file to generate tests for')

    # Report command
    report_parser = subparsers.add_parser('report', help='Generate report')
    report_parser.add_argument('--repo', required=True, help='Path to repository')
    report_parser.add_argument('--output', help='Output file for report')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize orchestrator
    orchestrator = SelfHealingOrchestrator()

    # Execute command
    if args.command == 'analyze':
        results = orchestrator.analyze_repository(args.repo)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)

    elif args.command == 'fix':
        orchestrator.fix_repository(args.repo, args.task, args.dry_run)

    elif args.command == 'test':
        orchestrator.generate_tests(args.repo, args.file)

    elif args.command == 'report':
        orchestrator.generate_report(args.repo, args.output)


if __name__ == "__main__":
    main()
