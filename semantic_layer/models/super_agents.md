# Semantic model: super_agents

**Last updated:** 2025-03-10  
**Source:** `data/super_agents.csv`  
**Grain:** One row per agent (as created in ClickUp).  
**Row count (reference):** 156,932

Agents created by users in ClickUp: identifiers, lifecycle, feature flags, schedules, memory, configured tools/knowledge, and workspace/private asset counts.

---

## Identifiers

| Column | Type | Description |
|--------|------|-------------|
| `AGENT_ID` | VARCHAR | Unique agent ID (PK). |
| `AGENT_USER_ID` | BIGINT | User-scoped agent identifier; nullable for some legacy/invalid rows. |
| `WORKSPACE_ID` | BIGINT | Workspace the agent belongs to. |
| `AGENT_CREATOR_USER_ID` | BIGINT | User who created the agent. |
| `AGENT_DELETED_USER_ID` | BIGINT | User who deleted the agent (non-null only when agent is deleted). |

---

## Lifecycle & status

| Column | Type | Description |
|--------|------|-------------|
| `AGENT_CREATED_AT` | TIMESTAMP | When the agent was created. |
| `AGENT_LAST_UPDATED_AT` | TIMESTAMP | Last update time. |
| `AGENT_DELETED_AT` | TIMESTAMP | When the agent was deleted (null if not deleted). |
| `AGENT_VERSION` | VARCHAR | Agent version (e.g. `v1.0`). |
| `AGENT_CLASSIFICATION` | VARCHAR | Classification label (e.g. `Super Agent`). |
| `CURRENT_AGENT_STATUS` | VARCHAR | `active`, `inactive`, or `deleted`. |

---

## Infrastructure

| Column | Type | Description |
|--------|------|-------------|
| `METADATA_SHARD` | VARCHAR | Region/shard (e.g. `prod-us-east-2-2`, `prod-eu-west-1-3`). |
| `AGENT_BUILDER_CONVERSATION_ID` | BIGINT | Builder conversation ID; null when not set. |

---

## Feature flags (booleans)

| Column | Description |
|--------|-------------|
| `IS_DM_ENABLED` | DM (direct message) enabled. |
| `IS_MENTIONS_ENABLED` | Mentions enabled. |
| `IS_ASSIGNEE_ENABLED` | Assignee feature enabled. |
| `HAS_SCHEDULES` | Agent has at least one schedule. |
| `IS_MEMORY_ENABLED` | Memory feature enabled. |
| `IS_EPISODIC_MEMORY_ENABLED` | Episodic memory enabled. |
| `IS_AI_GENERATED_MEMORY_ENABLED` | AI-generated memory enabled. |
| `IS_PREFERENCES_MEMORY_ENABLED` | Preferences memory enabled. |

---

## Schedules

| Column | Type | Description |
|--------|------|-------------|
| `SCHEDULE_IDS` | VARCHAR | JSON-like array of schedule IDs; null when none. |
| `SCHEDULE_COUNT` | BIGINT | Number of schedules (0–1970 in sample). |

---

## Memory

| Column | Type | Description |
|--------|------|-------------|
| `MEMORY_DOC_ID` | VARCHAR | Memory doc ID; null when memory not configured. |
| `MEMORY_PREFERENCES_PAGE_ID` | VARCHAR | Preferences page ID for memory. |

---

## Tools & knowledge

| Column | Type | Description |
|--------|------|-------------|
| `CONFIGURED_AGENT_TOOL_COUNT` | BIGINT | Number of tools configured (0–45). |
| `CONFIGURED_AGENT_TOOL_NAMES` | VARCHAR | JSON-like array of tool names. |
| `CONFIGURED_APP_KNOWLEDGE_COUNT` | BIGINT | Number of app knowledge sources. |
| `CONFIGURED_APP_KNOWLEDGE_NAMES` | VARCHAR | Names of app knowledge sources; often null. |
| `CONNECTED_EXTERNAL_APPS` | VARCHAR | Connected external apps (array/JSON); often null. |
| `WORKSPACE_KNOWLEDGE_ASSET_TYPES` | VARCHAR | Asset types used for workspace knowledge (e.g. docs, tasks, chats). |

---

## Workspace & private assets (counts)

| Column | Description |
|--------|-------------|
| `WORKSPACE_ASSETS_CHAT_COUNT` | Count of chat assets. |
| `WORKSPACE_ASSETS_DOC_COUNT` | Count of doc assets. |
| `WORKSPACE_ASSETS_FOLDER_COUNT` | Count of folder assets. |
| `WORKSPACE_ASSETS_LIST_COUNT` | Count of list assets. |
| `WORKSPACE_ASSETS_SPACE_COUNT` | Count of space assets. |
| `WORKSPACE_ASSETS_TASK_COUNT` | Count of task assets. |
| `PRIVATE_ASSETS_*_COUNT` | Same asset types, private scope (often 0). |

---

## Suggested dimensions (for grouping/filtering)

- `CURRENT_AGENT_STATUS` — active / inactive / deleted  
- `METADATA_SHARD` — region  
- `AGENT_VERSION`, `AGENT_CLASSIFICATION`  
- Time dimensions derived from `AGENT_CREATED_AT`, `AGENT_LAST_UPDATED_AT`, `AGENT_DELETED_AT` (year, quarter, month, week, etc.)  
- Boolean flags (e.g. `HAS_SCHEDULES`, `IS_MEMORY_ENABLED`)

## Suggested measures (aggregations)

- Count of agents (total, by status, by workspace, by creator)  
- Average `CONFIGURED_AGENT_TOOL_COUNT`, `SCHEDULE_COUNT`  
- Sum/count of workspace asset counts  
- Count of deleted agents (`AGENT_DELETED_AT` non-null)
