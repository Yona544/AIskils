# How to Use the Repo Changelog Skill

Hey Claude—I just added the "repo-changelog" skill. Can you show me what changed since our last release?

## Example Invocations

### Example 1: Tag-Based Analysis
```
Hey Claude—I just added the "repo-changelog" skill. Can you show me what changed since v1.2.0?
```

### Example 2: Recent Commits
```
Hey Claude—I just added the "repo-changelog" skill. Can you give me the last 20 commits with a summary?
```

### Example 3: Specific Repository
```
Hey Claude—I just added the "repo-changelog" skill. Can you analyze commits in /home/user/my-project since tag release-2024-01?
```

### Example 4: Detailed Analysis with JSON Output
```
Hey Claude—I just added the "repo-changelog" skill. Can you analyze the last 30 commits and give me JSON output?
```

### Example 5: Release Notes Generation
```
Hey Claude—I just added the "repo-changelog" skill. Can you generate release notes for everything since v2.0.0?
```

## What to Provide

**Required**:
- Either a tag name (e.g., "v1.2.0") OR number of commits to analyze (e.g., 15)

**Optional**:
- Repository path (defaults to current directory)
- Output format preference (markdown, JSON, plain text)
- Include/exclude emoji icons
- Include/exclude commit links
- Maximum commits to analyze (for tag-based queries)

**Natural Language Examples**:
- "Show me changes since v1.2.0"
- "What are the last 15 commits?"
- "Analyze commits since release-2024-01 in /path/to/repo"
- "Give me a changelog for the last sprint"

**Structured Request**:
```json
{
  "repo_path": "/home/user/my-project",
  "since_tag": "v1.2.0",
  "max_commits": 25,
  "group_by_type": true,
  "output_format": "markdown",
  "include_emoji": true,
  "include_links": true
}
```

## What You'll Get

### Markdown Output (Default)
- **Summary Statistics**: Total commits, date range, contributors, breaking changes
- **Changes by Type**: Commits grouped by category (features, fixes, docs, etc.)
- **Commit Details**: Hash, scope, description, author, date
- **Commit Links**: Direct links to commits on GitHub/GitLab/Bitbucket (if remote configured)
- **Contributors List**: All contributors in the analyzed range

### JSON Output
- Structured data with all commit information
- Suitable for programmatic processing
- Includes metadata, summary, statistics, and full commit details

### Plain Text Output
- Simple text format without Markdown formatting
- Easy to copy/paste into other documents
- Good for email or plain text documentation

## Best Practices

1. **Use Conventional Commits**: If your repository follows conventional commit format, the skill will automatically group commits by type (feat, fix, docs, etc.)

2. **Specify Tags Clearly**: Use exact tag names (they are case-sensitive)
   - Good: `v1.2.0`, `release-2024-01`, `v2.0.0-beta`
   - Will fail: `V1.2.0` (if tag is lowercase)

3. **Start Small**: For large repositories, start with 15-25 commits to see the output format, then adjust

4. **Check Remote URL**: For commit links to work, your repository needs a configured git remote (origin)

5. **Combine with Other Skills**: Use the JSON output to feed into other analysis or reporting skills

## Common Use Cases

- **Release Notes**: Generate changelog for version releases
- **Sprint Reviews**: Summarize work completed in a sprint
- **Code Review Prep**: Understand recent changes before review
- **Team Updates**: Share progress with stakeholders
- **Documentation**: Keep CHANGELOG.md up to date
- **Audit Trail**: Track what changed and when

## Troubleshooting

**"Not a valid git repository"**
- Ensure you're in a git repository or provide a valid repo path

**"Tag 'v1.2.0' not found"**
- Verify the tag exists: `git tag -l`
- Check spelling and case-sensitivity

**"No commits found"**
- Check if there are commits after the specified tag
- Verify you're on the correct branch

**"Commit links not working"**
- Ensure git remote is configured: `git remote -v`
- The skill supports GitHub, GitLab, and Bitbucket

## Output Examples

### Markdown Format
```markdown
# Changelog

## Summary

**Total Commits**: 18
**Contributors**: 2
**Conventional Commits**: 100.0%

### Changes by Type
- ✨ **Features**: 7
- 🐛 **Bug Fixes**: 5

## Changes

### ✨ Features (7)
- [`abc123d`](https://github.com/.../abc123d) **auth**: Add user authentication
```

### JSON Format
```json
{
  "summary": {
    "total_commits": 18,
    "by_type": {
      "feat": {"count": 7, "label": "Features"}
    }
  },
  "changes": [...]
}
```
