# Semantic model: super_agent_tools

**Last updated:** 2025-03-10  
**Source:** `data/super_agent_tools.csv`  
**Grain:** One row per tool call (tool-level).  
**Row count (reference):** 59,651,247

**Hierarchy:**
- 1 **Agent** → many **Runs** (super_agent_run)
- 1 **Run** → many **Tool calls** (super_agent_tools)

**Joins:**
- To **super_agents:** `AGENT_ID` → `super_agents.AGENT_ID`
- To **super_agent_run:** `RUN_ID` → `super_agent_run.RUN_ID`

Each run of an agent can invoke multiple tools; this table has one row per tool invocation (LLM call or ClickUp tool call).

---

## Relationship

- **super_agent_tools** is at the lowest grain: individual tool/LLM calls within a run.
- **super_agent_run** has one row per run; join on `RUN_ID` to get run-level context.
- **super_agents** has one row per agent; join on `AGENT_ID` to get agent-level attributes.

---

## Identifiers

| Column | Type | Description |
|--------|------|-------------|
| `AGENT_TOOL_ID` | VARCHAR | Unique tool-call ID (PK). |
| `RUN_ID` | VARCHAR | Run this call belongs to (FK to super_agent_run.RUN_ID). |
| `AGENT_ID` | VARCHAR | Agent (FK to super_agents.AGENT_ID). |
| `WORKSPACE_ID` | BIGINT | Workspace. |

---

## Timing

| Column | Type | Description |
|--------|------|-------------|
| `RUN_STARTED_AT` | TIMESTAMP | When the parent run started. |
| `CALL_STARTED_AT` | VARCHAR | When this tool call started (cast to timestamp if needed). |
| `TOTAL_DURATION_MS` | VARCHAR | Duration of this call in ms (cast to numeric for analysis). |

---

## Call type & identity

| Column | Type | Description |
|--------|------|-------------|
| `CALL_TYPE` | VARCHAR | e.g. `llm_call`, `clickup_tool`. |
| `CALL_SUBTYPE` | VARCHAR | e.g. `external_llm_call`, `clickup_tool_call`, `clickup_tool_external_llm_call`. |
| `CALL_NAME` | VARCHAR | Name of the call (e.g. prompt/tool name). |
| `VENDOR` | VARCHAR | e.g. `openai`, `clickup`, `google`, or `\N`. |
| `INVOCATION_ORDER` | BIGINT | Order of this call within the run. |
| `CLICKUP_TOOL_INVOCATION_ORDER` | VARCHAR | Order among ClickUp tool calls (when applicable). |
| `CLICKUP_TOOL_TYPE` | VARCHAR | Type of ClickUp tool (when applicable). |

---

## Success & retries

| Column | Type | Description |
|--------|------|-------------|
| `IS_SUCCESS` | VARCHAR | Whether the call succeeded. |
| `IS_CALL_BILLED_TO_CUSTOMER` | BOOLEAN | Whether this call was billed to the customer. |
| `CALL_ATTEMPT_NUMBER` | BIGINT | Attempt number for this call. |
| `IS_FIRST_CALL` | BOOLEAN | Whether this was the first call in the attempt. |
| `IS_CLICKUP_TOOL_CALL_RETRY` | VARCHAR | Whether this is a ClickUp tool retry. |
| `IS_CLICKUP_TOOL_CALL_RETRY_SUCCESSFUL` | VARCHAR | Whether the retry succeeded. |
| `CLICKUP_TOOL_RETRY_CHAIN_POSITION` | VARCHAR | Position in retry chain. |
| `CLICKUP_TOOL_RETRY_CHAIN_LENGTH` | VARCHAR | Length of retry chain. |
| `IS_CLICKUP_TOOL_RETRY_CHAIN_SUCCESSFUL` | VARCHAR | Whether the full retry chain succeeded. |

---

## LLM / token usage

| Column | Type | Description |
|--------|------|-------------|
| `CLICKUP_TOOL_LLM_CALL_COUNT` | VARCHAR | LLM calls for this ClickUp tool (cast if needed). |
| `HAS_NESTED_EXTERNAL_LLM_CALLS` | VARCHAR | Whether there are nested external LLM calls. |
| `NUM_TOKENS_FULL` | VARCHAR | Token count (full); cast to numeric for analysis. |
| `NUM_TOKENS_COMPACT` | VARCHAR | Token count (compact). |
| `NUM_TOKENS_SQUASHED` | VARCHAR | Token count (squashed). |
| `INPUT_TOKEN_COUNT` | VARCHAR | Input tokens (cast to numeric). |
| `OUTPUT_TOKEN_COUNT` | VARCHAR | Output tokens (cast to numeric). |
| `INPUT_CACHED_TOKEN_COUNT` | VARCHAR | Cached input tokens. |
| `TIME_TO_FIRST_TOKEN_MS` | VARCHAR | Time to first token in ms. |

---

## Model & cost

| Column | Type | Description |
|--------|------|-------------|
| `MODEL` | VARCHAR | Model used (e.g. `gpt-4.1-mini-2025-04-14`). |
| `COST` | VARCHAR | Cost of this call (cast to decimal for analysis). |
| `SERVICE_TIER` | VARCHAR | Service tier (e.g. `default`). |

---

## Parent call (nested calls)

| Column | Type | Description |
|--------|------|-------------|
| `PARENT_TOOL_NAME` | VARCHAR | Name of parent tool (when this is a nested call). |
| `PARENT_AGENT_TOOL_ID` | VARCHAR | AGENT_TOOL_ID of the parent call. |

*Note: Many numeric columns (duration, tokens, cost) are stored as VARCHAR in the CSV; cast to numeric for aggregations.*

---

## Suggested dimensions (for grouping/filtering)

- `AGENT_ID`, `RUN_ID` — join to super_agents and super_agent_run.
- `CALL_TYPE` — llm_call vs clickup_tool.
- `CALL_SUBTYPE` — external_llm_call, clickup_tool_call, clickup_tool_external_llm_call.
- `VENDOR` — openai, clickup, google.
- `MODEL` — model name.
- Time from `RUN_STARTED_AT` or `CALL_STARTED_AT` (year, month, day, hour).
- `WORKSPACE_ID`.

## Suggested measures (aggregations)

- **Tool call count** — total calls, calls per run, calls per agent, by CALL_TYPE / VENDOR.
- **Distinct runs/agents** — count distinct RUN_ID or AGENT_ID (from tools).
- **Duration** — sum/avg of TOTAL_DURATION_MS (cast to numeric).
- **Cost** — sum of COST (cast to decimal).
- **Tokens** — sum of INPUT_TOKEN_COUNT, OUTPUT_TOKEN_COUNT (cast to numeric).
- **Success rate** — count where IS_SUCCESS = true / total.
