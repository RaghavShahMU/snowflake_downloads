# Semantic model: agent_classifications

**Last updated:** 2025-03-10  
**Source:** `data/agent_classifications.csv`  
**Grain:** One row per agent (classified from agent/memory prompt; ~114.8K agents).  
**Row count (reference):** 114,802

**Join:** To **super_agents** on `agent_id` → `super_agents.AGENT_ID`.

This table was created outside the data warehouse: agent IDs and agent prompt (memory/agent prompt, not user prompt) were extracted, and the prompt was classified using LLMs into 10–12 categorical dimensions. The prompt is stable per agent and does not change per run or per tool call.

---

## Relationship

- **agent_classifications** has one row per classified agent.
- Join to **super_agents** on `agent_id` to attach classification dimensions to agent metadata (status, features, workspace, etc.).
- Classification is at **agent level only** (no join to run or tool tables).

---

## Identifiers

| Column | Type | Description |
|--------|------|-------------|
| `agent_id` | VARCHAR | Agent ID (PK, FK to super_agents.AGENT_ID). |

---

## Classification dimensions (LLM-derived)

Each dimension below is a categorical value derived from the agent/memory prompt. Options and descriptions follow the classification schema used for the LLM.

---

### 1. `team_orientation`

**Description:** Whether the agent is framed for an individual, small team, or larger team.

| Option | Description |
|--------|-------------|
| `individual` | Agent is oriented to a single user. |
| `small_team` | Agent is oriented to a small team. |
| `larger_team` | Agent is oriented to a larger team. |
| `unknown` | Could not be determined. |

---

### 2. `domain_knowledge_depth`

**Dimension description:** How much specialized field expertise is baked into the prompt (generic vs. craft knowledge vs. formal processes).

| Option | Description |
|--------|-------------|
| `none` | Generic instructions only — no domain references. |
| `light` | Domain is the setting, not the skill — swap names, logic unchanged. |
| `moderate` | Domain craft knowledge essential — techniques, frameworks, quality criteria. |
| `deep` | Formal procedural knowledge — lifecycle stages, compliance gates. |
| `unknown` | Could not be determined. |

---

### 3. `operational_scope`

**Dimension description:** How complex the agent's workflow is per run (one action vs. linear pipeline vs. branching logic vs. multiple independent workflows).

| Option | Description |
|--------|-------------|
| `single_action` | One discrete action per invocation. |
| `sequential_workflow` | Multi-step linear pipeline; conditionals are guard clauses only. |
| `branching_workflow` | Core logic diverges based on input type or business rules. |
| `multi_workflow_orchestration` | Two or more independent sub-workflows in one agent. |
| `unknown` | Could not be determined. |

---

### 4. `data_flow_direction`

**Dimension description:** Where data moves relative to ClickUp (pulling in, reshuffling internally, pushing out, or both directions).

| Option | Description |
|--------|-------------|
| `inbound` | Captures external data into ClickUp. |
| `processing` | Restructures/condenses ClickUp data; output stays in ClickUp. |
| `outbound` | Output leaves ClickUp or is genuinely new intellectual content. |
| `bidirectional` | Requires both importing and exporting external data. |
| `unknown` | Could not be determined. |

---

### 5. `autonomy_level`

**Dimension description:** Whether the agent asks before acting, acts then reports, or acts silently on its own.

| Option | Description |
|--------|-------------|
| `consultative` | Asks user before acting — human gates the action. |
| `human_in_the_loop` | Acts first, then reports for human review. |
| `autonomous` | Acts without asking; handles edge cases via fallback rules. |
| `enforcer` | Validates compliance and corrects violations. |
| `monitor` | Surfaces alerts without fixing anything. |
| `unknown` | Could not be determined. |

---

### 6. `functional_archetype`

**Dimension description:** The agent's primary job function (creating, organizing, analyzing, communicating, monitoring, or enforcing).

| Option | Description |
|--------|-------------|
| `communicator` | Drafts and sends messages (emails, DMs, notifications). |
| `analyzer` | Produces insights, metrics, or recommendations from data. |
| `organizer` | Structures, routes, or categorizes existing work items. |
| `creator` | Generates new content — writing, images, docs, code. |
| `monitor` | Observes and reports; does not create or enforce. |
| `enforcer` | Enforces rules, compliance, or corrections. |
| `unknown` | Could not be determined. |

---

### 7. `tone_and_persona`

**Dimension description:** The communication style the agent adopts (formal, casual, technical, or empathetic).

| Option | Description |
|--------|-------------|
| `professional_formal` | Concise, structured, executive-ready. |
| `casual_friendly` | Warm, conversational, approachable. |
| `technical_precise` | Data-driven, rigorous, systematic. |
| `empathetic_supportive` | Encouraging, coaching, patient. |
| `unknown` | Could not be determined. |

