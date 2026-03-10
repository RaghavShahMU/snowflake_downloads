# Agent success and retention analysis

**Last updated:** 2026-03-10 (after full pipeline run with directional analysis and prompts-only)

---

## 1. Executive summary

- **Success definition:** Agents active and used at least once after 7 days post-creation; **39,606 success**, 30,889 failure, 86,437 dormant (156,932 total in cohort). Success rate among non-dormant is ~56%.
- **Triggers:** **Scheduled** is the strongest positive driver of success (48.8% of runs among success agents vs 2.5% dormant, 20.3% failure). **Introduction** is strongly associated with failure/dormant (40.5% dormant, 5.3% success). Logistic coefficients confirm: scheduled +1.59, introduction −2.17.
- **Tools:** Success agents use more **post_chat_message**, **read_memory**, **write_memory**, **retrieve_activity**, **create_task** (cohort comparison p ≈ 0). RF importance: read_memory, todo_write, post_reply, retrieve_tasks_by_filters. Logistic: todo_write positive, post_reply negative (context-dependent).
- **Prompts (classifications):** Among 113,863 classified agents (36,712 success, 6,611 failure, 70,540 dormant), **trigger and template dominate** the full model (scheduled +1.25, introduction −1.21; template=custom +0.56). **Prompts-only** (no trigger/template) shows classification dimensions matter: execution_dataset=collection_scoped, functional_archetype=creator/monitor, data_flow_direction=outbound, output_modality=visual_image.
- **Retention insight:** Driving agents toward **scheduled** usage and **custom templates**, and away from introduction-heavy mixes, aligns with higher success. Tool usage (memory, chat, tasks) is higher in success; prompt design (creator/monitor, collection-scoped execution) adds signal when trigger/template are excluded.

---

## 2. Methodology

### Success criteria

- **Success:** After 7 days of creation, the agent has been used at least once (manually, DM, automated, scheduled, or any other form) and is still **active** as of the analysis date. Edits/updates after 7 days still count as success.
- **Failure:** Agent is **inactive** and/or **deleted**.
- **Dormant:** Created, not deleted, **active**, but **no usage post 7 days** of creation.
- **Unknown / other:** Any agent that does not fall into the above three categories.

**Parameters:** `analysis_reference_date` (see cohort_metadata.yaml); `days_post_creation` = 7.

### Data sources

- **super_agents** — agent list and status.
- **super_agent_run** — runs and trigger/template.
- **super_agent_tools** — tool calls (ClickUp tools).
- **agent_classifications** — LLM-derived prompt dimensions (exclude business_items). Prompts analysis scope: only agents in this table.

### Scope by analysis

| Analysis | Scope |
|----------|--------|
| Success criteria, triggers, tools | All agents in super_agents.csv |
| Prompts (classifications) | Only agent_ids in agent_classifications.csv |

---

## 3. Sample and metadata

- **Cohort size:** 156,932 agents (analysis_reference_date: 2026-03-10).
- **Segment counts:** success 39,606; failure 30,889; dormant 86,437; unknown 0.
- **Classification coverage:** 113,863 agents with classifications (dormant 70,540, success 36,712, failure 6,611). All success/failure/dormant in prompts analysis are from this subset.

---

## 4. Assumptions and conditions

- Reference date is set in config (2026-03-10). Cohort and run/tool data are as of the CSV export used for the run.
- TRIGGER_SOURCE may include `\N` (normalized to "unknown" where needed). Segment definitions are simplifications (e.g. dormant vs success is usage-based; we do not model time-to-failure).
- RF and logistic models use resampled (trigger) or full (tool, classification) data; SHAP is on a sample (e.g. 500 agents) for speed. Directional interpretation uses signed mean SHAP and logistic coefficients together.

---

## 5. Results

### 5.1 Success criteria

**Tables, graphs, visuals:**  
- Cohort distribution: see `analysis/output/cohort_segment_distribution.png` and `cohort_segment_counts.csv`.

**Commentary:**  
Dormant agents (86,437) outnumber success (39,606) and failure (30,889) combined. Among agents with any usage (success + failure), success rate is ~56%. The large dormant segment indicates many agents are created but never used after the 7-day window—opportunity for activation and onboarding.

