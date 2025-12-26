#!/usr/bin/env python3
"""
Generate Changelog - Main Entry Point

A command-line tool that generates end-user friendly release notes
from git repository history.

Usage:
    python generate_changelog.py --help
    python generate_changelog.py --last 20
    python generate_changelog.py --since v1.0.0
    python generate_changelog.py --from v1.0.0 --to v1.1.0
    python generate_changelog.py --version v1.2.0 --output release_notes.md

Outputs clean, non-technical release notes suitable for:
- Slack updates to support teams
- CHANGELOG.md files
- Release documentation
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import get_config, ConfigLoader
from git_analyzer import GitAnalyzer
from diff_parser import DiffParser
from change_consolidator import ChangeConsolidator
from changelog_formatter import ChangelogFormatter
from breaking_change_detector import BreakingChangeDetector
from ai_interpreter import AIInterpreter


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate end-user friendly release notes from git history.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --last 20                    # Last 20 commits
  %(prog)s --since v1.0.0               # Since tag v1.0.0
  %(prog)s --from v1.0.0 --to v1.1.0    # Between two tags
  %(prog)s --since HEAD~50 --preview    # Preview last 50 commits
  %(prog)s --version v1.2.0 --append    # Append to CHANGELOG.md
        """
    )

    # Commit range options (mutually exclusive groups)
    range_group = parser.add_argument_group('Commit Range')
    range_group.add_argument(
        '--last', '-n',
        type=int,
        metavar='N',
        help='Analyze the last N commits'
    )
    range_group.add_argument(
        '--since',
        metavar='REF',
        help='Analyze commits since REF (tag, branch, or commit hash)'
    )
    range_group.add_argument(
        '--from',
        dest='from_ref',
        metavar='REF',
        help='Start of commit range (use with --to)'
    )
    range_group.add_argument(
        '--to',
        dest='to_ref',
        metavar='REF',
        default='HEAD',
        help='End of commit range (default: HEAD)'
    )

    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--version', '-v',
        metavar='VERSION',
        help='Version string for release notes header (e.g., v1.2.0)'
    )
    output_group.add_argument(
        '--output', '-o',
        metavar='FILE',
        help='Output file path (default: auto-generated in RELEASE_NOTES/)'
    )
    output_group.add_argument(
        '--format', '-f',
        choices=['markdown', 'slack', 'simple'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    output_group.add_argument(
        '--append',
        action='store_true',
        help='Append to existing CHANGELOG.md instead of creating new file'
    )
    output_group.add_argument(
        '--changelog',
        metavar='FILE',
        default='CHANGELOG.md',
        help='Path to CHANGELOG.md for --append mode (default: CHANGELOG.md)'
    )
    output_group.add_argument(
        '--stdout',
        action='store_true',
        help='Print to stdout instead of writing to file'
    )

    # Preview and interactive options
    preview_group = parser.add_argument_group('Preview Options')
    preview_group.add_argument(
        '--preview',
        action='store_true',
        help='Preview changes before generating (interactive)'
    )
    preview_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be generated without writing files'
    )

    # Configuration options
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument(
        '--config', '-c',
        metavar='FILE',
        help='Path to custom config.yaml file'
    )
    config_group.add_argument(
        '--repo', '-r',
        metavar='PATH',
        default='.',
        help='Path to git repository (default: current directory)'
    )

    # Filtering options
    filter_group = parser.add_argument_group('Filtering')
    filter_group.add_argument(
        '--include-merge',
        action='store_true',
        help='Include merge commits (excluded by default)'
    )
    filter_group.add_argument(
        '--category',
        action='append',
        choices=['feature', 'enhancement', 'bugfix', 'change', 'breaking', 'security', 'dependency', 'other'],
        help='Only include specific categories (can be repeated)'
    )

    # AI interpretation options
    ai_group = parser.add_argument_group('AI Interpretation')
    ai_group.add_argument(
        '--ai',
        action='store_true',
        help='Enable AI interpretation for ambiguous changes (requires API key)'
    )
    ai_group.add_argument(
        '--anthropic-key',
        metavar='KEY',
        help='Anthropic API key for Claude-based interpretation'
    )
    ai_group.add_argument(
        '--openai-key',
        metavar='KEY',
        help='OpenAI API key for GPT-based interpretation'
    )
    ai_group.add_argument(
        '--no-ai-fallback',
        action='store_true',
        help='Disable pattern-based fallback when AI unavailable'
    )

    # Verbosity
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed processing information'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )

    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> bool:
    """Validate argument combinations."""
    # Check for at least one commit range specification
    if not any([args.last, args.since, args.from_ref]):
        print("Error: Must specify commit range with --last, --since, or --from/--to")
        print("Use --help for usage information")
        return False

    # Check --from requires --to (which has default)
    if args.from_ref and not args.to_ref:
        print("Error: --from requires --to")
        return False

    # Check repo path exists
    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {args.repo}")
        return False

    # Check for .git directory
    git_dir = repo_path / '.git'
    if not git_dir.exists():
        print(f"Error: Not a git repository: {args.repo}")
        return False

    return True


def log(message: str, args: argparse.Namespace, level: str = 'info') -> None:
    """Log a message based on verbosity settings."""
    if args.quiet:
        return
    if level == 'verbose' and not args.verbose:
        return
    print(message)


class ChangelogGenerator:
    """Main changelog generation orchestrator."""

    def __init__(self, config_path: Optional[str] = None, repo_path: str = '.',
                 ai_enabled: bool = False, ai_client: Any = None):
        """
        Initialize the changelog generator.

        Args:
            config_path: Optional path to custom config file
            repo_path: Path to git repository
            ai_enabled: Enable AI interpretation for ambiguous changes
            ai_client: Pre-configured AI client (Anthropic or OpenAI)
        """
        self.config = get_config(config_path)
        self.repo_path = Path(repo_path).resolve()

        # Initialize components
        self.git_analyzer = GitAnalyzer(str(self.repo_path), config_path)
        self.diff_parser = DiffParser(config_path)
        self.consolidator = ChangeConsolidator(config_path)
        self.formatter = ChangelogFormatter(config_path)
        self.breaking_detector = BreakingChangeDetector(config_path)

        # Initialize AI interpreter
        self.ai_interpreter = AIInterpreter(config_path, ai_client=ai_client)
        self.ai_enabled = ai_enabled

    def generate(self, commit_range: Dict[str, Any],
                 version: Optional[str] = None,
                 include_merge: bool = False,
                 categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate changelog from commit range.

        Args:
            commit_range: Dict with 'type' and range-specific keys
            version: Version string for header
            include_merge: Whether to include merge commits
            categories: List of categories to include (None = all)

        Returns:
            Dict with 'changes', 'grouped', 'formatted' keys
        """
        # Step 1: Get commits from git
        commits = self._get_commits(commit_range, include_merge)

        if not commits:
            return {
                'changes': [],
                'grouped': {},
                'formatted': '',
                'stats': {'total_commits': 0, 'total_changes': 0}
            }

        # Step 2: Parse each commit's diff
        all_changes = []
        for commit in commits:
            # Parse diff content
            diff_changes = self.diff_parser.parse_diff(
                commit.get('diff', ''),
                commit.get('files_changed', []),
                commit.get('subject', '')
            )

            # Step 2a: Use AI interpretation for ambiguous changes if enabled
            if self.ai_enabled:
                enhanced_changes = []
                for change in diff_changes:
                    # Try AI interpretation for low confidence or diff_analysis source
                    if change.get('confidence') == 'low' or change.get('source') == 'diff_analysis':
                        ai_result = self.ai_interpreter.interpret_commit({
                            'hash': commit.get('hash', ''),
                            'subject': commit.get('subject', ''),
                            'diff': commit.get('diff', ''),
                            'files_changed': commit.get('files_changed', [])
                        })
                        if ai_result and ai_result.get('confidence') == 'high':
                            # Use AI-enhanced result
                            enhanced_changes.append(ai_result)
                            continue
                    enhanced_changes.append(change)
                diff_changes = enhanced_changes

            all_changes.extend(diff_changes)

            # Detect breaking changes
            breaking = self.breaking_detector.detect(
                commit.get('subject', ''),
                commit.get('body', ''),
                commit.get('diff', '')
            )
            all_changes.extend(breaking)

        # Step 3: Consolidate changes
        consolidated = self.consolidator.consolidate(all_changes)

        # Step 4: Filter by category if specified
        if categories:
            consolidated = [c for c in consolidated if c.get('category') in categories]

        # Step 5: Group by category
        grouped = self.consolidator.group_by_category(consolidated)

        # Step 6: Generate statistics
        stats = {
            'total_commits': len(commits),
            'total_changes': len(consolidated),
            'by_category': {cat: len(changes) for cat, changes in grouped.items()}
        }

        return {
            'changes': consolidated,
            'grouped': grouped,
            'formatted': '',  # Format separately based on output format
            'stats': stats
        }

    def _get_commits(self, commit_range: Dict[str, Any],
                     include_merge: bool) -> List[Dict[str, Any]]:
        """Get commits based on range specification."""
        range_type = commit_range.get('type')

        if range_type == 'last':
            return self.git_analyzer.get_last_commits(
                commit_range['count'],
                include_merge=include_merge
            )
        elif range_type == 'since':
            return self.git_analyzer.get_commits_since(
                commit_range['ref'],
                include_merge=include_merge
            )
        elif range_type == 'range':
            return self.git_analyzer.get_commits_between(
                commit_range['from'],
                commit_range['to'],
                include_merge=include_merge
            )
        else:
            return []

    def format_output(self, result: Dict[str, Any],
                      output_format: str = 'markdown',
                      version: Optional[str] = None,
                      summary: Optional[str] = None) -> str:
        """
        Format the generated changelog.

        Args:
            result: Result from generate()
            output_format: 'markdown', 'slack', or 'simple'
            version: Version string
            summary: Optional summary line

        Returns:
            Formatted string
        """
        grouped = result.get('grouped', {})

        if output_format == 'slack':
            return self.formatter.format_slack_message(grouped, version, summary)
        elif output_format == 'simple':
            return self.formatter.format_simple_list(grouped)
        else:  # markdown
            return self.formatter.format_changelog(grouped, version)

    def save_output(self, content: str,
                    output_path: Optional[str] = None,
                    version: Optional[str] = None,
                    append_mode: bool = False,
                    changelog_path: Optional[str] = None) -> str:
        """
        Save formatted content to file.

        Args:
            content: Formatted content
            output_path: Explicit output path (or auto-generate)
            version: Version for auto-generated filename
            append_mode: Append to existing CHANGELOG
            changelog_path: Path to CHANGELOG for append mode

        Returns:
            Path to saved file
        """
        if append_mode:
            return self.formatter.append_to_changelog(
                content,
                changelog_path=changelog_path
            )
        else:
            return self.formatter.save_to_file(
                content,
                file_path=output_path,
                version=version,
                base_path=str(self.repo_path)
            )


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Validate arguments
    if not validate_args(args):
        return 1

    # Load configuration
    try:
        config_path = args.config
        log(f"Using config: {config_path or 'default'}", args, 'verbose')
    except Exception as e:
        print(f"Error loading config: {e}")
        return 1

    # Configure AI client if requested
    ai_client = None
    ai_enabled = args.ai

    if ai_enabled:
        # Try Anthropic first, then OpenAI
        anthropic_key = args.anthropic_key or os.environ.get('ANTHROPIC_API_KEY')
        openai_key = args.openai_key or os.environ.get('OPENAI_API_KEY')

        if anthropic_key:
            try:
                import anthropic
                ai_client = anthropic.Anthropic(api_key=anthropic_key)
                log("AI interpretation enabled using Claude", args, 'verbose')
            except ImportError:
                log("Warning: anthropic package not installed. Run: pip install anthropic", args)
            except Exception as e:
                log(f"Warning: Could not initialize Anthropic client: {e}", args)

        elif openai_key:
            try:
                import openai
                ai_client = openai.OpenAI(api_key=openai_key)
                log("AI interpretation enabled using GPT", args, 'verbose')
            except ImportError:
                log("Warning: openai package not installed. Run: pip install openai", args)
            except Exception as e:
                log(f"Warning: Could not initialize OpenAI client: {e}", args)

        if ai_enabled and not ai_client:
            if args.no_ai_fallback:
                print("Error: --ai specified but no API key provided and --no-ai-fallback set")
                print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or use --anthropic-key/--openai-key")
                return 1
            else:
                log("AI client unavailable, using pattern-based fallback", args)

    # Initialize generator
    try:
        generator = ChangelogGenerator(
            config_path=config_path,
            repo_path=args.repo,
            ai_enabled=ai_enabled,
            ai_client=ai_client
        )
    except Exception as e:
        print(f"Error initializing generator: {e}")
        return 1

    # Determine commit range
    if args.last:
        commit_range = {'type': 'last', 'count': args.last}
        log(f"Analyzing last {args.last} commits...", args)
    elif args.since:
        commit_range = {'type': 'since', 'ref': args.since}
        log(f"Analyzing commits since {args.since}...", args)
    elif args.from_ref:
        commit_range = {'type': 'range', 'from': args.from_ref, 'to': args.to_ref}
        log(f"Analyzing commits from {args.from_ref} to {args.to_ref}...", args)
    else:
        # Should not reach here due to validation
        print("Error: No commit range specified")
        return 1

    # Generate changelog
    try:
        log("Parsing commits and diffs...", args, 'verbose')
        result = generator.generate(
            commit_range,
            version=args.version,
            include_merge=args.include_merge,
            categories=args.category
        )
    except Exception as e:
        print(f"Error generating changelog: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Check if any changes found
    if not result['changes']:
        log("No user-facing changes found in the specified range.", args)
        return 0

    # Show statistics
    stats = result['stats']
    log(f"Found {stats['total_changes']} changes from {stats['total_commits']} commits", args)
    if args.verbose:
        for cat, count in stats.get('by_category', {}).items():
            log(f"  - {cat}: {count}", args, 'verbose')

    # Preview mode
    if args.preview:
        try:
            from preview_mode import PreviewMode
            previewer = PreviewMode(generator.config)
            if not previewer.preview_and_confirm(result):
                log("Generation cancelled by user.", args)
                return 0
        except ImportError:
            log("Preview mode not available (preview_mode.py not found)", args)
            log("Continuing with generation...", args)

    # Format output
    formatted = generator.format_output(
        result,
        output_format=args.format,
        version=args.version
    )

    # Dry run - just show what would be generated
    if args.dry_run:
        log("\n--- DRY RUN OUTPUT ---\n", args)
        print(formatted)
        log("\n--- END DRY RUN ---", args)
        return 0

    # Output to stdout
    if args.stdout:
        print(formatted)
        return 0

    # Save to file
    try:
        if args.append:
            output_file = generator.save_output(
                formatted,
                append_mode=True,
                changelog_path=args.changelog
            )
            log(f"Appended to: {output_file}", args)
        else:
            output_file = generator.save_output(
                formatted,
                output_path=args.output,
                version=args.version
            )
            log(f"Saved to: {output_file}", args)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except IOError as e:
        print(f"Error writing file: {e}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
