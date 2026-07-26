# Map-first scan

Build the initial topology from high-information repository artifacts instead of reading implementation broadly.

## Evidence order

1. Repository instructions such as `AGENTS.md` and contribution guidance
2. Architecture maps such as `DESIGN.md`, `ARCHITECTURE.md`, and ADR indexes
3. Convention and testing guides
4. Contracts such as `schema.sql`, OpenAPI, GraphQL, protobuf, and event schemas
5. Top-level file and module structure
6. Build manifests, workspace configuration, and task runners
7. One implementation anchor per lane only when ownership remains unclear

Treat these names as examples. Discover equivalent project-specific files rather than requiring exact filenames.

## Stop rule

Stop the initial scan when every proposed lane has a plausible ownership boundary, input, output, validation method, and obvious prerequisites. Do not read implementation broadly to remove task-local uncertainty.

Mark the initial topology `provisional`. Detail subagents verify the map against actual code, deepen task comprehension, and record proposed dependency or collision corrections without mutating the shared graph.

If map files conflict or appear stale, record the uncertainty and inspect one relevant implementation anchor. Escalate to a deeper synchronous scan only when the contradiction prevents a safe lane boundary or prerequisite decision.
