# Testing Notes: Repo-Changelog Skill

**Date**: December 26, 2025
**Tested on**: Express.js (50 commits), Flask (50 commits)
**Skill Version**: Phase 5 -> Phase 6 (with noise reduction fixes)

---

## Executive Summary

Testing the changelog generator against two popular open-source repositories revealed **significant issues** with noise filtering, pattern matching, and categorization. The tool produces unusable output when lock files or dependency updates are present.

### Initial Results (Before Fixes)

| Repository | Commits | Changes Found | Usable? |
|------------|---------|---------------|---------|
| Express.js | 50 | 11 | Partially - descriptions are poor |
| Flask | 38* | 1,271 | No - flooded with hash strings |

*Only 38 commits returned due to shallow clone depth

### After Fixes (Phase 6 Quick Wins)

| Repository | Commits | Changes Found | Improvement |
|------------|---------|---------------|-------------|
| Express.js | 50 | 11 | Security category now shows! |
| Flask | 38* | 26 | **98% noise reduction** (1,271 -> 26) |

**Fixes implemented:**
- Lock file ignore patterns (package-lock.json, yarn.lock, poetry.lock, etc.)
- SHA256/SHA512 hash exclusion patterns
- Security category (`sec:` prefix recognition)
- Dependency category (`build(deps):` prefix recognition)

---

## Critical Issues Found

### 1. Lock File Content Pollutes Output (CRITICAL)

**Problem**: SHA256 hashes from dependency lock files (requirements.txt, poetry.lock, yarn.lock, package-lock.json) are being detected as "text changes".

**Example output**:
```
- Updated text: "sha256:82a8d0b81e318cc5ce71a5f1f8b5c4e63619620b631..."
- Updated text: "sha256:0287e96f4d26d4149305414d4e3bc32f0dcd0862365..."
[...hundreds more...]
```

**Root Cause**: The `USER_FACING_PATTERNS` regex in `diff_parser.py` matches any quoted string 10-100 characters:
```python
(r'["\']([^"\']{10,100})["\']', 'text_change')
```

**Suggested Fix**:
1. Add file-type ignore list for lock files
2. Add pattern to exclude SHA/hash-like strings
3. Check if parent file is a known lock file before extracting patterns

**Files to modify**: `diff_parser.py`, `config.yaml`

---

### 2. Dependency Bump Commits Not Handled (HIGH)

**Problem**: `build(deps):` commits generate noise instead of being summarized or excluded.

**Example commits**:
```
build(deps): bump actions/checkout from 5.0.0 to 6.0.0
build(deps): bump github/codeql-action from 4.31.2 to 4.31.6
build(deps): bump coverallsapp/github-action from 2.3.6 to 2.3.7
```

**Current behavior**: Each generates individual entries with poor descriptions.

**Suggested Fix**:
1. Detect `build(deps):` prefix pattern
2. Group all dependency updates into single entry: "Updated X dependencies"
3. Add config option: `exclude_dependency_bumps: true`

**Files to modify**: `diff_parser.py`, `change_consolidator.py`, `config.yaml`

---

### 3. Security Prefix Not Recognized (HIGH)

**Problem**: `sec:` conventional commit prefix is not recognized.

**Example**: `sec: security patch for CVE-2024-51999` was not properly categorized.

**Root Cause**: `_categorize_from_message()` in `diff_parser.py` doesn't include `sec:` pattern.

**Suggested Fix**:
```python
if re.match(r'^sec(\(.+?\))?!?:', message_lower):
    return 'security'  # New category
```

**Files to modify**: `diff_parser.py`, `generate_changelog.py` (add security category)

---

### 4. No Security Category (MEDIUM)

**Problem**: `security` is not a valid category filter.

```bash
$ python generate_changelog.py --category security
error: invalid choice: 'security' (choose from 'feature', 'enhancement', 'bugfix', 'change', 'breaking', 'other')
```

**Suggested Fix**: Add `security` as first-class category with:
- High visibility in output (before features)
- CVE reference extraction
- Special emoji/formatting

**Files to modify**: `config.yaml`, `generate_changelog.py`, `changelog_formatter.py`

---

### 5. Poor Description Generation (HIGH)

**Problem**: Many entries show raw code snippets instead of meaningful descriptions.

**Example outputs**:
```
- Updated text: "/?hasOwnProperty=yee"
- Updated text: "should persist store"
- Updated text: "eslint . --fix"
```

**Root Cause**: Pattern matching extracts literal string values from diffs without understanding context.

**Suggested Fix**:
1. Increase confidence threshold for `diff_analysis` source
2. Prefer `commit_message` source over raw diff patterns
3. Add semantic validation: skip entries that look like code/tests/configs
4. Use AI interpretation more aggressively (when available)

**Files to modify**: `diff_parser.py`, `change_consolidator.py`

