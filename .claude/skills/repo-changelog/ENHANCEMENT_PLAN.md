# Repo-Changelog Skill Enhancement Plan

**Created:** 2024-12-25
**Status:** Planning
**Branch:** `claude/continue-previous-work-aDj0u`

---

## Overview

This document outlines 8 enhancements to the repo-changelog skill to make it more powerful, easier to use, and fully integrated into the development workflow.

---

## Task 1: Output File Organization

### Objective
All generated release notes should be saved to a `RELEASE_NOTES/` subfolder with timestamped filenames.

### Requirements
- Create `RELEASE_NOTES/` folder if it doesn't exist
- Filename format: `RELEASE_NOTES_v{version}_{YYYYMMDD}_{HHMMSS}.md`
- If no version specified: `RELEASE_NOTES_{YYYYMMDD}_{HHMMSS}.md`
- Keep the folder organized and prevent overwrites

### Implementation Steps
1. Modify `changelog_formatter.py`:
   - Update `generate_filename()` to include timestamp
   - Add `ensure_output_directory()` method
   - Update `save_to_file()` to use the new directory structure

2. File naming examples:
   ```
   RELEASE_NOTES/
   ├── RELEASE_NOTES_v1.1.0_20241225_143052.md
   ├── RELEASE_NOTES_v1.2.0_20241226_091530.md
   └── RELEASE_NOTES_20241227_160000.md  (no version)
   ```

### Files to Modify
- `changelog_formatter.py`

### Acceptance Criteria
- [ ] `RELEASE_NOTES/` folder created automatically
- [ ] Filenames include date and time stamp
- [ ] No file overwrites (unique timestamps)
- [ ] Works on Windows and Unix paths

---

## Task 2: Add Main Entry Point Script

### Objective
Create a single `generate_changelog.py` script that users can run directly without knowing the internal module structure.

### Requirements
- Command-line interface with clear arguments
- Support all three range types (tag-to-tag, since-tag, last-n-commits)
- Output options (markdown file, Slack format, preview only)
- Cross-platform (Windows PowerShell/CMD and Unix bash)

### Implementation Steps
1. Create `generate_changelog.py` with:
   ```
   Usage: python generate_changelog.py [OPTIONS]

   Options:
     --repo PATH        Repository path (default: current directory)
     --from TAG         Starting tag
     --to TAG           Ending tag (default: HEAD)
     --since TAG        Changes since tag to HEAD
     --last N           Last N commits (default: 50)
     --output FILE      Output file path (default: auto-generated)
     --slack            Format for Slack
     --preview          Preview without saving
     --config FILE      Config file path (default: config.yaml)
     --append FILE      Append to existing CHANGELOG.md
     --help             Show help message
   ```

2. Wire up all modules:
   - GitAnalyzer → DiffParser → ChangeConsolidator → BreakingChangeDetector → ChangelogFormatter

3. Add error handling and user-friendly messages

4. Support both direct execution and import as module

### Files to Create
- `generate_changelog.py`

### Acceptance Criteria
- [ ] Can run with `python generate_changelog.py --from v1.0.0 --to v1.1.0`
- [ ] All options work as documented
- [ ] Clear error messages for invalid inputs
- [ ] Works on Windows (no bash-specific commands)
- [ ] Exit codes: 0 = success, 1 = error

---

## Task 3: Configuration File

### Objective
Move all hardcoded values to a `config.yaml` file for easy customization.

### Requirements
- Default config included with skill
- User can override with custom config
- All customizable options documented

