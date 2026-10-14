# `.agents/`

Agent configuration scoped to **this repository**. The sibling of this file,
[`../AGENTS.md`](../AGENTS.md), holds the rules; this directory holds the
procedures.

| Path | Purpose |
|---|---|
| `skills/run-pipeline/` | Start the stack, run it end to end, debug the real failure modes |
| `skills/add-dbt-model/` | Conventions for adding or changing a dbt model |

## Why this exists

The rules in `AGENTS.md` are short enough to read every time. The procedures are
not — and they contain hard-won detail (a port collision, a TLS interception, an
empty-string cast) that is expensive to rediscover and cheap to write down.

## Scope

Everything here is specific to this repository. Personal preferences, generic
skills and cross-project rules belong in the user's own global configuration,
not in a repository a hiring manager may read.

## Adding a skill

Create `.agents/skills/<kebab-case-name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: kebab-case-name
description: One sentence saying when this applies and what it does.
---
```

The `description` is what an agent matches against, so lead with the trigger:
"Use when ..." beats "This skill is about ...".