---

### 6. Revert Commits Not Handled Properly (MEDIUM)

**Problem**: Reverts are categorized as "other" with poor descriptions.

**Example**:
```
Input: Revert "sec: security patch for CVE-2024-51999"
Output: - Revert "sec: security patch for -51999"
```

Note: The CVE number got truncated!

**Suggested Fix**:
1. Detect `Revert "..."` pattern
2. Extract original change and mark as "Reverted: [original description]"
3. Consider linking revert to original change

**Files to modify**: `diff_parser.py`

---

### 7. Version/Release Commits Not Special-Cased (LOW)

**Problem**: Version bump commits like `5.2.1` or `Release: 5.2.0` generate noise.

**Suggested Fix**:
1. Detect version-only commits (just version number in subject)
2. Detect `Release:` prefix
3. Either exclude or group into "Version X.Y.Z released"

**Files to modify**: `diff_parser.py`, `config.yaml`

---

## What Worked Well

1. **Conventional commit prefix detection** - `feat:`, `fix:`, `docs:` are properly recognized
2. **Basic categorization** - Features, bugfixes, and changes are generally correct
3. **Semantic grouping** - The "(multiple improvements)" suffix shows consolidation is working
4. **File output** - Saves to RELEASE_NOTES directory correctly
5. **CLI interface** - Arguments work as expected
6. **Test infrastructure** - 42 unit tests pass

---

## What I Struggled With

### 1. Pattern Matching is Too Greedy

The regex patterns for detecting "user-facing changes" are too broad. Any quoted string gets picked up, including:
- Test assertions
- Error messages
- Configuration values
- Hash strings

**Lesson**: Need negative patterns (what NOT to match) as well as positive patterns.

### 2. No File-Type Awareness for Diffs

The diff parser treats all files equally. A change in `package-lock.json` is processed the same as a change in `src/app.js`.

**Lesson**: Should have file-type-specific processing rules.

### 3. Commit Message Quality Varies Wildly

Real-world commits have:
- Emoji in messages (handled okay)
- Multiple conventional prefixes: `build(deps):`
- Non-standard prefixes: `sec:`
- No prefix at all
- Just version numbers

**Lesson**: Need more robust message parsing with fallbacks.

### 4. Scale Issues

1,271 changes from 38 commits is a 33:1 ratio. Even with consolidation, this produces unusable output.

**Lesson**: Need aggressive pre-filtering before consolidation.

---

## Improvement Priorities

### Phase 6: Noise Reduction (Recommended Next)

| Task | Priority | Complexity | Impact |
|------|----------|------------|--------|
| Add lock file ignore list | P0 | Low | Very High |
| Add hash/SHA pattern exclusion | P0 | Low | Very High |
| Group dependency bumps | P1 | Medium | High |
| Add security category | P1 | Medium | High |
| Improve revert handling | P2 | Low | Medium |
| Add version commit detection | P3 | Low | Low |

### Implementation Order

1. **Quick Wins** (can be done immediately):
   - Add file extensions to ignore: `.lock`, `*-lock.json`, `requirements*.txt`
   - Add regex to exclude SHA256 patterns: `sha256:[a-f0-9]{64}`
   - Recognize `sec:` prefix

2. **Medium Effort**:
   - Add security category
   - Group `build(deps):` commits
   - Improve revert detection

3. **Larger Effort**:
   - File-type-specific diff processing
   - AI interpretation for ambiguous changes
   - Confidence scoring improvements

---

## Test Commands Used

```bash
# Clone test repositories
git clone --depth 100 https://github.com/expressjs/express.git /tmp/express-test
git clone --depth 100 https://github.com/pallets/flask.git /tmp/flask-test

# Run changelog generator
cd /tmp/express-test
python3 /path/to/generate_changelog.py --last 50 --stdout

cd /tmp/flask-test
python3 /path/to/generate_changelog.py --last 50 --stdout

# With verbose mode
python3 /path/to/generate_changelog.py --last 50 --verbose
```

---

## Conclusion

The repo-changelog skill has a solid foundation but needs **noise reduction improvements** before being useful on real-world repositories with:
- Lock files
- Dependency management
- CI/CD changes
- Security patches

The core architecture (diff parsing, consolidation, semantic grouping, formatting) is sound. The issues are primarily in the **input filtering** and **pattern matching** layers.

**Recommended next step**: Implement Phase 6 focusing on noise reduction, starting with lock file exclusion and hash pattern filtering.

---

---

## Fixes Applied During This Session

Based on testing, the following fixes were implemented:

### 1. Lock File Ignore Patterns (diff_parser.py)