---

### 8. `execution_dataset`

**Dimension description:** What the agent works on per invocation and who decides the scope (one triggered event, one user request, one user-provided asset, or a scanned collection).

| Option | Description |
|--------|-------------|
| `single_event_data` | Triggered by one ClickUp automation event. |
| `single_user_prompt` | User sends a request/brief; agent creates in response. |
| `single_asset_from_user` | User provides material; agent parses/transforms it. |
| `collection_scoped` | Queries a defined scope (named lists, time windows). |
| `collection_unbounded` | Searches broadly with no predetermined boundary. |
| `messages` | Comments, DMs, or chat messages. |
| `unknown` | Could not be determined. |

---

### 9. `output_modality`

**Dimension description:** The type of artifact the agent primarily produces (messages, docs, tasks, images, or emails).

| Option | Description |
|--------|-------------|
| `structured_document` | ClickUp Docs or Doc Pages. |
| `task_artifact` | Tasks, subtasks, or checklists. |
| `visual_image` | AI-generated images or visual designs. |
| `email_external_message` | Emails or messages sent outside ClickUp. |
| `messages` | Comments, DMs, or in-app messages. |
| `unknown` | Could not be determined. |

---

### 10. `domain_industry_vertical`

**Dimension description:** Which industry or functional area the agent serves (PM, sales, marketing, HR, legal, finance, education, personal, creative, engineering, or general).

| Option | Description |
|--------|-------------|
| `project_management_ops` | Projects, sprints, standups, deadlines, capacity. |
| `sales_crm` | Deals, pipeline, leads, CRM, revenue. |
| `marketing_content` | Content, social media, SEO, campaigns, branding. |
| `hr_people` | Hiring, recruiting, onboarding, performance. |
| `legal_compliance` | Legal, contracts, compliance, regulatory. |
| `finance_accounting` | Budgeting, invoicing, financial reporting. |
| `education_academic` | Teaching, tutoring, coursework, exam prep. |
| `personal_productivity` | Personal planning, habits, journaling (non-work). |
| `creative_design` | Graphic design, UI/UX, image generation, video. |
| `it_engineering` | Software dev, coding, debugging, DevOps. |
| `general_cross_functional` | General-purpose or doesn't fit a specific vertical. |
| `unknown` | Could not be determined. |

---

### 11. `state_persistence`

**Description:** Whether and how the agent keeps state across invocations.

| Option | Description |
|--------|-------------|
| `stateless` | No state kept across calls. |
| `state_referencing` | References existing state but does not accumulate. |
| `state_accumulating` | Accumulates state across invocations. |
| `unknown` | Could not be determined. |

---

### 12. `external_integration_scope`

**Description:** Extent of integration with systems outside ClickUp.

| Option | Description |
|--------|-------------|
| `clickup_only` | No external integrations; ClickUp only. |
| `email_integration` | Integrates with email. |
| `calendar_integration` | Integrates with calendar. |
| `web_research_integration` | Uses web/search or research tools. |
| `multiple_external_systems` | Integrates with multiple external systems. |
| `unknown` | Could not be determined. |

---

### 13. `use_case_context`

**Description:** High-level context of how the agent is used (specific workflow, general productivity, personal, etc.).

| Option | Description |
|--------|-------------|
| `specific_use_case` | Tied to a specific workflow or business use case. |
| `general_productivity` | General productivity assistance. |
| `personal_use_case` | Personal use (e.g. study, habits). |
| `personal_productivity` | Personal productivity. |
| `entertainment` | Entertainment or non-work. |
| `test_or_placeholder` | Test or placeholder agent. |
| `unknown` | Could not be determined. |

---

### 14. `implied_end_date`

**Description:** Whether the agent’s use case implies a defined end date (e.g. project end, course end).

| Option | Description |
|--------|-------------|
| `true` | Use case implies an end date. |
| `false` | No implied end date. |
| `unknown` | Could not be determined. |

---

### 15. `business_items`

**Description:** Free-text list of business entities or concepts the agent works with (e.g. “clients, tickets, invoices”), as derived from the prompt. Not a closed taxonomy; many distinct values.

---

## Suggested dimensions (for grouping/filtering)

- All classification columns above (e.g. `domain_knowledge_depth`, `operational_scope`, `autonomy_level`, `functional_archetype`, `domain_industry_vertical`).
- Use with **super_agents** (join on `agent_id`) to slice agent counts, run counts, or tool usage by classification.

## Suggested measures (aggregations)

- **Agent count** — total classified agents; count by any dimension (e.g. by `operational_scope`, `domain_industry_vertical`).
- **Classified agent share** — count in agent_classifications vs. count in super_agents (coverage).
- When joined to **super_agent_run** or **super_agent_tools** via **super_agents**: run count, tool call count, or cost by classification dimension.