**Recommended actions:**  
- Focus on converting dormant agents to first use (onboarding, discovery, scheduled nudges).
- Monitor failure segment for churn patterns; reinforce triggers and tools associated with success.

---

### 5.2 Trigger sources

**Tables, graphs, visuals:**  
- Trigger taxonomy: `analysis/output/trigger_taxonomy.csv`  
- Trigger × segment (mean % per agent): `trigger_by_segment.csv`, `trigger_by_segment.png`  
- RF importance: `trigger_rf_importance.csv`  
- SHAP: `trigger_shap_summary.csv`, `trigger_shap_bar.png`  
- **Directional:** `trigger_shap_direction.csv` (signed mean SHAP: positive → toward success), `trigger_shap_by_value.csv` (mean SHAP by quartile bin), `trigger_logistic_coefficients.csv` (validation of direction), `trigger_shap_beeswarm.png` (SHAP by agent, color = feature value).

**Commentary:**  
- **Scheduled** has the highest mean % among success agents (48.8%) vs dormant (2.5%) and failure (20.3%). RF importance (0.48) and positive logistic coefficient (+1.59) both indicate scheduled usage strongly pushes toward success.
- **Introduction** is dominant in dormant (40.5%) and failure (23.0%) and low in success (5.3%). Logistic coefficient −2.17 and high RF importance (0.26) show introduction-heavy mix is associated with failure/dormant.
- **dm** and **automation** have moderate positive coefficients (+0.42, +0.53); **\N** (unknown trigger) is slightly negative (−0.13). Signed mean SHAP aligns: introduction and scheduled have the largest |mean_shap| with opposite directional pull.

**Recommended actions:**  
- Double down on **scheduled** triggers (recurring use) and reduce reliance on **introduction** as the primary driver.
- Encourage dm and automation where appropriate; treat unknown/missing trigger as a data-quality and product signal.

---

### 5.3 ClickUp tools

**Tables, graphs, visuals:**  
- Tool taxonomy: `analysis/output/tool_taxonomy.csv`  
- Tool × segment: `tool_by_segment.csv`, `tool_by_segment.png`  
- Cohort comparison (success vs failure, p-values): `tool_cohort_comparison.csv`  
- RF importance: `tool_rf_importance.csv`  
- SHAP: `tool_shap_bar.png`  
- **Directional:** `tool_shap_direction.csv`, `tool_shap_by_value.csv` (quartile bins), `tool_logistic_coefficients.csv`, `tool_shap_beeswarm.png`.

**Commentary:**  
- Cohort comparison (Mann-Whitney): **write_memory**, **view_tools_catalog**, **post_chat_message**, **post_reply**, **post_task_comment**, **read_memory**, **retrieve_activity**, **create_task** (and others) have significantly higher mean usage in success than failure (p ≈ 0). Success agents use more messaging, memory, and task/activity tools.
- RF importance: read_memory (0.24), todo_write (0.20), post_reply (0.11), retrieve_tasks_by_filters (0.11), post_chat_message (0.07). SHAP mean magnitude is highest for read_memory, todo_write, post_reply.
- Logistic coefficients: todo_write +0.99, post_reply −0.46, read_memory +0.23, retrieve_tasks_by_filters +0.21. Direction can differ from raw “more usage = success” because of correlations (e.g. post_reply may be conditional on other factors). Use cohort comparison and SHAP-by-value for “higher usage band → higher success” and logistic for marginal direction in the linear combination.

**Recommended actions:**  
- Promote tools that show both higher usage in success and positive coefficient where interpretable: **read_memory**, **write_memory**, **retrieve_activity**, **create_task**, **post_chat_message**, **post_task_comment**.
- Use SHAP beeswarm and `tool_shap_by_value.csv` to see how direction changes by usage level (quartile).

---

### 5.4 Prompts (classifications)

**Tables, graphs, visuals:**  
- Coverage: `analysis/output/classification_coverage.csv`  
- Per dimension: `classification_dim_<dim>.csv`  
- Trigger × segment: `classification_trigger_by_segment.csv`  
- Template × segment: `classification_template_by_segment.csv`  
- RF importance: `classification_rf_importance.csv`  
- SHAP: `classification_shap_bar.png`  
- **Directional:** `classification_shap_direction.csv`, `classification_shap_by_value.csv` (value 0 vs 1 per one-hot), `classification_logistic_coefficients.csv`, `classification_shap_beeswarm.png`  
- Example: `classification_operational_scope_success_rate.png`  
- Dedicated section: **§5.5 Prompts-only** (no trigger/template).

