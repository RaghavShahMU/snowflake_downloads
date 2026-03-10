---
name: Agent success and retention analysis
overview: Analysis of agent success and retention (success criteria, trigger sources, ClickUp tools, prompt classifications) with Random Forest + SHAP, cohort/statistical tests, and an exhaustive C-suite readout with commentary and recommended actions.
todos: []
isProject: false
---

# Agent success and retention analysis — plan

## Objective

Understand which types of agents tend to be more **successful** and **retained**, and produce a **running C-suite readout** (methodology, data, sample, assumptions, commentary, recommended actions) for data-based product and retention decisions.

---

## Scope (population)

| Analysis | Scope (agent population) |
|----------|---------------------------|
| Success criteria, trigger-source analysis, ClickUp tool success | **All agents** in `super_agents.csv` |
| Prompts (classifications) analysis | **Only agent_ids** present in `agent_classifications.csv` |

---

## Data and model context

- **super_agents** — 156,932 agents; `CURRENT_AGENT_STATUS`, `AGENT_CREATED_AT`, `AGENT_DELETED_AT`.
- **super_agent_run** — 3.2M runs; `TRIGGER_SOURCE`, `TRIGGER_SURFACE_TYPE`, `TRIGGER_SURFACE_SUBTYPE`, `RUN_STARTED_AT`, `AGENT_ID`, `RUN_ID`.
- **super_agent_tools** — 59.6M tool calls; `CALL_TYPE`, `CALL_NAME`, `CLICKUP_TOOL_TYPE`, `IS_SUCCESS`, `AGENT_ID`, `RUN_ID`.
- **agent_classifications** — 114,802 agents; categorical dimensions; **exclude `business_items`** for prompts analysis.

Joins: run/agents/tools as in semantic layer; classifications join on `agent_id`.

---

## 1. Success criteria (agent-level segments)

**Scope:** All agents in `super_agents.csv`.

**Exact definitions:**

| Segment | Definition |
|---------|------------|
| **Success** | After 7 days of creation, the agent has been **used** at least once (manually, DM, automated, scheduled, or any other form) **and** is still **active** as of the analysis date. Edits/updates after 7 days still count as success (user iterating on prompt/outcome; active). |
| **Failure** | Agent is **inactive** and/or **deleted**. |
| **Dormant** | Created, not deleted, **active**, but **no usage post 7 days** of creation. |
| **Unknown / other** | Any agent that does not fall into the above three categories. |

**Parameters:** `analysis_reference_date` (for "to date"); `days_post_creation` = 7.

**Implementation:** (1) From `super_agent_run`, compute per agent: first run date, any run after `AGENT_CREATED_AT + 7 days`. (2) Join to `super_agents` for `CURRENT_AGENT_STATUS`, `AGENT_CREATED_AT`, `AGENT_DELETED_AT`. (3) Apply rules: failure (inactive or deleted) → success (active and used post 7 days) → dormant (active, no use post 7 days) → unknown/other. (4) Output **cohort table**: `AGENT_ID`, `success_segment`, and key attributes. Cohort is used for trigger and tool analyses (all agents) and, when restricted to `agent_classifications.agent_id`, for prompts analysis. (5) **Graphs/visuals/tables** wherever applicable (e.g. cohort distribution bar chart, segment counts table).

---

## 2. Trigger sources and success

**Scope:** All agents in `super_agents.csv` (cohort).

**Goal:** Trigger taxonomy, trigger source vs segment, triggers associated with success. **Normalize metrics as percentage per agent** so successful agents (with more runs) do not dominate: e.g. if one agent has 20 DM, 35 comments/mentions, 45 scheduled runs, express as 20% DM, 35% comments/mentions, 45% scheduled (each agent’s trigger mix sums to 100%).

**Data:** `super_agent_run`: `TRIGGER_SOURCE`, `TRIGGER_SURFACE_TYPE`, `TRIGGER_SURFACE_SUBTYPE` (and optionally `USE_TYPE`). Derive **trigger taxonomy** from the data; normalize `\N` and map surface type/subtype to manual / mentions / chats where present.

**Method:**

- For each agent, compute run counts by trigger (source and/or surface); then **normalize to percentages** (share of that agent’s total runs).
- Aggregate: trigger taxonomy (list with counts); table trigger × segment (e.g. mean % per agent by segment); triggers associated with success (higher mean % in success vs failure/dormant).
- **Random Forest:** Use normalized trigger percentages (and optionally segment as target) to extract **feature importance** (which triggers predict success).
- **SHAP:** Run SHAP on the same model for **directional insights** (e.g. higher DM % → higher success probability).
- **Class balance:** If success vs failure (or vs non-success) is extremely imbalanced, **resample or rebalance** the training set (e.g. oversample minority or undersample majority); use best judgment and document in readout.

