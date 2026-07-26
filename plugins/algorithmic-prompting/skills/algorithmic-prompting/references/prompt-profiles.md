# Prompt profiles

Choose how much task-local detail each fire-and-forget agent produces.

| Profile | Use when | Detail-result budget |
| --- | --- | --- |
| `lean` | Default; routine, well-bounded work | Guidance up to about 80 words; up to 3 scope and completion items; up to 2 checks |
| `balanced` | Some ambiguity, coordination, or unfamiliar code | Guidance up to about 120 words; up to 5 items per list |
| `thorough` | Security, migrations, compatibility, or high-risk changes | Guidance up to about 200 words; up to 8 items per list, including edge cases and risks |

These are soft budgets, not validation failures. Omit optional fields when they add no execution value.

Set `"prompt_profile": "lean"` on the plan. A task may override it. Natural-language requests are also valid:

- “Use lean prompts.”
- “Use balanced prompts.”
- “Use thorough prompts.”
- “Use lean overall, but thorough for SECURITY-01.”

The renderer always adds the full branch, commit, and handoff contract. Profile depth controls task-specific reasoning and the amount of presentation around the final prompt.