**Commentary:**  
- **Full model (with trigger/template):** Trigger and template dominate. RF: trigger=scheduled (0.35), trigger=introduction (0.12), then functional_archetype=creator, execution_dataset=collection_scoped. Logistic: trigger=scheduled +1.25, trigger=introduction −1.21, template=custom +0.56, template=unknown −0.56. Among classified agents, scheduled trigger and custom template are the strongest levers; introduction and unknown template pull toward failure.
- **Classification dimensions in full model:** functional_archetype=creator/monitor, execution_dataset=collection_scoped, data_flow_direction=outbound, output_modality=visual_image, domain_industry_vertical=creative_design have notable importance; logistic shows domain_industry_vertical=creative_design negative (−0.18), project_management_ops positive (+0.07), autonomy_level=consultative negative (−0.02).
- **operational_scope:** multi_workflow_orchestration has the highest success rate (~58.5%) in the dimension table; branching_workflow and sequential_workflow lower (~22–33%).

**Recommended actions:**  
- Prioritize **scheduled** trigger and **custom** template in product and onboarding.
- In prompt design, favor **collection-scoped** execution, **creator/monitor** archetypes, **outbound** data flow (see §5.5 Prompts-only). Use full vs prompts-only comparison to separate how the agent is triggered/templated from how the agent is classified.

---

### 5.5 Prompts-only analysis (no trigger, no template)

Model uses **only** one-hot encoded classification dimensions (LLM-derived prompt dimensions). No trigger or template features. Same cohort (113,863 classified agents).

**Tables, graphs, visuals:**  
- RF importance: `classification_prompts_only_rf_importance.csv`  
- SHAP direction: `classification_prompts_only_shap_direction.csv`  
- SHAP by value (0 vs 1 per feature): `classification_prompts_only_shap_by_value.csv`  
- Logistic coefficients: `classification_prompts_only_logistic_coefficients.csv`  
- SHAP bar: `classification_prompts_only_shap_bar.png`  
- SHAP beeswarm: `classification_prompts_only_shap_beeswarm.png`

**Commentary:**  
- **Top importance:** execution_dataset=collection_scoped (0.17), functional_archetype=creator (0.13), monitor (0.09), execution_dataset=single_user_prompt (0.07), data_flow_direction=outbound (0.04), output_modality=visual_image (0.04). **Prompt design** (execution scope, archetype, data flow, modality) carries signal for success when trigger and template are excluded.
- **Logistic (prompts-only):** creative_design and consultative autonomy negative; project_management_ops, finance_accounting, personal_productivity positive. Interpretation is purely about classification dimensions, not how the agent is triggered or templated.

**Recommended actions:**  
- Use prompts-only outputs to iterate on classification dimensions and prompt taxonomy without conflating with trigger/template. Compare with full model (§5.4) to attribute success to prompts vs trigger/template.

---

## 6. Appendix (exhaustive)

- **Trigger taxonomy:** full list and counts — `analysis/output/trigger_taxonomy.csv`
- **Tool list:** full list and counts — `analysis/output/tool_taxonomy.csv`
- **Classification dimension tables:** `analysis/output/classification_dim_*.csv`
- **Cohort summary:** `analysis/output/cohort_metadata.yaml`, `cohort_segment_counts.csv`
- **RF/SHAP:** importance and SHAP summary CSVs and figures in `analysis/output/`
- **Directional (triggers, tools, classifications):** `*_shap_direction.csv`, `*_shap_by_value.csv`, `*_logistic_coefficients.csv`, `*_shap_beeswarm.png`
- **Prompts-only:** all `classification_prompts_only_*` outputs (classifications-only model, no trigger/template) — see §5.5
- **Reference data:** CSV row counts and date ranges used in the run
- **Code/script references:** `analysis/define_success_cohort.py`, `trigger_success_analysis.py`, `tool_success_analysis.py`, `classification_success_analysis.py`, `run_all_analysis.py`, `config.yaml`
