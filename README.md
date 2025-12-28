# Repo Changelog Generator

A Claude Code skill that generates **end-user friendly** release notes and changelogs from git repositories. Analyzes actual code diffs (not just commit messages), consolidates changes, and outputs clean markdown for Slack, documentation, or stakeholder updates.

## Features

- **Diff-Based Analysis**: Reads actual code changes, not just commit messages
- **End-User Focus**: No technical jargon, functions, or variables in output
- **Smart Consolidation**: Eliminates flip-flop changes with no net result
- **Audience Targeting**: Output tailored for end-users, developers, or executives
- **AI-Powered Interpretation**: Uses Claude AI to translate technical changes to plain English
- **Multi-Language Support**: Delphi, xHarbour/Harbour, Lazarus/FPC, and common languages
- **Cross-Platform**: Windows, macOS, and Linux

## Quick Start

### Installation

**For your team (recommended)** - Add to your project:
```bash
mkdir -p .claude/skills
cp -r generated-skills/repo-changelog .claude/skills/
git add .claude/skills/repo-changelog
git commit -m "Add repo-changelog skill"
```

**For personal use** - Add to your Claude config:
```bash
cp -r generated-skills/repo-changelog ~/.claude/skills/
```

### Basic Usage

```bash
cd /path/to/your/repo

# Last 20 commits (quick check)
python ~/.claude/skills/repo-changelog/generate_changelog.py --last 20 --stdout

# Between tags
python ~/.claude/skills/repo-changelog/generate_changelog.py --from-tag v1.0.0 --to-tag v1.1.0

# Since last tag
python ~/.claude/skills/repo-changelog/generate_changelog.py --since-tag
```

## Audience Targeting

Generate output tailored to your audience:

```bash
# End-users (default) - Plain language, no technical terms
--audience end-users

# Developers - Full technical detail, all changes
--audience developers

# Executives - High-level summary with counts
--audience executives
```

**Example output by audience:**

| Audience | Output Style |
|----------|--------------|
| end-users | "Added dark mode toggle in settings" |
| developers | "feat(ui): Add dark mode toggle with CSS variables" |
| executives | "**New Capabilities** (5) **Stability & Fixes** (12)" |

## AI Integration

The tool can use Claude AI to interpret technical diffs into plain English:

```bash
# With AI (requires API key or MAX subscription)
python generate_changelog.py --last 20 --stdout

# Without AI (rule-based interpretation)
python generate_changelog.py --last 20 --stdout --no-ai
```

### Setup AI (First Time)

```bash
python generate_changelog.py --setup-ai
```

This opens your browser to get an API key. Supports:
- Anthropic MAX subscription (priority)
- Anthropic API key
- Environment variable (`ANTHROPIC_API_KEY`)

## Output Categories

Changes are organized into:

| Category | Description |
|----------|-------------|
| **New Features** | Brand new functionality |
| **Enhancements** | Improvements to existing features |
| **Bug Fixes** | Issues that were resolved |
| **Changes** | Modifications to behavior |
| **Breaking Changes** | Changes requiring user action |

## Command Reference

```bash
# Range options (pick one)
--last N              # Last N commits
--from-tag TAG        # Starting tag
--to-tag TAG          # Ending tag (default: HEAD)
--since-tag           # Auto-detect last tag to HEAD

# Output options
--stdout              # Print to console (don't save file)
--output FILE         # Save to specific file
--version VER         # Version string for header

# AI options
--no-ai               # Disable AI interpretation
--setup-ai            # Configure AI credentials

# Audience targeting
--audience TYPE       # end-users | developers | executives
```

## Language Support

Optimized noise filtering for:

- **Delphi** - Filters .dproj, .dfm, Android/iOS resources, project groups
- **xHarbour/Harbour** - Filters .prg, .ch, HB_* constants, compiler flags
- **Lazarus/FPC** - Filters .lpi, .lpk, compiler directives
- **General** - Package locks, IDE configs, build artifacts

## Example Workflow

```bash
# 1. Navigate to your project
cd ~/projects/my-delphi-app

# 2. Generate release notes for stakeholders
python ~/.claude/skills/repo-changelog/generate_changelog.py \
  --from-tag v2.0.0 \
  --to-tag v2.1.0 \
  --audience end-users \
  --stdout

# 3. Generate detailed notes for dev team
python ~/.claude/skills/repo-changelog/generate_changelog.py \
  --from-tag v2.0.0 \
  --to-tag v2.1.0 \
  --audience developers \
  --output RELEASE_NOTES/v2.1.0-dev.md
```

## Output Example

```markdown
# Release Notes - v2.1.0

*Released: 2025-12-28*

## What's New

- Added dark mode toggle in settings
- New export to PDF option in reports

## Improvements

- Improved loading speed when opening large files
- Search now finds partial matches

## Fixes

- Fixed issue where login would fail on slow connections
- Resolved crash when uploading files over 10MB
```

## Team Installation

### Option 1: Project-Level (Recommended)

Add to your repo so everyone gets it:

```bash
# In your team project
mkdir -p .claude/skills
cp -r /path/to/repo-changelog .claude/skills/
git add .claude/skills/
git commit -m "Add repo-changelog skill for team"
git push
```

### Option 2: Shared Repository

Keep this repo as your team's skill library:

```bash
git clone https://github.com/Yona544/AIskils.git
cd AIskils/generated-skills/repo-changelog
python generate_changelog.py --help
```

## File Structure

```
repo-changelog/
├── SKILL.md                 # Skill documentation
├── generate_changelog.py    # Main entry point
├── config.yaml              # Configuration settings
├── git_analyzer.py          # Git operations
├── diff_parser.py           # Diff interpretation
├── change_consolidator.py   # Change merging
├── changelog_formatter.py   # Output formatting
├── ai_interpreter.py        # AI integration
├── audience_profiles.py     # Audience targeting
└── breaking_change_detector.py
```

## Requirements

- Python 3.8+
- Git repository
- (Optional) Anthropic API key for AI features

## License

MIT License - Use freely for your projects.

---

**Questions?** Open an issue or check the [SKILL.md](generated-skills/repo-changelog/SKILL.md) for detailed documentation.
