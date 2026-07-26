# Routing plan schema

Persist only enough information to route deep investigation and create stable placeholders.

```json
{
  "goal": "Add a language feature",
  "goal_slug": "language-feature",
  "plan_stage": "routing",
  "topology_status": "provisional",
  "prompt_profile": "lean",
  "lanes": [
    {
      "id": "PARSER",
      "scope": "Syntax ownership",
      "paths": ["compiler/parser/**"]
    },
    {
      "id": "RUNTIME",
      "scope": "Runtime behavior",
      "paths": ["runtime/**"]
    }
  ],
  "tasks": [
    {
      "id": "PARSER-01",
      "lane": "PARSER",
      "title": "Route syntax work",
      "status": "planned"
    },
    {
      "id": "RUNTIME-01",
      "lane": "RUNTIME",
      "title": "Route runtime work",
      "status": "planned"
    }
  ],
  "dependencies": [],
  "collisions": []
}
```

## Routing rules

- Derive uppercase lane names and ownership paths from the intentionally structured repository layout.
- Use one task shell per independently investigated area unless the layout makes a second unit obvious.
- Add a dependency only when the request or structured layout explicitly establishes the prerequisite.
- Keep uncertain dependencies and collisions out of the shared graph; detail subagents propose them later.
- Do not add modules, implementation files, acceptance criteria, validation, completion gates, branches, or prompt guidance during routing.
- Use `routing` and `provisional` until detail evidence is reviewed.

The detail landing result supplies scope, files, completion criteria, checks, risks, and task-specific guidance. Legacy detailed plans remain accepted with `plan_stage` omitted or set to `detailed`.
