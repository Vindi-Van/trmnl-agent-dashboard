---
trigger: always_on
---

> **STRICTNESS LEVEL: MUST** — All rules are mandatory.

---

## 1. Task-Based Development

- **MUST** break work into numbered tasks and complete one at a time
- **MUST** verify each task before starting the next
- **MUST** maintain a running Task Tracker

**Task Format:**
```markdown
### Task N: [Task Name]
- **Objective**: What this task achieves
- **Plan**: Approach and files to touch
- **Changes**: Diffs/snippets
- **Verification**: How verified and result
- **Docs**: Which docs updated
- **Status**: Pending → In Progress → Complete
```

**Task Tracker:**
```markdown
## Task Tracker
- [ ] Task 1: ...
- [x] Task 2: ... (mark only after verification)
```

---

## 2. Design Review

**MUST** share a design proposal and wait for approval before implementing:
- Large architectural changes
- Public API changes
- Data model changes
- Major refactors

**Design Proposal Format:**
```markdown
## Design Proposal: [Title]
- **Summary & Motivation**: Why needed
- **Current vs. Proposed**: What changes
- **Affected Modules**: Components impacted
- **Migration Plan**: How to transition
- **Alternatives**: Other approaches considered
- **Rollback Plan**: How to revert if needed
```

---

## 3. Documentation Structure

### Root Level
| File | Purpose |
|------|---------|
| `README.md` | Setup, env vars, commands, troubleshooting |
| `CONTEXT.md` | Architecture, data flows, decisions, rationale |
| `CHANGELOG.md` | Keep a Changelog format + SemVer |

### Each Subdirectory
| File | Purpose |
|------|---------|
| `content.md` | Purpose, key components, owned contracts |
| `readme.md` | How to run/test, entry points |
| `CONTEXT.md` | Module context and change log |

### CONTEXT.md Maintenance
- **MUST** update change log after every significant change
- **MUST** maintain CONTEXT.md in each subdirectory
- **MUST** add date, summary, and agent identifier

---

## 4. Git Rules

**Commit Format:**
```
<type>: <short description>

Types: feat, fix, refactor, test, docs, chore
```

- **MUST** write descriptive commit messages
- **MUST** keep commits atomic
- **MUST** run tests before committing

**CHANGELOG Format:**
- Use Keep a Changelog + SemVer
- Categories: Added, Changed, Fixed, Removed
- Include brief rationale

---

## 5. Final Deliverables

**MUST** include in each reply:
- Summary of changes and motivation
- Updated Task Tracker
- Diffs/snippets for files changed
- Build/test/lint commands and outcomes
- Migrations/manual steps
- Docs and changelog updates
- Known limitations and follow-ups

---

## 6. Verification Checklist

```markdown
## Final Verification
- [ ] All tasks completed and verified
- [ ] Build passes locally
- [ ] All tests pass
- [ ] Lint/format clean
- [ ] Docs updated (README, CONTEXT, content)
- [ ] CHANGELOG updated if user-facing
- [ ] Manual sanity check done
- [ ] Open questions documented