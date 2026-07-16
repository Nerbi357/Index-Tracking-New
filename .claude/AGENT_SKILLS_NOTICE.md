# Agent Skills — provenance & attribution

The skills, agents, slash commands and reference checklists under `.claude/`
are vendored from an external open-source pack:

- **Source:** https://github.com/addyosmani/agent-skills
- **Author:** Addy Osmani (and contributors)
- **Upstream commit:** `c1974de476a39cb002a3b8e51e6a7e8e57b808c6`
- **License:** MIT — full text in `.claude/AGENT_SKILLS_LICENSE`

## What was vendored

| Location | Content | Count |
|---|---|---|
| `.claude/skills/<name>/SKILL.md` | Lifecycle skills (Define → Plan → Build → Verify → Review → Ship) | 24 |
| `.claude/agents/<name>.md` | Specialist review personas | 4 |
| `.claude/commands/<name>.md` | Slash commands (`/spec`, `/plan`, `/build`, `/test`, `/review`, `/webperf`, `/code-simplify`, `/ship`) | 8 |
| `.claude/references/<name>.md` | Supplementary checklists referenced by the skills | 7 |

## Local modifications (mechanical only)

The upstream pack is designed to be installed as a Claude Code *plugin*. Here it
is vendored as **project** skills instead, so two path-only rewrites were applied:

1. **Commands** — removed the `agent-skills:` plugin namespace prefix, so each
   command invokes the project skill by its bare name
   (e.g. `agent-skills:spec-driven-development` → `spec-driven-development`).
2. **Skills** — repointed reference links from `references/…` to
   `.claude/references/…` so they resolve from the repository root.

No skill/agent instructions or content were otherwise changed.

## Updating

Re-clone upstream, re-copy the four directories, and re-apply the two `sed`
rewrites documented above.

## Removing at the end of the project

Everything in this pack is self-contained under `.claude/`. None of the actual
project code lives here, so the pack can be removed in one step without breaking
anything else:

```bash
rm -rf .claude
```

If by then `.claude/` also holds project-specific Claude Code config you want to
keep (e.g. a hand-written `.claude/settings.json`), delete only the vendored
pieces instead:

```bash
rm -rf .claude/skills .claude/agents .claude/commands .claude/references \
       .claude/AGENT_SKILLS_LICENSE .claude/AGENT_SKILLS_NOTICE.md
```
