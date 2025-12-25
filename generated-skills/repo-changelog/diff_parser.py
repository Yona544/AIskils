"""
Diff parser and interpreter.
Reads actual code diffs and translates them into plain English descriptions
that end-users can understand. No technical jargon, functions, or variables.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class DiffParser:
    """
    Parses git diffs and interprets them into user-friendly descriptions.
    Focuses on the end result, not technical implementation details.
    """

    # File type categories for context
    FILE_CATEGORIES = {
        'ui': ['.html', '.css', '.scss', '.less', '.jsx', '.tsx', '.vue', '.svelte'],
        'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.config'],
        'docs': ['.md', '.txt', '.rst', '.doc', '.docx', '.pdf'],
        'code': ['.py', '.js', '.ts', '.go', '.java', '.cs', '.rb', '.php', '.swift', '.kt'],
        'data': ['.sql', '.csv', '.xml'],
        'build': ['Makefile', 'Dockerfile', '.sh', '.bat', '.ps1', 'package.json', 'requirements.txt'],
        'test': ['test_', '_test.', '.test.', 'spec.']
    }

    # Patterns that indicate user-facing changes
    USER_FACING_PATTERNS = [
        # UI text patterns
        (r'["\']([^"\']{10,100})["\']', 'text_change'),  # String literals
        (r'message\s*[:=]\s*["\'](.+?)["\']', 'message_change'),
        (r'label\s*[:=]\s*["\'](.+?)["\']', 'label_change'),
        (r'title\s*[:=]\s*["\'](.+?)["\']', 'title_change'),
        (r'error\s*[:=]\s*["\'](.+?)["\']', 'error_change'),
        (r'placeholder\s*[:=]\s*["\'](.+?)["\']', 'placeholder_change'),
        # Feature toggles
        (r'enabled?\s*[:=]\s*(true|false)', 'toggle_change'),
        (r'disabled?\s*[:=]\s*(true|false)', 'toggle_change'),
        (r'show\w*\s*[:=]\s*(true|false)', 'visibility_change'),
        (r'hide\w*\s*[:=]\s*(true|false)', 'visibility_change'),
        (r'visible\s*[:=]\s*(true|false)', 'visibility_change'),
        # Settings/config
        (r'timeout\s*[:=]\s*(\d+)', 'timeout_change'),
        (r'limit\s*[:=]\s*(\d+)', 'limit_change'),
        (r'max\w*\s*[:=]\s*(\d+)', 'limit_change'),
        (r'min\w*\s*[:=]\s*(\d+)', 'limit_change'),
        # URLs and endpoints
        (r'url\s*[:=]\s*["\'](.+?)["\']', 'url_change'),
        (r'endpoint\s*[:=]\s*["\'](.+?)["\']', 'endpoint_change'),
    ]

    def __init__(self):
        """Initialize the diff parser."""
        self.changes: List[Dict[str, Any]] = []

    def parse_diff(self, diff_content: str, files_changed: List[Dict[str, str]],
                   commit_subject: str) -> List[Dict[str, Any]]:
        """
        Parse a diff and extract user-friendly change descriptions.

        Args:
            diff_content: Raw git diff content
            files_changed: List of files with their status (added, modified, deleted)
            commit_subject: The commit message subject

        Returns:
            List of change descriptions
        """
        changes = []

        # First, try to understand from the commit message
        message_interpretation = self._interpret_commit_message(commit_subject)
        if message_interpretation:
            changes.append(message_interpretation)

        # Parse the actual diff for more details
        diff_changes = self._parse_diff_content(diff_content, files_changed)
        changes.extend(diff_changes)

        # Analyze file-level changes
        file_changes = self._analyze_file_changes(files_changed)
        changes.extend(file_changes)

        return changes

    def _interpret_commit_message(self, subject: str) -> Optional[Dict[str, Any]]:
        """
        Interpret the commit message into a user-friendly description.

        Args:
            subject: Commit message subject line

        Returns:
            Change description dictionary or None
        """
        if not subject:
            return None

        # Clean up common prefixes
        clean_subject = subject

        # Remove conventional commit prefixes
        clean_subject = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+?\))?!?:\s*', '', clean_subject, flags=re.IGNORECASE)

        # Remove ticket references
        clean_subject = re.sub(r'\[?[A-Z]+-\d+\]?\s*', '', clean_subject)
        clean_subject = re.sub(r'#\d+\s*', '', clean_subject)

        # Remove WIP, TODO prefixes
        clean_subject = re.sub(r'^(WIP|TODO|FIXME|HACK):\s*', '', clean_subject, flags=re.IGNORECASE)

        clean_subject = clean_subject.strip()

        if not clean_subject or len(clean_subject) < 5:
            return None

        # Determine category from original subject
        category = self._categorize_from_message(subject)

        return {
            'description': self._humanize_description(clean_subject),
            'category': category,
            'source': 'commit_message',
            'confidence': 'medium',
            'raw': subject
        }

    def _categorize_from_message(self, message: str) -> str:
        """Determine category from commit message."""
        message_lower = message.lower()

        # Check for conventional commit prefixes
        if re.match(r'^feat(\(.+?\))?!?:', message_lower):
            return 'feature'
        if re.match(r'^fix(\(.+?\))?!?:', message_lower):
            return 'bugfix'
        if re.match(r'^(perf|enhance|improve)(\(.+?\))?:', message_lower):
            return 'enhancement'
        if re.match(r'^(docs|doc)(\(.+?\))?:', message_lower):
            return 'other'
        if re.match(r'^(refactor|style|chore|build|ci|test)(\(.+?\))?:', message_lower):
            return 'other'
        if re.match(r'^revert(\(.+?\))?:', message_lower):
            return 'change'

        # Check for keywords
        if any(word in message_lower for word in ['add', 'new', 'create', 'implement', 'introduce']):
            return 'feature'
        if any(word in message_lower for word in ['fix', 'bug', 'issue', 'error', 'crash', 'resolve']):
            return 'bugfix'
        if any(word in message_lower for word in ['improve', 'enhance', 'update', 'upgrade', 'optimize', 'better']):
            return 'enhancement'
        if any(word in message_lower for word in ['remove', 'delete', 'deprecate']):
            return 'change'
        if any(word in message_lower for word in ['breaking', 'migrate', 'migration']):
            return 'breaking'

        return 'other'

    def _humanize_description(self, text: str) -> str:
        """
        Convert technical description to human-friendly language.

        Args:
            text: Technical description

        Returns:
            Human-friendly description
        """
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]

        # Remove technical terms and make more readable
        replacements = [
            (r'\bimpl(?:ement(?:ed|s|ation)?)?', 'Added'),
            (r'\brefactor(?:ed|ing)?', 'Improved'),
            (r'\boptimiz(?:e|ed|ation)', 'Improved speed of'),
            (r'\bapi\b', 'system'),
            (r'\bendpoint\b', 'feature'),
            (r'\bmodule\b', 'component'),
            (r'\bcomponent\b', 'feature'),
            (r'\bhandler\b', 'processor'),
            (r'\bcallback\b', 'action'),
            (r'\butil(?:ity|s)?\b', 'helper'),
            (r'\binit(?:ialize)?(?:d)?\b', 'set up'),
            (r'\bconfig(?:uration)?\b', 'settings'),
            (r'\bparam(?:eter)?s?\b', 'options'),
            (r'\bauth(?:entication)?\b', 'login'),
            (r'\bvalidat(?:e|ion)\b', 'check'),
        ]

        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text.strip()

    def _parse_diff_content(self, diff_content: str, files_changed: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Parse actual diff content for user-facing changes.

        Args:
            diff_content: Raw diff content
            files_changed: List of changed files

        Returns:
            List of detected changes
        """
        changes = []

        if not diff_content:
            return changes

        # Look for user-facing patterns in additions
        additions = self._extract_additions(diff_content)

        for line in additions:
            for pattern, change_type in self.USER_FACING_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    # Found a user-facing change
                    value = match.group(1) if match.groups() else match.group(0)

                    # Skip if it looks like code (has function calls, brackets, etc.)
                    if self._looks_like_code(value):
                        continue

                    description = self._describe_pattern_change(change_type, value, line)
                    if description:
                        changes.append({
                            'description': description,
                            'category': self._category_from_change_type(change_type),
                            'source': 'diff_analysis',
                            'confidence': 'high',
                            'raw': line.strip()
                        })

        return changes

    def _extract_additions(self, diff_content: str) -> List[str]:
        """Extract added lines from diff."""
        additions = []
        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                additions.append(line[1:])  # Remove the '+' prefix
        return additions

    def _looks_like_code(self, text: str) -> bool:
        """Check if text looks like code rather than user-facing content."""
        code_patterns = [
            r'\w+\s*\(',  # Function calls
            r'\{\s*\}',  # Empty braces
            r'\[\s*\]',  # Empty brackets
            r'=>',  # Arrow functions
            r'->',  # Method chains
            r'\$\w+',  # Variables
            r'^\d+$',  # Just numbers
            r'^[a-z_]+$',  # Just identifiers
            r'^\s*$',  # Empty/whitespace
        ]

        for pattern in code_patterns:
            if re.search(pattern, text):
                return True

        # Too short to be meaningful text
        if len(text) < 3:
            return True

        return False

    def _describe_pattern_change(self, change_type: str, value: str, context: str) -> Optional[str]:
        """
        Create a description for a pattern-matched change.

        Args:
            change_type: Type of change detected
            value: The matched value
            context: Full line context

        Returns:
            Human-friendly description or None
        """
        descriptions = {
            'text_change': f'Updated text: "{value[:50]}..."' if len(value) > 50 else f'Updated text: "{value}"',
            'message_change': f'Changed message to: "{value[:50]}..."' if len(value) > 50 else f'Changed message: "{value}"',
            'label_change': f'Updated label: "{value}"',
            'title_change': f'Changed title to: "{value}"',
            'error_change': f'Improved error message: "{value[:50]}..."' if len(value) > 50 else None,
            'placeholder_change': f'Updated placeholder text: "{value}"',
            'toggle_change': 'Enabled feature' if value.lower() == 'true' else 'Disabled feature',
            'visibility_change': 'Made element visible' if value.lower() == 'true' else 'Hidden element',
            'timeout_change': f'Adjusted timeout to {value} seconds',
            'limit_change': f'Changed limit to {value}',
            'url_change': None,  # Don't expose URLs
            'endpoint_change': None,  # Don't expose endpoints
        }

        return descriptions.get(change_type)

    def _category_from_change_type(self, change_type: str) -> str:
        """Map change type to category."""
        category_map = {
            'text_change': 'change',
            'message_change': 'enhancement',
            'label_change': 'enhancement',
            'title_change': 'change',
            'error_change': 'enhancement',
            'placeholder_change': 'enhancement',
            'toggle_change': 'feature',
            'visibility_change': 'change',
            'timeout_change': 'enhancement',
            'limit_change': 'change',
        }
        return category_map.get(change_type, 'other')

    def _analyze_file_changes(self, files_changed: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Analyze file-level changes for high-level descriptions.

        Args:
            files_changed: List of changed files with status

        Returns:
            List of file-based change descriptions
        """
        changes = []

        # Group by category
        added_files = [f for f in files_changed if f['status'] == 'added']
        deleted_files = [f for f in files_changed if f['status'] == 'deleted']

        # Check for new features (new UI files, new screens)
        new_ui_files = [f for f in added_files if self._is_ui_file(f['path'])]
        if new_ui_files:
            for f in new_ui_files[:3]:  # Limit to 3
                name = self._get_friendly_name(f['path'])
                if name:
                    changes.append({
                        'description': f'Added new {name}',
                        'category': 'feature',
                        'source': 'file_analysis',
                        'confidence': 'medium',
                        'raw': f['path']
                    })

        # Check for removed features
        removed_ui_files = [f for f in deleted_files if self._is_ui_file(f['path'])]
        if removed_ui_files:
            for f in removed_ui_files[:3]:
                name = self._get_friendly_name(f['path'])
                if name:
                    changes.append({
                        'description': f'Removed {name}',
                        'category': 'change',
                        'source': 'file_analysis',
                        'confidence': 'medium',
                        'raw': f['path']
                    })

        return changes

    def _is_ui_file(self, path: str) -> bool:
        """Check if file is UI-related."""
        path_lower = path.lower()
        for ext in self.FILE_CATEGORIES['ui']:
            if path_lower.endswith(ext):
                return True
        return False

    def _get_friendly_name(self, path: str) -> Optional[str]:
        """Extract a friendly name from file path."""
        filename = Path(path).stem

        # Skip common non-descriptive names
        skip_names = ['index', 'main', 'app', 'utils', 'helpers', 'common', 'types', 'constants']
        if filename.lower() in skip_names:
            return None

        # Convert to readable name
        # CamelCase -> separate words
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', filename)
        # snake_case -> separate words
        name = name.replace('_', ' ').replace('-', ' ')
        # Capitalize
        name = name.title()

        return name if len(name) > 2 else None

    def get_net_changes(self, all_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter changes to only include net changes (eliminate flip-flops).

        This is a placeholder - actual implementation would need to track
        the same item across commits and compare initial vs final state.

        Args:
            all_changes: All detected changes

        Returns:
            Filtered list of net changes
        """
        # Deduplicate by description
        seen = set()
        unique_changes = []

        for change in all_changes:
            desc = change['description'].lower()
            if desc not in seen:
                seen.add(desc)
                unique_changes.append(change)

        return unique_changes
