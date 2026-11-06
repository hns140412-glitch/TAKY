# TAKY 2.0 — Shared Skills portability (candidate)

This is a reversible **local Skills link restorer**, not a replacement for canonical TAKY rules and not evidence that any agent has executed a Skill. Supports Antigravity's `.agents/skills/<name>/SKILL.md`, Claude Code's `.claude/skills/`, and Git-sourced skill ownership.

## Prerequisite on another PC
Keep the TAKY source and TAKY 2.0 worktree in either of the verified layouts; do not move or duplicate the canonical TAKY repository:

```text
<parent>/
  TAKY/.claude/skills/<skill>/SKILL.md       # approved Git-tracked source
  TAKY-2.0-ORCH/.agents/skills/              # sibling layout, supported
  TAKY-2.0-ORCH/.claude/skills/
```

Current PC uses the nested Git worktree layout:

```text
D:/Git PWA/TAKY/.claude/skills/<skill>/SKILL.md
D:/Git PWA/TAKY/.local/TAKY-2.0-ORCH/.agents/skills/
D:/Git PWA/TAKY/.local/TAKY-2.0-ORCH/.claude/skills/
```

Both approved links and physical consumer directories with an exact recursive path/file/hash match are accepted by `check`; links are created only for missing destinations.

Install Python 3.10+, Git, and the native Claude/Codex extensions separately. The script creates links but does **not** install models, authenticate accounts, approve MCP servers, or launch any AI.

## Use

From `TAKY-2.0-ORCH`, check in **read-only mode**:

```powershell
python -m TAKY2.skill_links check
```

If the output says `NEEDS_RESTORE`, and all existing files have been preserved, explicitly restore **missing links only**:

```powershell
python -m TAKY2.skill_links restore
python -m TAKY2.skill_links check
```

`restore` never replaces an existing real directory or an unexpected link. Windows uses a directory junction, requiring no paid services. Linux/macOS uses a directory symlink. `SKILL_LINKS_MANIFEST.json` pins SHA-256 of 11 TAKY source `SKILL.md` files; if a canonical source changes, `check` fails until the change is reviewed and a new manifest is approved.

Regression (on the current PC; temporary fixture only):

```powershell
python TAKY2/test_skill_links.py
```

The fixture covers sibling/nested paths, 22 links and 22 hash-verified materialized directories, idempotence, source hash drift, tamper/extra-file conflicts and non-mutation. It does not modify real consumer skill folders.

## Authority and limitations

- `TAKY/MASTER/AI_COLLABORATION_PROTOCOL.md`: ChatGPT orchestrator, Claude Code primary code executor, Codex need-based independent verifier or usage-justified fallback executor.
- The conflicting legacy `savey-ai-economy` skill is **not** silently included.
- `SKILL.md` present / valid junction / hash-verified materialized directory **≠** skill discovered and invoked at agent runtime.
- Nothing here proves native Antigravity Claude/Codex panel control, provider receipt, context ACK, paid API availability, Git push/merge or deployment.
- All files created in `TAKY-2.0-ORCH` in this candidate remain **uncommitted until an authorized Git checkpoint**. File presence in the current dirty worktree is not proof a new clone has them.