Added `IGNORE_FILES` list to skip processing of:
- `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
- `Pipfile.lock`, `poetry.lock`, `Gemfile.lock`
- `composer.lock`, `Cargo.lock`, `go.sum`
- `requirements.txt` (often contains hashes)
- All `*.lock` files

### 2. Hash/Checksum Exclusion (diff_parser.py)

Added `NOISE_PATTERNS` to filter out:
- `sha256:[a-f0-9]{64}` patterns
- `sha512:[a-f0-9]{128}` patterns
- `sha1:[a-f0-9]{40}` patterns
- Bare 64-character hex strings
- npm integrity and resolved URL patterns

### 3. Security Category (diff_parser.py, config.yaml)

Added recognition for:
- `sec:` and `security:` conventional commit prefixes
- CVE references
- Security-related keywords (vulnerability, exploit, XSS, etc.)
- New "Security Updates" section in output (order: 1, after Breaking Changes)

### 4. Dependency Category (diff_parser.py, config.yaml)

Added recognition for:
- `build(deps):` and `build(deps-dev):` prefixes
- Keywords: bump, deps, dependency
- New "Dependency Updates" section in output (order: 6)

### Results

- **Flask repo**: 98% noise reduction (1,271 -> 26 changes)
- **Express.js repo**: Security category now properly appears
- All 42 unit tests continue to pass

---

## Round 2: Additional Repository Testing

### Repositories Tested

| Repository | Language | Commit Style |
|------------|----------|--------------|
| axios | JavaScript/TypeScript | Conventional commits (feat:, fix:, chore:) |
| requests | Python | Merge commits, less conventional |

### Initial Results (After Phase 6)

| Repository | Commits | Changes Found | Issues |
|------------|---------|---------------|--------|
| axios | 50 | 87 | SHA512 hashes, test assertions, sponsor spam |
| requests | 37 | 37 | GitHub Actions refs, CI commands, test data |

### After Phase 7 Improvements

| Repository | Before | After | Improvement |
|------------|--------|-------|-------------|
| axios | 87 | 35 | **60% reduction** |
| requests | 37 | 20 | **46% reduction** |

### New Issues Discovered

1. **Test file content leaking** - Test assertions like "should convert...", "Should have thrown..."
2. **GitHub Actions references** - `actions/checkout@v4`, `uses: org/repo@ref`
3. **CI/CD step names** - "Set up Python", "Install dependencies", "Build dists"
4. **SHA512 hashes** - Base64 encoded hashes in package-lock.json
5. **Sponsor/promotional content** - Marketing text in sponsor blocks
6. **node_modules paths** - Internal dependency paths
7. **Python classifiers** - "Programming Language :: Python :: 3.14"
8. **Test data** - `machine example.com login aaaa password bbbb\n`
9. **CSS classes** - "btn-primary", "fas-icon"
10. **Internal error messages** - "Invalid file path", "Error while reading"

### Fixes Applied (Phase 7)

#### 1. Expanded IGNORE_FILES (diff_parser.py)

Added test file patterns:
- `test_*.py`, `*_test.py`, `*.test.js`, `*.spec.ts`
- `**/test/**`, `**/tests/**`, `**/__tests__/**`

Added CI/CD files:
- `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`

Added generated directories:
- `**/node_modules/**`, `**/vendor/**`, `**/dist/**`

#### 2. Expanded NOISE_PATTERNS (diff_parser.py)

GitHub Actions patterns:
- `actions/[\w-]+@v?\d+` - version refs
- `::set-output\s+name=` - workflow commands
- `uses:\s+[\w-]+/[\w-]+@` - action references

CI/CD framework patterns:
- `slsa-framework/`, `pypa/gh-action-`, `step-security/`

Test patterns:
- `^should\s+\w+` - test assertions
- `assert\w*\(`, `expect\(`, `describe\(` - test frameworks

#### 3. Enhanced _looks_like_code() (diff_parser.py)

Added detection for:
- CSS class patterns (`btn-primary`)
- CI step names (`set up`, `checkout`, `install`, `build`)
- Test data patterns (login/password with newlines)
- Python classifiers
- Error message patterns
- Spam/promotional keywords

### Results Summary

| Phase | Repository | Changes | Cumulative Reduction |
|-------|------------|---------|---------------------|
| Phase 6 | Flask | 1,271 → 26 | 98% |
| Phase 6 | Express.js | 11 → 11 | Security category added |
| Phase 7 | axios | 87 → 35 | 60% |
| Phase 7 | requests | 37 → 20 | 46% |

### Remaining Edge Cases

Some content is genuinely ambiguous and hard to filter automatically:
1. User-facing error messages (legitimate but look like internal errors)
2. Sponsor block promotional content
3. Package names in dependencies section
4. CSS classes vs user-facing labels

These would require AI interpretation or manual review to filter correctly.

---

*Document updated: December 26, 2025*
*Testing rounds: 2 (Phase 6 + Phase 7)*
