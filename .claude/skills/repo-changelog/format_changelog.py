"""
Changelog formatting and output generation module.
Converts categorized commits into user-friendly formats.
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class ChangelogFormatter:
    """Format categorized commits into various output formats."""

    def __init__(self, grouped_commits: List[Dict[str, Any]],
                 summary: Dict[str, Any],
                 statistics: Dict[str, Any]):
        """
        Initialize formatter with data.

        Args:
            grouped_commits: Commits grouped by type
            summary: Category summary statistics
            statistics: Overall repository statistics
        """
        self.grouped_commits = grouped_commits
        self.summary = summary
        self.statistics = statistics

    def format_markdown(self, include_emoji: bool = True,
                       include_links: bool = True,
                       include_stats: bool = True) -> str:
        """
        Format changelog as Markdown.

        Args:
            include_emoji: Include emoji icons for commit types
            include_links: Include links to commits
            include_stats: Include summary statistics

        Returns:
            Formatted Markdown string
        """
        lines = []

        # Header
        lines.append("# Changelog\n")

        # Statistics section
        if include_stats:
            lines.append("## Summary\n")
            lines.append(f"**Total Commits**: {self.summary['total_commits']}")

            if self.statistics.get('date_range'):
                date_range = self.statistics['date_range']
                if date_range['oldest'] and date_range['newest']:
                    lines.append(f"**Date Range**: {date_range['newest']} to {date_range['oldest']}")

            lines.append(f"**Contributors**: {self.statistics['contributor_count']}")

            if self.summary.get('breaking_changes'):
                lines.append(f"**⚠️ Breaking Changes**: {len(self.summary['breaking_changes'])}")

            lines.append(f"**Conventional Commits**: {self.summary['conventional_percentage']:.1f}%\n")

            # Changes by type
            lines.append("### Changes by Type\n")
            for commit_type, info in self.summary['by_type'].items():
                emoji = info['emoji'] if include_emoji else ""
                lines.append(f"- {emoji} **{info['label']}**: {info['count']}")

            lines.append("")

        # Breaking changes section
        if self.summary.get('breaking_changes'):
            lines.append("## ⚠️ Breaking Changes\n")
            for commit in self.summary['breaking_changes']:
                lines.append(self._format_commit_markdown(commit, include_links, include_emoji))
            lines.append("")

        # Commits by type
        lines.append("## Changes\n")

        for group in self.grouped_commits:
            if group['count'] == 0:
                continue

            emoji = group['emoji'] if include_emoji else ""
            lines.append(f"### {emoji} {group['label']} ({group['count']})\n")

            if group['description']:
                lines.append(f"*{group['description']}*\n")

            for commit in group['commits']:
                lines.append(self._format_commit_markdown(commit, include_links, include_emoji))

            lines.append("")

        # Contributors section
        if self.statistics.get('contributors'):
            lines.append("## Contributors\n")
            for contributor in sorted(self.statistics['contributors']):
                lines.append(f"- {contributor}")
            lines.append("")

        return "\n".join(lines)

    def _format_commit_markdown(self, commit: Dict[str, Any],
                                include_links: bool = True,
                                include_emoji: bool = True) -> str:
        """Format a single commit as Markdown."""
        parts = []

        # Commit hash (linked if URL available)
        if include_links and commit.get('url'):
            parts.append(f"[`{commit['short_hash']}`]({commit['url']})")
        else:
            parts.append(f"`{commit['short_hash']}`")

        # Scope (if available)
        if commit.get('scope'):
            parts.append(f"**{commit['scope']}**:")

        # Description
        description = commit.get('description', commit.get('message', ''))
        parts.append(description)

        # Breaking change indicator
        if commit.get('is_breaking') and include_emoji:
            parts.append("⚠️")

        # Author and date
        author = commit.get('author', 'Unknown')
        date = commit.get('date', '')
        if date:
            # Parse and format date
            try:
                date_obj = datetime.fromisoformat(date.replace(' ', 'T'))
                date_str = date_obj.strftime('%Y-%m-%d')
            except:
                date_str = date.split()[0] if date else ''

            parts.append(f"(*{author}*, {date_str})")
        else:
            parts.append(f"(*{author}*)")

        return f"- {' '.join(parts)}"

    def format_json(self) -> str:
        """
        Format changelog as JSON.

        Returns:
            JSON string
        """
        output = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'repository': self.statistics.get('repository_path', 'Unknown'),
                'remote_url': self.statistics.get('remote_url')
            },
            'summary': self.summary,
            'statistics': self.statistics,
            'changes': []
        }

        for group in self.grouped_commits:
            if group['count'] == 0:
                continue

            change_group = {
                'type': group['type'],
                'label': group['label'],
                'emoji': group['emoji'],
                'count': group['count'],
                'commits': []
            }

            for commit in group['commits']:
                change_group['commits'].append({
                    'hash': commit['hash'],
                    'short_hash': commit['short_hash'],
                    'author': commit['author'],
                    'email': commit['email'],
                    'date': commit['date'],
                    'message': commit['description'],
                    'scope': commit.get('scope'),
                    'is_breaking': commit.get('is_breaking', False),
                    'files_changed': commit.get('files_changed', 0),
                    'url': commit.get('url')
                })

            output['changes'].append(change_group)

        return json.dumps(output, indent=2)

    def format_plain_text(self) -> str:
        """
        Format changelog as plain text.

        Returns:
            Plain text string
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("CHANGELOG")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append(f"Total Commits: {self.summary['total_commits']}")
        lines.append(f"Contributors: {self.statistics['contributor_count']}")

        if self.summary.get('breaking_changes'):
            lines.append(f"Breaking Changes: {len(self.summary['breaking_changes'])}")

        lines.append("")

        # Breaking changes
        if self.summary.get('breaking_changes'):
            lines.append("BREAKING CHANGES")
            lines.append("-" * 60)
            for commit in self.summary['breaking_changes']:
                lines.append(self._format_commit_plain(commit))
            lines.append("")

        # Changes by type
        for group in self.grouped_commits:
            if group['count'] == 0:
                continue

            lines.append(f"{group['label'].upper()} ({group['count']})")
            lines.append("-" * 60)

            for commit in group['commits']:
                lines.append(self._format_commit_plain(commit))

            lines.append("")

        # Contributors
        lines.append("CONTRIBUTORS")
        lines.append("-" * 60)
        for contributor in sorted(self.statistics.get('contributors', [])):
            lines.append(contributor)
        lines.append("")

        return "\n".join(lines)

    def _format_commit_plain(self, commit: Dict[str, Any]) -> str:
        """Format a single commit as plain text."""
        description = commit.get('description', commit.get('message', ''))
        author = commit.get('author', 'Unknown')
        short_hash = commit['short_hash']

        scope = f"[{commit['scope']}] " if commit.get('scope') else ""
        breaking = " [BREAKING]" if commit.get('is_breaking') else ""

        return f"  {short_hash} - {scope}{description}{breaking} ({author})"
