# Semantic Layer

**Last updated:** 2025-03-10

Business-facing definitions for dimensions, measures, and entities on top of the raw CSV datasets. Use these for consistent reporting and analysis.

## Structure

- **Markdown** (`.md`) — Human-readable documentation: column meanings, grain, and usage.
- **YAML** (`.yml`) — Machine- and tool-friendly model definitions: dimensions, measures, types, and mappings to source columns.

## Models

| Model | Source | Description |
|-------|--------|-------------|
| [super_agents](models/super_agents.md) | `data/super_agents.csv` | All agents ever created by users in ClickUp: identity, status, features, schedules, memory, tools, and workspace assets. |
| [super_agent_run](models/super_agent_run.md) | `data/super_agent_run.csv` | All triggered agent runs; one agent can have multiple runs. **Join to super_agents on `AGENT_ID`.** |
| [super_agent_tools](models/super_agent_tools.md) | `data/super_agent_tools.csv` | Tool-level: one row per tool call. **Hierarchy:** 1 Agent → many Runs; 1 Run → many tool calls. **Join to super_agents on `AGENT_ID`**, **to super_agent_run on `RUN_ID`.** |
| [agent_classifications](models/agent_classifications.md) | `data/agent_classifications.csv` | LLM-derived classification of agents from agent/memory prompt (~10–12 dimensions). One row per agent. **Join to super_agents on `agent_id`.** Classification is stable per agent (does not vary by run or tool). |

## Conventions

- **Dimensions** — Attributes used for filtering, grouping, and slicing (e.g. status, region, date parts).
- **Measures** — Aggregations (count, sum, average) that define KPIs.
- **Grain** — One row per entity; stated at the top of each model doc and in YAML.
