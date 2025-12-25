"""
Changelog formatter module.
Generates Slack-ready markdown output with proper headings,
bullet points, and optional footnotes.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class ChangelogFormatter:
    """
    Formats consolidated changes into clean markdown for Slack and documentation.

    Output format:
    - Category headings (New Features, Enhancements, Bug Fixes, etc.)
    - Brief bullet points
    - Optional footnotes for important notes
    - No technical jargon or secrets
    """

    # Category display configuration
    CATEGORY_CONFIG = {
        'feature': {
            'heading': 'New Features',
            'emoji': '',  # No emoji as per user preference
            'order': 1
        },
        'enhancement': {
            'heading': 'Enhancements',
            'emoji': '',
            'order': 2
        },
        'bugfix': {
            'heading': 'Bug Fixes',
            'emoji': '',
            'order': 3
        },
        'change': {
            'heading': 'Changes',
            'emoji': '',
            'order': 4
        },
        'breaking': {
            'heading': 'Breaking Changes',
            'emoji': '',
            'order': 0  # Breaking changes first
        },
        'other': {
            'heading': 'Other Updates',
            'emoji': '',
            'order': 5
        }
    }

    def __init__(self):
        """Initialize the formatter."""
        self.footnotes: List[str] = []

    def format_changelog(self, grouped_changes: Dict[str, List[Dict[str, Any]]],
                         version: Optional[str] = None,
                         release_date: Optional[str] = None,
                         footnotes: Optional[List[str]] = None) -> str:
        """
        Format changes into a complete changelog markdown.

        Args:
            grouped_changes: Changes grouped by category
            version: Optional version string (e.g., "v1.1.0")
            release_date: Optional release date
            footnotes: Optional list of footnote strings

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        header = self._format_header(version, release_date)
        if header:
            lines.append(header)
            lines.append('')

        # Sort categories by order
        sorted_categories = sorted(
            grouped_changes.keys(),
            key=lambda c: self.CATEGORY_CONFIG.get(c, {}).get('order', 99)
        )

        # Format each category
        for category in sorted_categories:
            changes = grouped_changes.get(category, [])
            if not changes:
                continue

            section = self._format_category_section(category, changes)
            if section:
                lines.append(section)
                lines.append('')

        # Add footnotes if provided
        if footnotes:
            footnote_section = self._format_footnotes(footnotes)
            lines.append(footnote_section)

        return '\n'.join(lines)

    def _format_header(self, version: Optional[str],
                       release_date: Optional[str]) -> str:
        """Format the changelog header."""
        if version:
            header = f"# Release Notes - {version}"
        else:
            header = "# Release Notes"

        if release_date:
            header += f"\n\n*Released: {release_date}*"
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            header += f"\n\n*Released: {today}*"

        return header

    def _format_category_section(self, category: str,
                                  changes: List[Dict[str, Any]]) -> str:
        """Format a single category section."""
        config = self.CATEGORY_CONFIG.get(category, {
            'heading': category.title(),
            'emoji': '',
            'order': 99
        })

        lines = []

        # Section heading
        heading = config['heading']
        if config['emoji']:
            heading = f"{config['emoji']} {heading}"
        lines.append(f"## {heading}")
        lines.append('')

        # Bullet points
        for change in changes:
            bullet = self._format_bullet_point(change)
            if bullet:
                lines.append(bullet)

        return '\n'.join(lines)

    def _format_bullet_point(self, change: Dict[str, Any]) -> str:
        """Format a single change as a bullet point."""
        description = change.get('description', '')

        if not description:
            return ''

        # Clean up the description
        description = self._clean_description(description)

        # Format as bullet point
        return f"- {description}"

    def _clean_description(self, description: str) -> str:
        """Clean and format a description for output."""
        # Ensure proper capitalization
        if description and description[0].islower():
            description = description[0].upper() + description[1:]

        # Remove trailing punctuation except for question marks
        description = description.rstrip('.,;:')

        # Ensure single line
        description = description.replace('\n', ' ').strip()

        # Remove any remaining technical artifacts
        description = self._remove_technical_artifacts(description)

        return description

    def _remove_technical_artifacts(self, text: str) -> str:
        """Remove technical artifacts from text."""
        # Remove file paths
        text = re.sub(r'/[\w/.-]+\.\w+', '', text)

        # Remove Windows paths
        text = re.sub(r'[A-Z]:\\[\w\\.-]+', '', text)

        # Remove git hashes
        text = re.sub(r'\b[a-f0-9]{7,40}\b', '', text)

        # Remove URLs but keep the description
        text = re.sub(r'https?://\S+', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def _format_footnotes(self, footnotes: List[str]) -> str:
        """Format footnotes section."""
        lines = ['---', '', '**Notes:**']

        for note in footnotes:
            # Filter out any notes that might contain secrets
            if self._contains_sensitive_info(note):
                continue
            lines.append(f"- {note}")

        return '\n'.join(lines)

    def _contains_sensitive_info(self, text: str) -> bool:
        """Check if text contains potentially sensitive information."""
        sensitive_patterns = [
            r'password\s*[:=]',
            r'secret\s*[:=]',
            r'api[_-]?key\s*[:=]',
            r'token\s*[:=]',
            r'auth\s*[:=]',
            r'\b[A-Za-z0-9+/]{40,}\b',  # Long base64-like strings
            r'Bearer\s+\S+',  # Bearer tokens
            r'Basic\s+\S+',  # Basic auth
        ]

        text_lower = text.lower()
        for pattern in sensitive_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def format_slack_message(self, grouped_changes: Dict[str, List[Dict[str, Any]]],
                              version: Optional[str] = None,
                              summary: Optional[str] = None) -> str:
        """
        Format changes as a Slack-friendly message.

        Similar to changelog but more concise for Slack's format.

        Args:
            grouped_changes: Changes grouped by category
            version: Optional version string
            summary: Optional one-line summary

        Returns:
            Slack-formatted markdown string
        """
        lines = []

        # Header for Slack
        if version:
            lines.append(f"*Release {version} is now available!*")
        else:
            lines.append("*New Release Available!*")

        if summary:
            lines.append(f"_{summary}_")

        lines.append('')

        # Sort and format categories
        sorted_categories = sorted(
            grouped_changes.keys(),
            key=lambda c: self.CATEGORY_CONFIG.get(c, {}).get('order', 99)
        )

        for category in sorted_categories:
            changes = grouped_changes.get(category, [])
            if not changes:
                continue

            # Category header (bold for Slack)
            config = self.CATEGORY_CONFIG.get(category, {'heading': category.title()})
            lines.append(f"*{config['heading']}*")

            # Limit to top 5 changes per category for Slack
            for change in changes[:5]:
                description = self._clean_description(change.get('description', ''))
                if description:
                    lines.append(f"• {description}")

            if len(changes) > 5:
                lines.append(f"  _...and {len(changes) - 5} more_")

            lines.append('')

        return '\n'.join(lines)

    def format_simple_list(self, grouped_changes: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format changes as a simple bulleted list without headings.
        Useful for quick updates or small releases.

        Args:
            grouped_changes: Changes grouped by category

        Returns:
            Simple bullet list
        """
        lines = []

        # Flatten all changes in order
        all_changes = []
        sorted_categories = sorted(
            grouped_changes.keys(),
            key=lambda c: self.CATEGORY_CONFIG.get(c, {}).get('order', 99)
        )

        for category in sorted_categories:
            all_changes.extend(grouped_changes.get(category, []))

        for change in all_changes:
            description = self._clean_description(change.get('description', ''))
            if description:
                lines.append(f"- {description}")

        return '\n'.join(lines)

    def save_to_file(self, content: str, file_path: str) -> bool:
        """
        Save formatted content to a markdown file.

        Args:
            content: Formatted markdown content
            file_path: Path to save the file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def generate_filename(self, version: Optional[str] = None,
                          prefix: str = "RELEASE_NOTES") -> str:
        """
        Generate a filename for the changelog.

        Args:
            version: Optional version string
            prefix: Filename prefix

        Returns:
            Generated filename
        """
        date_str = datetime.now().strftime("%Y%m%d")

        if version:
            # Clean version string for filename
            clean_version = re.sub(r'[^\w.-]', '', version)
            return f"{prefix}_{clean_version}.md"
        else:
            return f"{prefix}_{date_str}.md"
