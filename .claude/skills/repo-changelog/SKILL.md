---
name: repo-changelog
description: Analyzes git repositories to present commit history in a user-friendly format with intelligent grouping by type and customizable filtering
---

# Repository Changelog Analyzer

This skill provides intelligent analysis of git repository commit history, transforming raw git logs into user-friendly, categorized summaries that help teams understand what changed in their codebase.

## Capabilities

- **Tag-Based Analysis**: Show all commits since a specific git tag (e.g., "show me what changed since v1.2.0")
- **Recent Commit Analysis**: Display the last N commits with customizable count (default: 15)
- **Conventional Commit Parsing**: Automatically detects and groups commits following conventional commit standards
- **Smart Categorization**: Groups changes by type (features, fixes, refactors, docs, tests, etc.)
- **User-Friendly Formatting**: Presents commits in readable format with clear summaries
- **Commit Links**: Generates links to specific commits (when repository URL is available)
- **Statistical Summary**: Provides overview metrics (total commits, changes by type, contributors)
- **Flexible Input**: Works with any git repository path or current directory

## Input Requirements

The skill accepts the following inputs:

- **Repository Path** (optional): Absolute path to git repository (defaults to current directory)
- **Tag Name** (optional): Git tag to start analysis from (e.g., "v1.2.0", "release-2024-01")
- **Commit Count** (optional): Number of recent commits to analyze (default: 15, max: 100)
- **Group by Type** (optional): Enable/disable grouping by conventional commit types (default: enabled)
- **Include Links** (optional): Generate commit URLs if remote repository configured (default: enabled)

**Formats Accepted**:
- Natural language request: "Show me what changed since v1.2.0"
- JSON input with structured parameters
- Command-line style: `--since v1.2.0 --count 20 --path /path/to/repo`

## Output Formats

The skill produces:

1. **Summary Statistics**:
   - Total commits analyzed
   - Date range covered
   - Number of contributors
   - Changes breakdown by type

2. **Grouped Changelog**:
   - **Features** (feat): New functionality added
   - **Bug Fixes** (fix): Issues resolved
   - **Refactoring** (refactor): Code improvements without feature changes
   - **Documentation** (docs): Documentation updates
   - **Tests** (test): Test additions or modifications
   - **Chores** (chore): Maintenance tasks
   - **Other**: Commits not following conventional format

3. **Commit Details**:
   - Commit hash (short format)
   - Author and date
   - Commit message (cleaned and formatted)
   - Link to commit (if available)
   - Files changed count

4. **Export Formats**:
   - Markdown (default)
   - JSON (for programmatic use)
   - Plain text (for simple output)

## How to Use

**Natural Language Examples**:
- "Show me what changed since v1.2.0"
- "Give me the last 20 commits in this repository"
- "Analyze commits since tag release-2024-01 and group them by type"
- "What's new in /path/to/my-project since v2.0.0?"

**Structured Request**:
```json
{
  "repo_path": "/home/user/my-project",
  "since_tag": "v1.2.0",
  "max_commits": 25,
  "group_by_type": true
}
```

## Scripts

- `analyze_commits.py`: Main git analysis engine that parses commit history
- `categorize_commits.py`: Conventional commit parser and categorization logic
- `format_changelog.py`: Output formatting and presentation layer

## Best Practices

1. **Use Conventional Commits**: For best results, follow conventional commit format in your repository
2. **Specify Tags Clearly**: Use exact tag names (case-sensitive)
3. **Set Reasonable Limits**: For large repositories, start with smaller commit counts (15-25)
4. **Include Repository URL**: Configure remote URL for automatic commit links
5. **Regular Analysis**: Run after each release or sprint to track progress
6. **Combine Outputs**: Use JSON output for further processing or integration

## Limitations

- **Git Repository Required**: Only works with valid git repositories
- **Tag Must Exist**: Specified tags must exist in the repository
- **Conventional Commits Optional**: Works without conventional commits but grouping is less meaningful
- **Performance**: Very large commit histories (>1000 commits) may take longer to process
- **Remote URL**: Commit links only work if git remote is configured
- **Merge Commits**: Complex merge commits may appear ungrouped
- **Date Ranges**: Currently supports tag-based or count-based filtering, not arbitrary date ranges

## When to Use This Skill

**Perfect for**:
- Release note generation
- Sprint retrospectives
- Change documentation
- Code review preparation
- Understanding recent repository activity
- Tracking feature development

**Not Ideal for**:
- Real-time git monitoring
- Detailed code diff analysis
- Git repository management/modification
- Automated deployment decisions
