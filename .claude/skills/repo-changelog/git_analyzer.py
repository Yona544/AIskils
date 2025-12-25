"""
Cross-platform Git repository analyzer.
Handles git operations for Windows, macOS, and Linux.
Supports GitHub, Bitbucket, and local repositories.
"""

import subprocess
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class GitAnalyzer:
    """
    Cross-platform git repository analyzer.
    Extracts commits, diffs, and metadata from git repositories.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize analyzer with repository path.

        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.remote_url: Optional[str] = None
        self.remote_type: Optional[str] = None  # 'github', 'bitbucket', or 'local'

        if not self._is_git_repo():
            raise ValueError(f"Not a valid git repository: {self.repo_path}")

        self._detect_remote()

    def _run_git(self, args: List[str], timeout: int = 60) -> Tuple[bool, str]:
        """
        Run a git command cross-platform.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds

        Returns:
            Tuple of (success, output)
        """
        try:
            # Use shell=True on Windows for better compatibility
            cmd = ['git'] + args
            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=timeout,
                # Windows-specific: prevent console window popup
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def _is_git_repo(self) -> bool:
        """Check if path is a valid git repository."""
        success, _ = self._run_git(['rev-parse', '--git-dir'], timeout=5)
        return success

    def _detect_remote(self) -> None:
        """Detect remote type (GitHub, Bitbucket, or local)."""
        success, output = self._run_git(['config', '--get', 'remote.origin.url'], timeout=5)

        if not success or not output.strip():
            self.remote_type = 'local'
            return

        url = output.strip()
        self.remote_url = self._normalize_remote_url(url)

        if 'github.com' in url.lower():
            self.remote_type = 'github'
        elif 'bitbucket' in url.lower():
            self.remote_type = 'bitbucket'
        else:
            self.remote_type = 'local'

    def _normalize_remote_url(self, url: str) -> str:
        """Convert SSH URLs to HTTPS format for linking."""
        # git@github.com:user/repo.git -> https://github.com/user/repo
        if url.startswith('git@'):
            url = url.replace('git@', 'https://')
            url = url.replace('.com:', '.com/')
            url = url.replace('.org:', '.org/')
        # Remove .git suffix
        if url.endswith('.git'):
            url = url[:-4]
        return url

    def get_tags(self) -> List[str]:
        """Get all tags sorted by version."""
        success, output = self._run_git(['tag', '--sort=-v:refname'])
        if not success:
            return []
        return [tag.strip() for tag in output.strip().split('\n') if tag.strip()]

    def get_latest_tag(self) -> Optional[str]:
        """Get the most recent tag."""
        tags = self.get_tags()
        return tags[0] if tags else None

    def get_commits_between_tags(self, from_tag: str, to_tag: str) -> List[Dict[str, Any]]:
        """
        Get commits between two tags.

        Args:
            from_tag: Starting tag (exclusive)
            to_tag: Ending tag (inclusive)

        Returns:
            List of commit dictionaries
        """
        # Verify tags exist
        for tag in [from_tag, to_tag]:
            success, _ = self._run_git(['rev-parse', tag], timeout=5)
            if not success:
                raise ValueError(f"Tag '{tag}' not found in repository")

        return self._get_commits(f'{from_tag}..{to_tag}')

    def get_commits_since_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get commits since a tag to HEAD.

        Args:
            tag: Starting tag (exclusive)

        Returns:
            List of commit dictionaries
        """
        success, _ = self._run_git(['rev-parse', tag], timeout=5)
        if not success:
            raise ValueError(f"Tag '{tag}' not found in repository")

        return self._get_commits(f'{tag}..HEAD')

    def get_recent_commits(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Get the most recent N commits.

        Args:
            count: Number of commits to retrieve

        Returns:
            List of commit dictionaries
        """
        return self._get_commits(f'-n {count}')

    def _get_commits(self, range_spec: str) -> List[Dict[str, Any]]:
        """
        Get commits matching a range specification.

        Args:
            range_spec: Git log range (e.g., 'v1.0..v1.1' or '-n 50')

        Returns:
            List of commit dictionaries
        """
        # Format: hash|short_hash|author|email|date|subject
        format_str = '%H|%h|%an|%ae|%ai|%s'

        args = ['log', f'--pretty=format:{format_str}']

        # Handle range spec
        if range_spec.startswith('-n'):
            args.append(range_spec)
        else:
            args.append(range_spec)

        success, output = self._run_git(args, timeout=120)
        if not success:
            return []

        commits = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue

            parts = line.split('|', 5)
            if len(parts) < 6:
                continue

            commit = {
                'hash': parts[0].strip(),
                'short_hash': parts[1].strip(),
                'author': parts[2].strip(),
                'email': parts[3].strip(),
                'date': parts[4].strip(),
                'subject': parts[5].strip(),
                'diff': None,  # Will be populated by get_commit_diff
                'files_changed': []
            }
            commits.append(commit)

        return commits

    def get_commit_diff(self, commit_hash: str) -> Dict[str, Any]:
        """
        Get the full diff for a commit.

        Args:
            commit_hash: Git commit hash

        Returns:
            Dictionary with diff information
        """
        # Get list of files changed
        success, files_output = self._run_git([
            'diff-tree', '--no-commit-id', '--name-status', '-r', commit_hash
        ], timeout=30)

        files_changed = []
        if success:
            for line in files_output.strip().split('\n'):
                if not line.strip():
                    continue
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    status, filepath = parts
                    files_changed.append({
                        'status': self._parse_file_status(status),
                        'path': filepath
                    })

        # Get the actual diff content
        success, diff_output = self._run_git([
            'show', commit_hash, '--pretty=format:', '--patch'
        ], timeout=60)

        return {
            'files_changed': files_changed,
            'diff_content': diff_output if success else '',
            'additions': self._count_diff_lines(diff_output, '+') if success else 0,
            'deletions': self._count_diff_lines(diff_output, '-') if success else 0
        }

    def _parse_file_status(self, status: str) -> str:
        """Convert git status code to readable status."""
        status_map = {
            'A': 'added',
            'M': 'modified',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied',
            'T': 'type_changed'
        }
        return status_map.get(status[0], 'modified')

    def _count_diff_lines(self, diff: str, prefix: str) -> int:
        """Count lines starting with prefix in diff."""
        count = 0
        for line in diff.split('\n'):
            if line.startswith(prefix) and not line.startswith(prefix * 3):
                count += 1
        return count

    def get_commit_body(self, commit_hash: str) -> str:
        """Get the full commit message body."""
        success, output = self._run_git([
            'log', '-1', '--pretty=format:%b', commit_hash
        ], timeout=10)
        return output.strip() if success else ''

    def get_file_content_at_commit(self, commit_hash: str, file_path: str) -> Optional[str]:
        """Get file content at a specific commit."""
        success, output = self._run_git([
            'show', f'{commit_hash}:{file_path}'
        ], timeout=30)
        return output if success else None

    def get_file_content_before_commit(self, commit_hash: str, file_path: str) -> Optional[str]:
        """Get file content before a specific commit."""
        success, output = self._run_git([
            'show', f'{commit_hash}^:{file_path}'
        ], timeout=30)
        return output if success else None

    def generate_commit_url(self, commit_hash: str) -> Optional[str]:
        """Generate URL to view commit on remote."""
        if not self.remote_url or self.remote_type == 'local':
            return None

        if self.remote_type == 'github':
            return f"{self.remote_url}/commit/{commit_hash}"
        elif self.remote_type == 'bitbucket':
            return f"{self.remote_url}/commits/{commit_hash}"

        return None

    def get_diff_between_refs(self, from_ref: str, to_ref: str) -> str:
        """
        Get combined diff between two refs (tags, commits, branches).

        Args:
            from_ref: Starting reference
            to_ref: Ending reference

        Returns:
            Combined diff content
        """
        success, output = self._run_git([
            'diff', from_ref, to_ref
        ], timeout=120)
        return output if success else ''

    def get_changed_files_between_refs(self, from_ref: str, to_ref: str) -> List[Dict[str, str]]:
        """
        Get list of files changed between two refs with their status.

        Args:
            from_ref: Starting reference
            to_ref: Ending reference

        Returns:
            List of file change dictionaries
        """
        success, output = self._run_git([
            'diff', '--name-status', from_ref, to_ref
        ], timeout=60)

        if not success:
            return []

        files = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                status, filepath = parts
                files.append({
                    'status': self._parse_file_status(status),
                    'path': filepath
                })

        return files
