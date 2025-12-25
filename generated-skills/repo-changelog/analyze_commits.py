"""
Git repository commit analysis module.
Provides functionality to extract and analyze commit history from git repositories.
"""

import subprocess
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


class GitCommitAnalyzer:
    """Analyze git commit history and extract structured data."""

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize analyzer with repository path.

        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = repo_path or os.getcwd()
        self.commits = []
        self.remote_url = None

        if not self._is_git_repo():
            raise ValueError(f"Not a valid git repository: {self.repo_path}")

        self._get_remote_url()

    def _is_git_repo(self) -> bool:
        """Check if path is a valid git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_remote_url(self) -> None:
        """Extract remote repository URL for generating commit links."""
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Convert SSH to HTTPS format
                if url.startswith('git@'):
                    url = url.replace('git@', 'https://')
                    url = url.replace('.com:', '.com/')
                # Remove .git suffix
                url = url.rstrip('.git')
                self.remote_url = url
        except Exception:
            pass

    def get_commits_since_tag(self, tag: str, max_commits: int = 100) -> List[Dict[str, Any]]:
        """
        Get commits since a specific tag.

        Args:
            tag: Git tag name
            max_commits: Maximum number of commits to retrieve

        Returns:
            List of commit dictionaries
        """
        try:
            # Verify tag exists
            tag_check = subprocess.run(
                ['git', 'rev-parse', tag],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if tag_check.returncode != 0:
                raise ValueError(f"Tag '{tag}' not found in repository")

            # Get commits since tag
            git_format = '--pretty=format:%H|%h|%an|%ae|%ai|%s|%b'
            result = subprocess.run(
                ['git', 'log', f'{tag}..HEAD', git_format, f'-n{max_commits}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"Git command failed: {result.stderr}")

            self.commits = self._parse_git_log(result.stdout)
            return self.commits

        except subprocess.TimeoutExpired:
            raise RuntimeError("Git command timed out")
        except Exception as e:
            raise RuntimeError(f"Error getting commits since tag: {str(e)}")

    def get_recent_commits(self, count: int = 15) -> List[Dict[str, Any]]:
        """
        Get the most recent N commits.

        Args:
            count: Number of commits to retrieve (default: 15, max: 100)

        Returns:
            List of commit dictionaries
        """
        count = min(count, 100)  # Cap at 100 for performance

        try:
            git_format = '--pretty=format:%H|%h|%an|%ae|%ai|%s|%b'
            result = subprocess.run(
                ['git', 'log', git_format, f'-n{count}'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"Git command failed: {result.stderr}")

            self.commits = self._parse_git_log(result.stdout)
            return self.commits

        except subprocess.TimeoutExpired:
            raise RuntimeError("Git command timed out")
        except Exception as e:
            raise RuntimeError(f"Error getting recent commits: {str(e)}")

    def _parse_git_log(self, git_output: str) -> List[Dict[str, Any]]:
        """
        Parse git log output into structured commit data.

        Args:
            git_output: Raw git log output

        Returns:
            List of parsed commit dictionaries
        """
        commits = []

        if not git_output.strip():
            return commits

        # Split by commit (git log separates commits with newlines)
        commit_entries = git_output.strip().split('\n')

        for entry in commit_entries:
            if not entry.strip():
                continue

            parts = entry.split('|', 6)
            if len(parts) < 6:
                continue

            full_hash, short_hash, author, email, date_str, subject = parts[:6]
            body = parts[6] if len(parts) > 6 else ""

            # Get files changed count
            files_changed = self._get_files_changed(full_hash)

            commit = {
                'hash': full_hash.strip(),
                'short_hash': short_hash.strip(),
                'author': author.strip(),
                'email': email.strip(),
                'date': date_str.strip(),
                'subject': subject.strip(),
                'body': body.strip(),
                'message': subject.strip(),  # For backward compatibility
                'files_changed': files_changed,
                'url': self._generate_commit_url(full_hash.strip()) if self.remote_url else None
            }

            commits.append(commit)

        return commits

    def _get_files_changed(self, commit_hash: str) -> int:
        """Get number of files changed in a commit."""
        try:
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return len([line for line in result.stdout.strip().split('\n') if line])
            return 0
        except Exception:
            return 0

    def _generate_commit_url(self, commit_hash: str) -> Optional[str]:
        """Generate URL to commit on remote repository."""
        if not self.remote_url:
            return None

        # Support GitHub, GitLab, Bitbucket
        if 'github.com' in self.remote_url:
            return f"{self.remote_url}/commit/{commit_hash}"
        elif 'gitlab.com' in self.remote_url or 'gitlab' in self.remote_url:
            return f"{self.remote_url}/-/commit/{commit_hash}"
        elif 'bitbucket.org' in self.remote_url:
            return f"{self.remote_url}/commits/{commit_hash}"
        else:
            # Generic format
            return f"{self.remote_url}/commit/{commit_hash}"

    def get_statistics(self) -> Dict[str, Any]:
        """
        Generate statistics about analyzed commits.

        Returns:
            Dictionary with commit statistics
        """
        if not self.commits:
            return {
                'total_commits': 0,
                'contributors': [],
                'date_range': None
            }

        # Get unique contributors
        contributors = list(set(
            f"{commit['author']} <{commit['email']}>"
            for commit in self.commits
        ))

        # Get date range
        dates = [commit['date'] for commit in self.commits]
        date_range = {
            'oldest': min(dates) if dates else None,
            'newest': max(dates) if dates else None
        }

        # Total files changed
        total_files = sum(commit.get('files_changed', 0) for commit in self.commits)

        return {
            'total_commits': len(self.commits),
            'contributors': contributors,
            'contributor_count': len(contributors),
            'date_range': date_range,
            'total_files_changed': total_files,
            'repository_path': self.repo_path,
            'remote_url': self.remote_url
        }
