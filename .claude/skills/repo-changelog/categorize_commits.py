"""
Conventional commit parser and categorization module.
Groups commits by type following conventional commit standards.
"""

import re
from typing import Dict, List, Any
from collections import defaultdict


class CommitCategorizer:
    """Categorize commits using conventional commit format."""

    # Conventional commit types and their descriptions
    COMMIT_TYPES = {
        'feat': {
            'label': 'Features',
            'description': 'New functionality added',
            'emoji': '✨'
        },
        'fix': {
            'label': 'Bug Fixes',
            'description': 'Issues resolved',
            'emoji': '🐛'
        },
        'docs': {
            'label': 'Documentation',
            'description': 'Documentation updates',
            'emoji': '📝'
        },
        'style': {
            'label': 'Styles',
            'description': 'Code style changes (formatting, etc.)',
            'emoji': '💄'
        },
        'refactor': {
            'label': 'Refactoring',
            'description': 'Code improvements without feature changes',
            'emoji': '♻️'
        },
        'perf': {
            'label': 'Performance',
            'description': 'Performance improvements',
            'emoji': '⚡'
        },
        'test': {
            'label': 'Tests',
            'description': 'Test additions or modifications',
            'emoji': '✅'
        },
        'build': {
            'label': 'Build System',
            'description': 'Build system or dependencies changes',
            'emoji': '🔧'
        },
        'ci': {
            'label': 'CI/CD',
            'description': 'CI/CD pipeline changes',
            'emoji': '👷'
        },
        'chore': {
            'label': 'Chores',
            'description': 'Maintenance tasks',
            'emoji': '🔨'
        },
        'revert': {
            'label': 'Reverts',
            'description': 'Reverted changes',
            'emoji': '⏪'
        }
    }

    # Conventional commit pattern
    CONVENTIONAL_PATTERN = re.compile(
        r'^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<description>.+)$',
        re.IGNORECASE
    )

    def __init__(self, commits: List[Dict[str, Any]]):
        """
        Initialize categorizer with commits.

        Args:
            commits: List of commit dictionaries from GitCommitAnalyzer
        """
        self.commits = commits
        self.categorized = defaultdict(list)
        self.parsed_commits = []

    def categorize(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize commits by type.

        Returns:
            Dictionary mapping commit types to lists of commits
        """
        for commit in self.commits:
            parsed = self._parse_commit(commit)
            self.parsed_commits.append(parsed)

            commit_type = parsed['type']
            self.categorized[commit_type].append(parsed)

        return dict(self.categorized)

    def _parse_commit(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse commit message using conventional commit format.

        Args:
            commit: Commit dictionary

        Returns:
            Enhanced commit dictionary with parsed metadata
        """
        message = commit.get('subject', commit.get('message', ''))

        # Try to match conventional commit pattern
        match = self.CONVENTIONAL_PATTERN.match(message)

        if match:
            commit_type = match.group('type').lower()
            scope = match.group('scope')
            is_breaking = match.group('breaking') is not None
            description = match.group('description')

            # Validate type exists in our known types
            if commit_type not in self.COMMIT_TYPES:
                commit_type = 'other'
        else:
            # Not a conventional commit
            commit_type = 'other'
            scope = None
            is_breaking = False
            description = message

        return {
            **commit,  # Include all original commit data
            'type': commit_type,
            'scope': scope,
            'is_breaking': is_breaking,
            'description': description,
            'original_message': message,
            'type_info': self.COMMIT_TYPES.get(commit_type, {
                'label': 'Other',
                'description': 'Uncategorized changes',
                'emoji': '📦'
            })
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Generate summary of categorized commits.

        Returns:
            Summary statistics by category
        """
        summary = {
            'total_commits': len(self.commits),
            'by_type': {},
            'breaking_changes': [],
            'conventional_percentage': 0
        }

        # Count by type
        for commit_type, commits in self.categorized.items():
            type_info = self.COMMIT_TYPES.get(commit_type, {
                'label': 'Other',
                'description': 'Uncategorized changes',
                'emoji': '📦'
            })

            summary['by_type'][commit_type] = {
                'count': len(commits),
                'label': type_info['label'],
                'emoji': type_info['emoji']
            }

        # Find breaking changes
        summary['breaking_changes'] = [
            commit for commit in self.parsed_commits
            if commit.get('is_breaking', False)
        ]

        # Calculate conventional commit percentage
        conventional_count = sum(
            1 for commit in self.parsed_commits
            if commit['type'] != 'other'
        )
        if self.commits:
            summary['conventional_percentage'] = (
                conventional_count / len(self.commits) * 100
            )

        return summary

    def get_grouped_commits(self) -> List[Dict[str, Any]]:
        """
        Get commits grouped by type with metadata.

        Returns:
            List of groups, each containing type info and commits
        """
        groups = []

        # Define order of types
        type_order = [
            'feat', 'fix', 'perf', 'refactor', 'docs',
            'style', 'test', 'build', 'ci', 'chore',
            'revert', 'other'
        ]

        for commit_type in type_order:
            if commit_type in self.categorized:
                commits = self.categorized[commit_type]
                type_info = self.COMMIT_TYPES.get(commit_type, {
                    'label': 'Other',
                    'description': 'Uncategorized changes',
                    'emoji': '📦'
                })

                groups.append({
                    'type': commit_type,
                    'label': type_info['label'],
                    'description': type_info['description'],
                    'emoji': type_info['emoji'],
                    'count': len(commits),
                    'commits': commits
                })

        return groups

    def detect_scopes(self) -> List[str]:
        """
        Extract all unique scopes from commits.

        Returns:
            List of unique scope names
        """
        scopes = set()
        for commit in self.parsed_commits:
            scope = commit.get('scope')
            if scope:
                scopes.add(scope)

        return sorted(list(scopes))
