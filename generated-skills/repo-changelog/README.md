# Repo Changelog - Git Repository Analysis Skill

Transform raw git commit history into beautiful, categorized changelogs.

## Overview

The **repo-changelog** skill analyzes git repositories and presents commit history in a user-friendly format with intelligent grouping, statistics, and multiple output formats.

## Features

- **Tag-Based Analysis**: Show commits since any git tag
- **Recent Commits**: Display last N commits (default: 15)
- **Conventional Commit Support**: Automatically detects and groups commits by type
- **Smart Categorization**: Groups changes (features, fixes, docs, refactors, etc.)
- **Multiple Formats**: Output as Markdown, JSON, or plain text
- **Commit Links**: Generates URLs to commits on GitHub/GitLab/Bitbucket
- **Statistics**: Contributors, file changes, date ranges, breaking changes

## Installation

### Claude Code (Project-Level)
```bash
cp -r repo-changelog ~/.claude/skills/
```

### Claude Code (User-Level)
```bash
cp -r repo-changelog ~/.claude/skills/
```

### Claude Desktop
Drag and drop the `repo-changelog.zip` file into Claude Desktop.

## Quick Start

```
Hey Claude—I just added the "repo-changelog" skill. Can you show me what changed since v1.2.0?
```

## Python Modules

The skill includes three Python modules:

1. **analyze_commits.py** - Git repository analysis and commit extraction
2. **categorize_commits.py** - Conventional commit parsing and categorization
3. **format_changelog.py** - Output formatting (Markdown, JSON, plain text)

## Usage Examples

### Show Changes Since a Tag
```
Show me what changed since v1.2.0
```

### Recent Commits
```
Give me the last 20 commits
```

### Specific Repository
```
Analyze commits in /path/to/repo since release-2024-01
```

### JSON Output
```
Analyze last 30 commits and give me JSON output
```

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_path` | string | current dir | Path to git repository |
| `since_tag` | string | - | Git tag to start from |
| `max_commits` | number | 15 | Number of commits (max 100) |
| `group_by_type` | boolean | true | Enable conventional commit grouping |
| `output_format` | string | markdown | Output format (markdown/json/text) |
| `include_emoji` | boolean | true | Include emoji icons |
| `include_links` | boolean | true | Generate commit URLs |

## Output Formats

### Markdown (Default)
- Summary statistics
- Grouped commits by type
- Commit links
- Contributors list

### JSON
- Structured data
- Programmatic processing
- All metadata included

### Plain Text
- Simple text format
- No special formatting
- Easy copy/paste

## Conventional Commit Support

The skill recognizes these commit types:

| Type | Label | Description |
|------|-------|-------------|
| `feat` | Features | New functionality |
| `fix` | Bug Fixes | Issue resolutions |
| `docs` | Documentation | Documentation updates |
| `style` | Styles | Code formatting |
| `refactor` | Refactoring | Code improvements |
| `perf` | Performance | Performance improvements |
| `test` | Tests | Test additions/changes |
| `build` | Build System | Build/dependency changes |
| `ci` | CI/CD | Pipeline changes |
| `chore` | Chores | Maintenance tasks |
| `revert` | Reverts | Reverted changes |

## Requirements

- Git repository
- Python 3.7+ (handled by Claude)
- Git command-line tools installed

## File Structure

```
repo-changelog/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── HOW_TO_USE.md              # Usage examples
├── analyze_commits.py         # Git analysis module
├── categorize_commits.py      # Categorization module
├── format_changelog.py        # Formatting module
├── sample_input.json          # Example input
└── expected_output.json       # Example output
```

## Example Output

```markdown
# Changelog

## Summary

**Total Commits**: 18
**Date Range**: 2024-12-20 to 2024-10-15
**Contributors**: 2
**Conventional Commits**: 100.0%

### Changes by Type

- ✨ **Features**: 7
- 🐛 **Bug Fixes**: 5
- 📝 **Documentation**: 3

## Changes

### ✨ Features (7)

- [`abc123d`](https://github.com/example/repo/commit/abc123d) **auth**: Add user authentication system (*John Doe*, 2024-12-20)
- [`def456e`](https://github.com/example/repo/commit/def456e) **api**: Implement REST API endpoints (*Jane Smith*, 2024-12-18)
```

## Use Cases

- Release note generation
- Sprint retrospectives
- Code review preparation
- Change documentation
- Team progress updates
- Audit trail tracking

## Limitations

- Requires valid git repository
- Tags must exist in repository
- Large histories (>1000 commits) may be slow
- Commit links require configured git remote
- Date-based filtering not yet supported (use tags or counts)

## Version

**Version**: 1.0.0
**Last Updated**: December 25, 2024
**Compatibility**: Claude Code, Claude Desktop, Claude API

## License

This skill is part of the Claude Code Skills Factory.

## Support

For issues or questions, refer to the HOW_TO_USE.md file or Claude Code documentation.