### Configuration Structure
```yaml
# repo-changelog configuration

# Output settings
output:
  directory: "RELEASE_NOTES"
  filename_format: "RELEASE_NOTES_{version}_{datetime}.md"
  datetime_format: "%Y%m%d_%H%M%S"
  include_date_header: true

# Category configuration
categories:
  feature:
    heading: "New Features"
    keywords:
      - "feat"
      - "add"
      - "new"
      - "create"
      - "implement"
    order: 1

  enhancement:
    heading: "Enhancements"
    keywords:
      - "enhance"
      - "improve"
      - "update"
      - "upgrade"
      - "optimize"
    order: 2

  bugfix:
    heading: "Bug Fixes"
    keywords:
      - "fix"
      - "bug"
      - "issue"
      - "resolve"
      - "patch"
    order: 3

  change:
    heading: "Changes"
    keywords:
      - "change"
      - "modify"
      - "refactor"
    order: 4

  breaking:
    heading: "Breaking Changes"
    keywords:
      - "breaking"
      - "migrate"
      - "incompatible"
    order: 0  # First

  other:
    heading: "Other Updates"
    keywords: []
    order: 5

# Filtering
filters:
  # Commit message patterns to ignore
  ignore_patterns:
    - "^Merge "
    - "^WIP"
    - "^fixup!"
    - "^squash!"

  # File patterns to ignore in diff analysis
  ignore_files:
    - "*.lock"
    - "package-lock.json"
    - "yarn.lock"
    - "*.min.js"
    - "*.min.css"

# AI interpretation settings
ai_interpretation:
  enabled: true
  max_diff_size: 5000  # Characters
  prompt_template: |
    Summarize this code change in plain English for an end user.
    Do not mention function names, variables, file paths, or technical details.
    Focus on what the user will experience differently.
    Keep it to one sentence.

# Slack formatting
slack:
  max_items_per_category: 5
  show_overflow_count: true

# Breaking change detection
breaking_changes:
  keywords:
    - "BREAKING"
    - "breaking change"
    - "migration required"
  detect_from_diff: true

# Consolidation settings
consolidation:
  similarity_threshold: 0.7
  remove_flipflops: true
  merge_similar: true
```

### Implementation Steps
1. Create `config.yaml` with all defaults
2. Create `config_loader.py` module:
   - Load YAML config
   - Merge with defaults
   - Validate config structure
3. Update all modules to read from config instead of hardcoded values
4. Add `--config` option to main script

### Files to Create
- `config.yaml`
- `config_loader.py`

### Files to Modify
- `diff_parser.py` (use config for patterns)
- `change_consolidator.py` (use config for thresholds)
- `changelog_formatter.py` (use config for headings)
- `breaking_change_detector.py` (use config for keywords)

### Acceptance Criteria
- [ ] Default config works out of the box
- [ ] User can override any setting
- [ ] Invalid config produces clear error message
- [ ] All previously hardcoded values now configurable

---

## Task 4: AI-Powered Diff Interpretation

### Objective
Use Claude to intelligently interpret code diffs and generate user-friendly descriptions, rather than relying only on pattern matching.