**Outputs:** (1) Trigger taxonomy. (2) Table: trigger source × segment (normalized: mean % per agent). (3) Trigger importance and SHAP summary. (4) Narrative: triggers leading to more success. (5) **Graphs/visuals/tables** wherever applicable (e.g. bar chart trigger × segment, SHAP summary plot, taxonomy table).

**Documentation:** In readout: trigger definitions, normalization method (%), RF/SHAP setup, resampling if applied, and how “associated with success” is measured.

---

## 3. ClickUp tools and success

**Scope:** All agents in `super_agents.csv` (cohort).

**Goal:** Same structure as triggers: taxonomy, tool × segment, tools associated with success. **Normalize as average tool count per run per agent:** e.g. agent ran 20 times with total reply count 100 and image generated 5 → avg reply per run = 5, avg image per run = 0.25. This avoids bias from agents with more runs having higher raw counts.

**Data:** `super_agent_tools`: filter `CALL_TYPE = 'clickup_tool'` (and `VENDOR = 'clickup'` if needed). Use `CALL_NAME` and/or `CLICKUP_TOOL_TYPE` as tool identifier. Use `IS_SUCCESS` (normalize to boolean; handle null/unknown).

**Method:**

- For each agent: run count in scope; per-tool call counts in those runs. Compute **avg tool count per run** per agent (e.g. total reply / run count).
- Aggregate: tool list (taxonomy) with counts; table tool × segment (e.g. mean avg-per-run by segment); tools associated with success.
- **Random Forest + SHAP:** Same as triggers: feature importance and directional insights using normalized tool metrics (avg per run).
- **Cohort analysis:** Success vs failed cohort: for each tool, compute **average value (avg per run)** for success cohort and for failed cohort; test **statistical significance** (e.g. t-test or Mann-Whitney) and report p-values. Document which tools differ significantly between success and failure.

**Outputs:** (1) ClickUp tool list with counts and success rates. (2) Table: tool × segment (normalized: mean avg per run per agent). (3) RF importance + SHAP summary. (4) Cohort comparison: success vs failed, mean per tool + statistical significance. (5) Narrative: tools resulting in more successful agents. (6) **Graphs/visuals/tables** wherever applicable (e.g. tool × segment heatmap or bar chart, cohort comparison table/chart, SHAP plot, significance summary table).

**Documentation:** In readout: definition of ClickUp tool, normalization (avg per run), RF/SHAP, cohort comparison method and significance tests.

---

## 4. Prompts (classifications) and success

**Scope:** **Only agent_ids** in `agent_classifications.csv` (joined to cohort for segment).

**Goal:** Which prompt types (classifications) are associated with more successful agents. Work at **one-hot encoded level** (categorical columns → dummy variables). **No normalization** (already agent-level). **Exclude `business_items`** (exploded values, no clear definition/scope). **Include trigger type and template type** for comparison and analysis alongside classifications.

**Data:** `agent_classifications`: all classification dimensions except `business_items`. Join to cohort on `agent_id`. **Add from run data (aggregated to agent level):** (1) **Trigger type** — scheduled / manual / automated (and other trigger categories from taxonomy); derive per-agent (e.g. primary trigger or one-hot from run-level trigger distribution). Source: `super_agent_run`: `TRIGGER_SOURCE`, `TRIGGER_SURFACE_TYPE`, `TRIGGER_SURFACE_SUBTYPE`. (2) **Template** — **custom vs templated** (one-hot); if templated, **template sub-type** (one-hot). Source: `super_agent_run`: `TEMPLATE_TYPE`; template sub-type from run/agent data if available (discover from schema or data).

**Method:**

- **One-hot encode** all classification dimensions (e.g. operational_scope_branching_workflow, functional_archetype_creator, etc.). Drop or keep `unknown` per dimension; document choice.
- **One-hot encode trigger type** (scheduled, manual, automated, and other trigger categories) at agent level for the prompts cohort (e.g. primary trigger per agent, or binary flags from run aggregates).
- **One-hot encode template:** custom vs templated; and **template sub-type** (e.g. templated_subtype_A, templated_subtype_B, …) when templated. Two additional feature groups for comparison.
- **Random Forest + SHAP:** Target = segment (e.g. success vs non-success); features = one-hot classification dimensions + trigger one-hot + template one-hot (+ template_subtype one-hot). Extract importance and SHAP for directional insights; compare role of triggers and template vs prompt classifications.
- **Detailed per-column analysis:** For each classification dimension, report population (count) by segment; success rate per dimension value; top values by success rate or share of success agents. Include **trigger (scheduled/manual/automated) vs segment** and **template (custom/templated) and template sub-type vs segment** in the same style (tables and narrative).

**Outputs:** (1) Coverage: count of cohort agents with classification; by segment. (2) Per dimension: table value × segment (counts, success rate); narrative. (3) **Trigger (scheduled/manual/automated) and template (custom/templated + sub-type) vs segment** tables and narrative for comparison. (4) RF importance + SHAP summary for one-hot features (including trigger and template). (5) Narrative: which prompt types, triggers, and template types create more successful agents. (6) **Graphs/visuals/tables** wherever applicable (e.g. dimension value × segment bar charts, trigger × segment, template × segment, SHAP summary plot, heatmaps or summary tables).

**Documentation:** In readout: dimensions analyzed, exclusion of business_items, one-hot encoding and handling of unknown; addition of trigger and template (custom/templated + sub-type) for comparison; RF/SHAP setup.

---

## 5. C-suite readout document (running, exhaustive)

**Location:** `docs/agent_success_retention_readout.md` (single Markdown file; versionable, exportable to PDF).

**Structure:**

1. **Title and date** — "Agent success and retention analysis"; "Last updated: &lt;date&gt;".
2. **Executive summary** — 3–5 bullet takeaways (success definition, top triggers, top tools, top classifications, retention insight).
3. **Methodology** — Success criteria (exact definitions, reference date, days_post_creation); data sources and join keys; time scope; scope by analysis (all agents vs classifications-only for prompts).
4. **Sample and metadata** — Cohort size and segment counts; run/tool volume in scope; classification coverage for prompts analysis.
5. **Assumptions and conditions** — Reference date, data quality caveats, segment definition limitations.
6. **Results** — **Dedicated section per analysis** (success criteria, trigger sources, ClickUp tools, prompts), each with:
   - **Tables, graphs, and visuals** — Include all relevant tables, charts (e.g. bar, heatmap, SHAP summary), and figures produced by the analysis.
   - **Commentary on the analysis and results:** What can be inferred; are findings statistically relevant or significant?
   - **Recommended actions** — What the organization could do to improve agents, usage, and retention based on the evidence.
7. **Appendix (exhaustive)** — Full results and metadata for **all** analyses and reference data used: trigger taxonomy; tool list with counts; classification dimension tables; cohort summary stats; RF/SHAP config and key outputs; reference data used (e.g. CSV row counts, date ranges); code/script references; and **all supporting tables/graphs/visuals** not in the main results.

Every time new analysis or parameters are run, update this document (methodology, sample metadata, results, commentary, recommended actions, appendix).

---

## 6. Implementation layout

```
analysis/
  config.py or config.yaml          # analysis_reference_date, days_post_creation = 7
  define_success_cohort.py          # Output: agent_id, success_segment, ...
  trigger_success_analysis.py       # Trigger taxonomy; normalized %; RF + SHAP; outputs
  tool_success_analysis.py         # Tool taxonomy; normalized avg per run; RF + SHAP; cohort comparison + statistical significance
  classification_success_analysis.py  # One-hot + trigger + template (custom/templated + subtype); exclude business_items; RF + SHAP; per-dimension detail; visuals
  run_all_analysis.py               # Optional: run scripts in order
docs/
  agent_success_retention_readout.md   # Single running C-suite readout (with commentary + exhaustive appendix)
analysis/output/                    # CSV/JSON + graphs/visuals (charts, tables) for each analysis
```

**Tech:** Python + DuckDB for data; scikit-learn for Random Forest; SHAP for explanations; scipy/stats for significance tests; matplotlib/seaborn (or equivalent) for **graphs and visuals**. Outputs to `analysis/output/` (CSV/JSON + figures); readout updated from outputs and references or embeds **tables, graphs, and visuals** for each analysis wherever applicable.

**Execution order:** (1) Config. (2) Define cohort (all agents). (3) Trigger analysis (cohort + runs, normalized %, RF + SHAP). (4) Tool analysis (cohort + runs + tools, normalized avg/run, RF + SHAP + cohort comparison). (5) Classification analysis (cohort restricted to agent_classifications.agent_id, one-hot, RF + SHAP + per-dimension). (6) Update readout (all sections + commentary + exhaustive appendix).

---

## 7. Summary

| Pillar | Scope | Normalization | ML / stats | Readout |
|--------|-------|---------------|------------|---------|
| Success criteria | All agents | — | — | Cohort distribution; definitions; **tables/visuals** |
| Trigger sources | All agents | % per agent (trigger mix = 100%) | RF + SHAP; resample if imbalanced | Taxonomy; trigger × segment; importance; **graphs/tables**; commentary; actions |
| ClickUp tools | All agents | Avg tool count per run per agent | RF + SHAP; cohort comparison + significance tests | Tool × segment; success vs failed means + p-values; **graphs/tables**; commentary; actions |
| Prompts | Classifications-only | None (agent-level, one-hot) | RF + SHAP; per-dimension detail; **+ trigger (sched/manual/auto) + template (custom/templated + subtype)** | Per-column + trigger + template vs segment; **graphs/tables**; commentary; actions |

**Appendix:** Exhaustive — all results, metadata, and reference data for every analysis.