### Requirements
- Send diff content to Claude for interpretation
- Get back plain English descriptions
- Fall back to pattern matching if AI unavailable
- Respect diff size limits (don't send huge diffs)

### Implementation Steps
1. Create `ai_interpreter.py` module:
   ```python
   class AIInterpreter:
       def interpret_diff(self, diff_content: str, context: dict) -> str:
           """
           Use Claude to interpret a code diff.

           Returns a plain English description suitable for end users.
           """
           prompt = f"""
           Analyze this code change and describe what it does in plain English.

           Rules:
           - Write for end users, not developers
           - Do NOT mention function names, variables, or file paths
           - Do NOT use technical jargon
           - Focus on what the user will experience differently
           - One sentence maximum
           - If the change is purely internal with no user impact, say "Internal improvement"

           Context:
           - Commit message: {context.get('commit_message', 'N/A')}
           - Files changed: {context.get('files_changed', [])}

           Diff:
           ```
           {diff_content[:5000]}  # Limit size
           ```

           User-friendly description:
           """
           # This will be called by Claude when the skill is invoked
           return prompt
   ```

2. Integrate with `diff_parser.py`:
   - Try AI interpretation first
   - Fall back to pattern matching if AI returns empty/error
   - Cache interpretations to avoid re-processing

3. Add batching for multiple commits:
   - Group small diffs together
   - Process large diffs individually

### Files to Create
- `ai_interpreter.py`

### Files to Modify
- `diff_parser.py` (integrate AI interpreter)
- `config.yaml` (AI settings)

### Acceptance Criteria
- [ ] Diffs are sent to Claude for interpretation
- [ ] Descriptions are user-friendly (no jargon)
- [ ] Large diffs are truncated appropriately
- [ ] Falls back gracefully if AI unavailable
- [ ] Config option to disable AI interpretation

---

## Task 5: Append to Existing CHANGELOG

### Objective
Support prepending new release notes to an existing CHANGELOG.md file, maintaining a running history.

### Requirements
- Detect existing CHANGELOG.md format
- Prepend new release section at top
- Preserve existing content
- Handle different changelog formats

### Implementation Steps
1. Add to `changelog_formatter.py`:
   ```python
   def append_to_changelog(self, new_content: str, changelog_path: str) -> bool:
       """
       Prepend new release to existing CHANGELOG.md.

       - Reads existing file
       - Inserts new content after header
       - Preserves all existing releases
       """
   ```

2. Detect changelog header pattern:
   ```markdown
   # Changelog

   All notable changes to this project...

   ## [1.1.0] - 2024-12-25   <-- Insert new release here
   ...
   ```

3. Add `--append` option to main script

4. Create backup before modifying existing file

### Files to Modify
- `changelog_formatter.py`
- `generate_changelog.py`

### Acceptance Criteria
- [ ] New releases prepended correctly
- [ ] Existing content preserved
- [ ] Backup created before modification
- [ ] Works with standard CHANGELOG.md format
- [ ] Clear error if file format unrecognized

---

## Task 6: Preview Mode with Interactive Editing

### Objective
Allow users to review, edit, and approve changes before saving the final output.

### Requirements
- Show generated changes in preview
- Allow removing unwanted items
- Allow editing descriptions
- Confirm before saving
- Works in terminal environment

### Preview Interface
```
═══════════════════════════════════════════════════════════
  RELEASE NOTES PREVIEW - v1.1.0
═══════════════════════════════════════════════════════════

## New Features (2 items)
  [1] ✓ Added dark mode toggle in settings
  [2] ✓ New export to PDF option in reports

## Enhancements (2 items)
  [3] ✓ Improved loading speed for large files
  [4] ✓ Search now finds partial matches

## Bug Fixes (2 items)
  [5] ✓ Fixed login issue on slow connections
  [6] ✓ Resolved crash when uploading large files

───────────────────────────────────────────────────────────
Commands:
  [number]  Toggle include/exclude
  e[number] Edit description (e.g., e3)
  a         Add custom item
  p         Show final preview
  s         Save and exit
  q         Quit without saving
───────────────────────────────────────────────────────────
Enter command:
```

### Implementation Steps
1. Create `preview_mode.py` module:
   - Display formatted preview
   - Handle user input commands
   - Track included/excluded items
   - Allow description editing

2. Add to main script:
   - `--preview` flag for preview-only mode
   - `--interactive` flag for full interactive mode

3. Handle terminal compatibility:
   - Work in Windows CMD/PowerShell
   - Work in Unix terminals
   - No special library dependencies

### Files to Create
- `preview_mode.py`

### Files to Modify
- `generate_changelog.py`

### Acceptance Criteria
- [ ] Preview displays all changes by category
- [ ] Can toggle items on/off
- [ ] Can edit descriptions inline
- [ ] Can add custom items
- [ ] Final preview before save
- [ ] Works on Windows terminal

---

## Task 7: Git Tag Hook for Auto-Generation

### Objective
Automatically generate release notes when a git tag is created.

### Requirements
- Trigger on `git tag` command
- Use the new tag as the version
- Find previous tag automatically
- Generate and save release notes
- Optional: commit the generated file

### Hook Configuration
```json
{
  "name": "auto-changelog-on-tag",
  "description": "Automatically generate release notes when a git tag is created",
  "hooks": [
    {
      "event": "PostToolUse",
      "matcher": {
        "tool": "Bash",
        "pattern": "git tag (?:(-a|-m|--annotate|--message)\\s+)?([v]?\\d+\\.\\d+\\.\\d+)"
      },
      "command": "python ~/.claude/skills/repo-changelog/generate_changelog.py --since-last-tag --version $2",
      "timeout": 60000
    }
  ]
}
```

### Implementation Steps
1. Create hook configuration file:
   - `hooks/auto-changelog-hook.json`

2. Create hook installer script:
   - Adds hook to `.claude/settings.json` or `~/.claude/settings.json`
   - Verifies skill is installed

3. Add documentation:
   - How to enable/disable the hook
   - How to customize trigger patterns

4. Handle edge cases:
   - First tag (no previous tag)
   - Tag deletion (don't trigger)
   - Tag on specific commit (not HEAD)

### Files to Create
- `hooks/auto-changelog-hook.json`
- `hooks/install_hook.py`
- `hooks/README.md`

### Acceptance Criteria
- [ ] Hook triggers on `git tag v1.0.0`
- [ ] Hook triggers on `git tag -a v1.0.0 -m "message"`
- [ ] Does NOT trigger on tag deletion
- [ ] Finds previous tag automatically
- [ ] Generates release notes to RELEASE_NOTES folder
- [ ] Can be easily enabled/disabled

---

## Task 8: Test Suite with Sample Repository

### Objective
Create a comprehensive test suite to verify the skill works correctly across different scenarios.

### Requirements
- Unit tests for each module
- Integration tests for full workflow
- Sample git repository with known commits
- Test cases for edge cases
- Cross-platform test compatibility

### Test Structure
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── sample_repo/             # Git repo for testing
│   ├── setup_repo.py        # Script to create sample repo
│   └── expected_outputs/    # Expected results for validation
├── unit/
│   ├── test_git_analyzer.py
│   ├── test_diff_parser.py
│   ├── test_change_consolidator.py
│   ├── test_changelog_formatter.py
│   └── test_breaking_change_detector.py
├── integration/
│   ├── test_full_workflow.py
│   ├── test_cli.py
│   └── test_config_loading.py
└── edge_cases/
    ├── test_large_repos.py
    ├── test_merge_commits.py
    ├── test_no_conventional_commits.py
    └── test_empty_ranges.py
```

### Sample Repository Scenarios
```python
# setup_repo.py creates a git repo with:

# Commit 1: Initial
# Commit 2: feat: Add login feature
# Commit 3: fix: Fix login bug
# Commit 4: Changed login text (flip)
# Commit 5: Changed login text back (flop) -- should be eliminated
# Commit 6: feat!: BREAKING CHANGE - New auth system
# Commit 7: docs: Update readme (should be in "other")
# Tag: v1.0.0
# Commit 8: feat: Add dark mode
# Commit 9: enhance: Improve performance
# Tag: v1.1.0
```

### Implementation Steps
1. Create test directory structure

2. Create `setup_repo.py`:
   - Generates a git repository with predefined commits
   - Creates tags at specific points
   - Includes various commit types and edge cases

3. Write unit tests for each module:
   - Test individual functions
   - Mock git commands where needed
   - Test error handling

4. Write integration tests:
   - Test full workflow from git repo to markdown output
   - Verify output matches expected results
   - Test CLI commands

5. Write edge case tests:
   - Empty commit range
   - No conventional commits
   - Very large diffs
   - Merge commits
   - Flip-flop detection

6. Add test runner configuration:
   - `pytest.ini` or `pyproject.toml`
   - Coverage reporting
   - Windows/Unix compatibility

### Files to Create
- `tests/` directory with all test files
- `tests/sample_repo/setup_repo.py`
- `tests/sample_repo/expected_outputs/*.md`
- `pytest.ini`
- `requirements-test.txt`

### Acceptance Criteria
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Sample repo creates consistently
- [ ] Edge cases handled correctly
- [ ] Tests run on Windows and Unix
- [ ] Coverage > 80%
- [ ] Can run with `pytest tests/`

---

## Implementation Order

Recommended sequence based on dependencies:

```
Phase 1: Foundation
├── Task 3: Config file (other tasks depend on this)
└── Task 1: Output file organization

Phase 2: Core Features
├── Task 2: Main entry point
└── Task 4: AI interpretation

Phase 3: User Experience
├── Task 5: Append to changelog
└── Task 6: Preview mode

Phase 4: Automation & Quality
├── Task 7: Git tag hook
└── Task 8: Test suite
```

---

## Estimated Effort

| Task | Estimated Time | Complexity |
|------|----------------|------------|
| Task 1: Output organization | 30 min | Low |
| Task 2: Main entry point | 1 hour | Medium |
| Task 3: Config file | 1 hour | Medium |
| Task 4: AI interpretation | 1 hour | Medium |
| Task 5: Append changelog | 45 min | Medium |
| Task 6: Preview mode | 1.5 hours | High |
| Task 7: Git tag hook | 45 min | Medium |
| Task 8: Test suite | 2 hours | High |
| **Total** | **~9 hours** | |

---

## Success Metrics

After all tasks complete:

1. **Ease of Use**: Single command generates complete release notes
2. **Quality**: AI-powered descriptions are user-friendly
3. **Flexibility**: All settings customizable via config
4. **Integration**: Auto-generates on git tag
5. **Reliability**: 80%+ test coverage
6. **Organization**: All outputs in RELEASE_NOTES folder with timestamps

---

## Next Steps

1. Review and approve this plan
2. Start with Phase 1 (Tasks 3 and 1)
3. Progress through phases sequentially
4. Test each task before moving to next

---

*Document created for AIskils/repo-changelog skill enhancement*
