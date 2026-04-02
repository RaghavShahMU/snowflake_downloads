# Prompts-only classification readout

**Last updated:** 2026-04-03  
**Maintenance:** This file and `prompts_classification_readout_plain.html` are edited by hand. Refresh numbers, charts, and `analysis/output/leadership_corr_heatmap_map.json` by running the analysis scripts; there is no doc generator for these readouts.  
**Scope:** Classification dimensions only (no triggers or tools in the success model). Correlation sections add tools, triggers, and templates for context.  
**Data:** Classified cohort (agents in `agent_classifications.csv` with success_segment from cohort).  
**Value meanings:** See [semantic_layer/models/agent_classifications.md](semantic_layer/models/agent_classifications.md).  
**Interactive view:** [prompts_classification_readout_plain.html](prompts_classification_readout_plain.html) loads heatmap paths from `../analysis/output/leadership_corr_heatmap_map.json` at runtime (serve over HTTP if `file://` blocks fetch).

## Executive summary

- **Purpose:** Link **prompt classifications** to **success vs non-success** (same cohort definitions as the main agent success readout).
- **Prompts-only model:** **Random Forest**, **SHAP**, and **logistic regression** on one-hot classification features only (no triggers/templates in that model).
- **Correlation blocks:** Agent-level **Pearson** between prompt dimensions and tools/triggers/templates (|r| ≥ 0.05 in dimension tables).
- **Cohort size:** Classified agents with segment counts below; ~**114K** prompts in classification pass.
- **Lead takeaway:** **Collection-scoped** execution and **monitor** archetype align with success; **single-user prompt** execution and **creator** archetype align with lower modeled success—details in **Key findings**.

**Detailed data analysis and methodologies** — See [Methodology and footnotes](#methodology-and-footnotes).

## Key findings

<details>
<summary><strong>Finding 1 — Execution dataset</strong> — <em>Scoped collections dominate RF/LR; one-off user prompts trail.</em></summary>

- **collection_scoped** — **Highest RF importance** (0.174) and **strong positive LR** (+0.346): agents scoped to a defined collection tend to model as more successful.
- **single_user_prompt** — **Strong negative** in both RF (0.069) and LR (-0.273): ad-hoc user Q&amp;A style aligns with lower modeled success.
- **Other execution_dataset levels** — **collection_unbounded** RF/LR (0.047 / +0.228); **single_event_data** and **single_asset_from_user** (0.031/-0.068; 0.027/-0.258).

**Distribution (classified cohort)**
### 2. Execution dataset

**Classification**  
What the agent works on per invocation (single event, user prompt, asset, collection_scoped, collection_unbounded, messages).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| collection_scoped | Queries a defined scope (lists, time windows). | 11,213 | 3,125 | 18,728 | 0.57 | <span style="color:green">retrieve_tasks_by_filters 0.38</span>; <span style="color:green">todo_write 0.37</span>; <span style="color:green">read_memory 0.22</span> | <span style="color:#c00">post_reply -0.27</span> | <span style="color:green">functional_archetype=monitor 0.28</span>; <span style="color:green">data_flow_direction=processing 0.27</span>; <span style="color:green">operational_scope=multi_workflow_orchestration 0.23</span> | <span style="color:#c00">functional_archetype=creator -0.37</span>; <span style="color:#c00">data_flow_direction=outbound -0.32</span>; <span style="color:#c00">output_modality=visual_image -0.22</span> |
| collection_unbounded | Searches broadly with no predetermined boundary. | 3,458 | 1,134 | 6,593 | 0.59 | <span style="color:green">todo_write 0.24</span>; <span style="color:green">retrieve_tasks_by_filters 0.21</span> | — | <span style="color:green">functional_archetype=monitor 0.28</span>; <span style="color:green">domain_knowledge_depth=none 0.22</span>; <span style="color:green">domain_industry_vertical=project_management_ops 0.21</span> | <span style="color:#c00">functional_archetype=creator -0.21</span>; <span style="color:#c00">domain_knowledge_depth=moderate -0.18</span>; <span style="color:#c00">data_flow_direction=outbound -0.15</span> |
| single_asset_from_user | User provides material; agent parses/transforms it. | 10,795 | 194 | 999 | 0.08 | — | <span style="color:#c00">todo_write -0.20</span> | <span style="color:green">domain_industry_vertical=education_academic 0.23</span>; <span style="color:green">functional_archetype=creator 0.23</span>; <span style="color:green">operational_scope=sequential_workflow 0.22</span> | <span style="color:#c00">operational_scope=branching_workflow -0.15</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.15</span>; <span style="color:#c00">data_flow_direction=processing -0.13</span> |
| single_event_data | Triggered by one ClickUp automation event. | 19,695 | 1,529 | 7,100 | 0.25 | — | <span style="color:#c00">retrieve_tasks_by_filters -0.18</span> | <span style="color:green">output_modality=task_artifact 0.16</span>; <span style="color:green">data_flow_direction=processing 0.15</span>; <span style="color:green">functional_archetype=organizer 0.15</span> | <span style="color:#c00">functional_archetype=monitor -0.16</span>; <span style="color:#c00">data_flow_direction=outbound -0.12</span>; <span style="color:#c00">autonomy_level=consultative -0.11</span> |
| single_user_prompt | User sends a request; agent creates in response. | 25,106 | 594 | 3,061 | 0.11 | <span style="color:green">post_reply 0.28</span> | <span style="color:#c00">todo_write -0.33</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.26</span>; <span style="color:#c00">load_assets -0.18</span> | <span style="color:green">data_flow_direction=outbound 0.44</span>; <span style="color:green">functional_archetype=creator 0.43</span>; <span style="color:green">autonomy_level=consultative 0.35</span> | <span style="color:#c00">data_flow_direction=processing -0.41</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.30</span>; <span style="color:#c00">domain_knowledge_depth=light -0.23</span> |
| unknown | Could not be determined. | 273 | 35 | 231 | 0.43 | — | — | <span style="color:green">operational_scope=unknown 0.57</span>; <span style="color:green">data_flow_direction=unknown 0.56</span>; <span style="color:green">autonomy_level=unknown 0.54</span> | <span style="color:#c00">team_orientation=individual -0.15</span>; <span style="color:#c00">operational_scope=branching_workflow -0.07</span>; <span style="color:#c00">external_integration_scope=clickup_only -0.06</span> |

![Execution dataset distribution](../analysis/output/classification_dim_execution_dataset_bar.png)

**Inference:** single_user_prompt and single_asset_from_user have very low success rates (0.11 and 0.08). collection_scoped and collection_unbounded have the highest (0.57 and 0.59). Collection-based execution is strongly associated with success.

**Direction (success vs fail)**

- **Population:** collection_scoped (0.57) and collection_unbounded (0.59) lead; single_user_prompt (0.11) and single_asset_from_user (0.08) trail.
- **Prompts-only model:** <span style="color:green">execution_dataset=collection_scoped</span> has the highest RF importance (0.174) and strong positive coefficient (+0.35); <span style="color:#c00">execution_dataset=single_user_prompt</span> and <span style="color:#c00">execution_dataset=single_asset_from_user</span> are strongly negative (−0.27, −0.26). Direction is very clear: collection-scoped toward success, single-user-prompt/asset toward failure.

**Correlation with tools, triggers, templates**  
See table above. collection_scoped correlates with scheduled and task/retrieval tools; single_user_prompt with introduction.

**Other insights**  
Execution dataset is one of the strongest predictors. Shifting prompts toward collection-scoped or unbounded semantics and away from single-user-prompt/asset may improve success.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

</details>

<details>
<summary><strong>Finding 2 — Functional archetype</strong> — <em>Monitor lifts outcomes; creator-heavy prompts stall.</em></summary>

- **creator** — **Largest negative** modeled pull: high RF importance with **LR ≈ −0.20**; population success rate ~**12%** (see table).
- **monitor** — **Strong positive** RF/LR (**+0.22** logistic); success rate ~**67%** — monitoring-style tasks track with better outcomes in both model and raw rates.

### 1. Functional archetype

**Classification**  
The agent's primary job function (creator, organizer, analyzer, communicator, monitor, enforcer).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| analyzer | Produces insights, metrics, or recommendations from data. | 6,656 | 867 | 4,884 | 0.39 | — | — | <span style="color:green">output_modality=messages 0.16</span>; <span style="color:green">domain_industry_vertical=finance_accounting 0.14</span>; <span style="color:green">external_integration_scope=web_research_integration 0.11</span> | <span style="color:#c00">output_modality=visual_image -0.13</span>; <span style="color:#c00">output_modality=task_artifact -0.13</span>; <span style="color:#c00">domain_industry_vertical=creative_design -0.12</span> |
| communicator | Drafts and sends messages (emails, DMs, notifications). | 2,129 | 500 | 2,528 | 0.49 | — | — | <span style="color:green">output_modality=email_external_message 0.38</span>; <span style="color:green">external_integration_scope=email_integration 0.30</span>; <span style="color:green">data_flow_direction=bidirectional 0.15</span> | <span style="color:#c00">external_integration_scope=clickup_only -0.16</span>; <span style="color:#c00">output_modality=task_artifact -0.10</span>; <span style="color:#c00">output_modality=structured_document -0.09</span> |
| creator | Generates new content (writing, images, docs, code). | 38,672 | 734 | 5,307 | 0.12 | <span style="color:green">post_reply 0.33</span>; <span style="color:green">generate_image 0.21</span> | <span style="color:#c00">todo_write -0.40</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.36</span>; <span style="color:#c00">retrieve_activity -0.20</span> | <span style="color:green">data_flow_direction=outbound 0.65</span>; <span style="color:green">domain_knowledge_depth=moderate 0.49</span>; <span style="color:green">output_modality=visual_image 0.48</span> | <span style="color:#c00">data_flow_direction=processing -0.56</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.50</span>; <span style="color:#c00">domain_knowledge_depth=light -0.38</span> |
| enforcer | Enforces rules, compliance, or corrections. | 1,947 | 375 | 1,640 | 0.41 | — | — | <span style="color:green">data_flow_direction=processing 0.16</span>; <span style="color:green">execution_dataset=single_event_data 0.14</span>; <span style="color:green">domain_knowledge_depth=deep 0.14</span> | <span style="color:#c00">data_flow_direction=outbound -0.14</span>; <span style="color:#c00">domain_knowledge_depth=moderate -0.11</span>; <span style="color:#c00">autonomy_level=consultative -0.10</span> |
| monitor | Observes and reports; does not create or enforce. | 3,297 | 1,750 | 10,049 | 0.67 | <span style="color:green">retrieve_tasks_by_filters 0.36</span>; <span style="color:green">todo_write 0.33</span>; <span style="color:green">post_chat_message 0.33</span> | <span style="color:#c00">post_reply -0.27</span> | <span style="color:green">output_modality=messages 0.32</span>; <span style="color:green">domain_industry_vertical=project_management_ops 0.31</span>; <span style="color:green">data_flow_direction=processing 0.29</span> | <span style="color:#c00">domain_knowledge_depth=moderate -0.28</span>; <span style="color:#c00">data_flow_direction=outbound -0.26</span>; <span style="color:#c00">execution_dataset=single_user_prompt -0.23</span> |
| organizer | Structures, routes, or categorizes existing work items. | 17,770 | 2,373 | 12,265 | 0.38 | <span style="color:green">update_task 0.20</span> | — | <span style="color:green">output_modality=task_artifact 0.48</span>; <span style="color:green">data_flow_direction=processing 0.34</span>; <span style="color:green">domain_industry_vertical=project_management_ops 0.25</span> | <span style="color:#c00">data_flow_direction=outbound -0.44</span>; <span style="color:#c00">output_modality=visual_image -0.25</span>; <span style="color:#c00">domain_knowledge_depth=moderate -0.23</span> |
| unknown | Could not be determined. | 69 | 12 | 39 | 0.32 | — | — | <span style="color:green">data_flow_direction=unknown 0.79</span>; <span style="color:green">operational_scope=unknown 0.76</span>; <span style="color:green">autonomy_level=unknown 0.58</span> | <span style="color:#c00">team_orientation=individual -0.13</span>; <span style="color:#c00">implied_end_date=false -0.08</span>; <span style="color:#c00">external_integration_scope=clickup_only -0.06</span> |

![Functional archetype distribution](../analysis/output/classification_dim_functional_archetype_bar.png)

**Inference:** Creator is the most common but has the lowest success rate (12%). Monitor has the highest success rate (67%). Organizer and analyzer are common with moderate success (~0.38–0.39).

**Direction (success vs fail)**

- **Population:** Monitor (0.67) and communicator (0.49) lead; creator (0.12) trails.
- **Prompts-only model:** <span style="color:#c00">functional_archetype=creator</span> has high importance (0.134) and strong negative coefficient (−0.20); <span style="color:green">functional_archetype=monitor</span> has high importance (0.090) and strong positive coefficient (+0.22). Creator pushes toward failure, monitor toward success.

**Correlation with tools, triggers, templates**  
See table above for top tools and other prompt categories (|r| ≥ 0.05). Monitor correlates with scheduled trigger and task/todo tools; creator with post_reply and introduction.

**Other insights**  
Creator-heavy prompts dominate but underperform; monitor and communicator are strong success levers. Product could favor monitor/communicator patterns where appropriate.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

</details>

<details>
<summary><strong>Finding 3 — Prompt × tool/trigger links</strong> — <em>High-|r| pairs with calendar-style tools de-ranked—open for surprises.</em></summary>

- **functional_archetype=creator** ↔ **todo_write** — *r* = **-0.40** — Lower rate of **todo_write** among agents with **functional_archetype=creator** (co-movement; not causal).
- **execution_dataset=collection_scoped** ↔ **retrieve_tasks_by_filters** — *r* = **0.38** — Higher rate of **retrieve_tasks_by_filters** among agents with **execution_dataset=collection_scoped** (co-movement; not causal).
- **external_integration_scope=web_research_integration** ↔ **search_public_web** — *r* = **0.38** — Higher rate of **search_public_web** among agents with **external_integration_scope=web_research_integration** (co-movement; not causal).
- **execution_dataset=collection_scoped** ↔ **trigger=scheduled** — *r* = **0.38** — Higher rate of **trigger=scheduled** among agents with **execution_dataset=collection_scoped** (co-movement; not causal).
- **functional_archetype=monitor** ↔ **trigger=scheduled** — *r* = **0.37** — Higher rate of **trigger=scheduled** among agents with **functional_archetype=monitor** (co-movement; not causal).
- **execution_dataset=collection_scoped** ↔ **todo_write** — *r* = **0.37** — Higher rate of **todo_write** among agents with **execution_dataset=collection_scoped** (co-movement; not causal).
</details>

---

## Distribution and model drivers

**Segments (classified cohort)**

| Segment | Count | Share | Success rate |
|---------|-------|-------|--------------|
| dormant | 70,540 | 62.0% | 0.32 |
| success | 36,712 | 32.2% | 0.32 |
| failure | 6,611 | 5.8% | 0.32 |

**Top drivers (RF importance + logistic coefficient)**

- <span style="color:green">**execution_dataset=collection_scoped**</span> — RF **0.174**, LR **+0.346** (success-leaning)
- <span style="color:green">**functional_archetype=monitor**</span> — RF **0.090**, LR **+0.218** (success-leaning)
- <span style="color:green">**execution_dataset=collection_unbounded**</span> — RF **0.047**, LR **+0.228** (success-leaning)
- <span style="color:green">**data_flow_direction=outbound**</span> — RF **0.041**, LR **+0.001** (success-leaning)
- <span style="color:green">**operational_scope=multi_workflow_orchestration**</span> — RF **0.034**, LR **+0.155** (success-leaning)
- <span style="color:#c00">**functional_archetype=creator**</span> — RF **0.134**, LR **-0.200** (failure-leaning)
- <span style="color:#c00">**execution_dataset=single_user_prompt**</span> — RF **0.069**, LR **-0.273** (failure-leaning)
- <span style="color:#c00">**output_modality=visual_image**</span> — RF **0.036**, LR **-0.202** (failure-leaning)
- <span style="color:#c00">**domain_industry_vertical=creative_design**</span> — RF **0.035**, LR **-0.190** (failure-leaning)
- <span style="color:#c00">**execution_dataset=single_event_data**</span> — RF **0.031**, LR **-0.068** (failure-leaning)

---

## SHAP beeswarm

**How to read the beeswarm**

- **Each row** is one one-hot **prompt classification** feature.
- **Horizontal position** is **SHAP** impact on the success score (right = higher predicted success for that agent).
- **Color** encodes the **feature value** (present vs absent for that one-hot column).
- **Density** of dots shows how many agents land at each impact.

![SHAP beeswarm – prompts-only](../analysis/output/classification_prompts_only_shap_beeswarm.png)

---

## Correlation matrix explorer

*Interactive heatmap selector is in the HTML readout.* Run `python analysis/full_feature_readout_analysis.py` to generate matrix PNGs under `analysis/output/`.

## Highlighted correlations

- **functional_archetype=creator** × **todo_write** — *r* = **-0.40** — Lower rate of todo_write among agents with functional_archetype=creator (co-movement; not causal).
- **execution_dataset=collection_scoped** × **retrieve_tasks_by_filters** — *r* = **0.38** — Higher rate of retrieve_tasks_by_filters among agents with execution_dataset=collection_scoped (co-movement; not causal).
- **external_integration_scope=web_research_integration** × **search_public_web** — *r* = **0.38** — Higher rate of search_public_web among agents with external_integration_scope=web_research_integration (co-movement; not causal).
- **execution_dataset=collection_scoped** × **trigger=scheduled** — *r* = **0.38** — Higher rate of trigger=scheduled among agents with execution_dataset=collection_scoped (co-movement; not causal).
- **functional_archetype=monitor** × **trigger=scheduled** — *r* = **0.37** — Higher rate of trigger=scheduled among agents with functional_archetype=monitor (co-movement; not causal).
- **execution_dataset=collection_scoped** × **todo_write** — *r* = **0.37** — Higher rate of todo_write among agents with execution_dataset=collection_scoped (co-movement; not causal).
- **output_modality=structured_document** × **create_document** — *r* = **0.36** — Higher rate of create_document among agents with output_modality=structured_document (co-movement; not causal).

---

## Other classification dimensions

### 3. Domain knowledge depth

**Classification**  
How much specialized field expertise is baked into the prompt (generic vs craft knowledge vs formal processes).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| deep | Formal procedural knowledge; lifecycle, compliance. | 5,120 | 449 | 3,084 | 0.36 | — | — | <span style="color:green">domain_industry_vertical=legal_compliance 0.32</span>; <span style="color:green">use_case_context=specific_use_case 0.21</span>; <span style="color:green">functional_archetype=enforcer 0.14</span> | <span style="color:#c00">use_case_context=general_productivity -0.19</span>; <span style="color:#c00">tone_and_persona=casual_friendly -0.14</span>; <span style="color:#c00">domain_industry_vertical=creative_design -0.10</span> |
| light | Domain is the setting, not the skill. | 18,570 | 3,444 | 16,673 | 0.43 | <span style="color:green">todo_write 0.21</span>; <span style="color:green">retrieve_tasks_by_filters 0.19</span>; <span style="color:green">retrieve_activity 0.16</span> | <span style="color:#c00">post_reply -0.17</span> | <span style="color:green">domain_industry_vertical=project_management_ops 0.50</span>; <span style="color:green">use_case_context=general_productivity 0.38</span>; <span style="color:green">data_flow_direction=processing 0.32</span> | <span style="color:#c00">functional_archetype=creator -0.38</span>; <span style="color:#c00">data_flow_direction=outbound -0.36</span>; <span style="color:#c00">use_case_context=specific_use_case -0.25</span> |
| moderate | Domain craft knowledge essential; techniques, frameworks. | 41,878 | 1,830 | 12,405 | 0.22 | <span style="color:green">post_reply 0.22</span> | <span style="color:#c00">todo_write -0.25</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.24</span>; <span style="color:#c00">retrieve_activity -0.17</span> | <span style="color:green">functional_archetype=creator 0.49</span>; <span style="color:green">data_flow_direction=outbound 0.45</span>; <span style="color:green">domain_industry_vertical=marketing_content 0.29</span> | <span style="color:#c00">domain_industry_vertical=project_management_ops -0.54</span>; <span style="color:#c00">use_case_context=general_productivity -0.44</span>; <span style="color:#c00">data_flow_direction=processing -0.41</span> |
| none | Generic instructions only; no domain references. | 4,962 | 885 | 4,544 | 0.44 | <span style="color:green">retrieve_personal_priorities 0.20</span>; <span style="color:green">retrieve_tasks_by_filters 0.13</span>; <span style="color:green">post_chat_message 0.12</span> | — | <span style="color:green">use_case_context=general_productivity 0.32</span>; <span style="color:green">execution_dataset=collection_unbounded 0.22</span>; <span style="color:green">domain_industry_vertical=project_management_ops 0.20</span> | <span style="color:#c00">use_case_context=specific_use_case -0.27</span>; <span style="color:#c00">functional_archetype=creator -0.16</span>; <span style="color:#c00">data_flow_direction=outbound -0.15</span> |
| unknown | Could not be determined. | 10 | 3 | 6 | 0.32 | — | — | <span style="color:green">domain_industry_vertical=unknown 0.77</span>; <span style="color:green">functional_archetype=unknown 0.40</span>; <span style="color:green">data_flow_direction=unknown 0.31</span> | <span style="color:#c00">implied_end_date=false -0.06</span>; <span style="color:#c00">team_orientation=individual -0.06</span> |

![Domain knowledge depth distribution](../analysis/output/classification_dim_domain_knowledge_depth_bar.png)

**Inference:** Moderate is the most common but has the lowest success rate (22%). Light and none have the highest success rates (~43–44%). Deeper domain depth in the prompt is associated with lower success in raw counts.

**Direction (success vs fail)**

- **Population:** Success rate highest for none and light (~0.43–0.44); lowest for moderate (0.22).
- **Prompts-only model:** <span style="color:#c00">domain_knowledge_depth=moderate</span> has notable RF importance (0.022) and negative logistic coefficient (−0.044); <span style="color:green">domain_knowledge_depth=light</span> is positive (+0.035). So moderate pushes toward failure, light toward success, consistent with population.

**Correlation with tools, triggers, templates**  
See table above. Moderate may correlate with trigger=introduction or creator-heavy tools; light/none with scheduled and task-retrieval tools.

**Other insights**  
Agents with moderate domain depth dominate the cohort but underperform; simplifying or clarifying prompts (e.g. toward light) may be worth testing.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 4. Operational scope

**Classification**  
How complex the agent's workflow is per run (one action vs linear pipeline vs branching vs multiple workflows).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| branching_workflow | Core logic diverges by input or business rules. | 42,705 | 4,002 | 23,223 | 0.33 | — | — | <span style="color:green">execution_dataset=single_event_data 0.13</span>; <span style="color:green">tone_and_persona=casual_friendly 0.09</span>; <span style="color:green">data_flow_direction=processing 0.09</span> | <span style="color:#c00">execution_dataset=single_asset_from_user -0.15</span>; <span style="color:#c00">output_modality=structured_document -0.11</span>; <span style="color:#c00">tone_and_persona=unknown -0.08</span> |
| multi_workflow_orchestration | Two or more independent sub-workflows. | 3,503 | 820 | 6,095 | 0.59 | <span style="color:green">todo_write 0.16</span>; <span style="color:green">retrieve_tasks_by_filters 0.15</span>; <span style="color:green">read_memory 0.15</span> | <span style="color:#c00">post_reply -0.14</span> | <span style="color:green">execution_dataset=collection_scoped 0.23</span>; <span style="color:green">data_flow_direction=bidirectional 0.19</span>; <span style="color:green">functional_archetype=organizer 0.17</span> | <span style="color:#c00">functional_archetype=creator -0.15</span>; <span style="color:#c00">state_persistence=unknown -0.13</span>; <span style="color:#c00">external_integration_scope=clickup_only -0.13</span> |
| sequential_workflow | Multi-step linear pipeline; guard clauses only. | 23,841 | 1,742 | 7,228 | 0.22 | <span style="color:green">post_reply 0.13</span>; <span style="color:green">create_document 0.06</span> | <span style="color:#c00">retrieve_tasks_by_filters -0.10</span>; <span style="color:#c00">todo_write -0.10</span>; <span style="color:#c00">post_chat_message -0.08</span> | <span style="color:green">execution_dataset=single_asset_from_user 0.22</span>; <span style="color:green">functional_archetype=creator 0.16</span>; <span style="color:green">data_flow_direction=outbound 0.14</span> | <span style="color:#c00">execution_dataset=collection_scoped -0.12</span>; <span style="color:#c00">autonomy_level=human_in_the_loop -0.12</span>; <span style="color:#c00">data_flow_direction=processing -0.10</span> |
| single_action | One discrete action per invocation. | 377 | 30 | 97 | 0.19 | — | — | <span style="color:green">implied_end_date=unknown 0.19</span>; <span style="color:green">autonomy_level=unknown 0.18</span>; <span style="color:green">tone_and_persona=unknown 0.17</span> | <span style="color:#c00">implied_end_date=false -0.09</span> |
| unknown | Could not be determined. | 114 | 17 | 69 | 0.34 | — | — | <span style="color:green">data_flow_direction=unknown 0.93</span>; <span style="color:green">functional_archetype=unknown 0.76</span>; <span style="color:green">autonomy_level=unknown 0.74</span> | <span style="color:#c00">team_orientation=individual -0.16</span>; <span style="color:#c00">implied_end_date=false -0.08</span>; <span style="color:#c00">external_integration_scope=clickup_only -0.07</span> |

![Operational scope distribution](../analysis/output/classification_dim_operational_scope_bar.png)

**Inference:** Multi_workflow_orchestration has the highest success rate (59%) and is a minority; branching is most common with moderate success rate (33%); sequential has the lowest success rate (22%).

**Direction (success vs fail)**

- **Population:** multi_workflow_orchestration (0.59) and branching (0.33) lead; sequential (0.22) and single_action (0.19) trail.
- **Prompts-only model:** <span style="color:green">operational_scope=multi_workflow_orchestration</span> has high RF importance (0.034) and strong positive logistic (+0.155); <span style="color:#c00">operational_scope=sequential_workflow</span> is negative (−0.115). SHAP direction aligns: multi_workflow positive, sequential negative.

**Correlation with tools, triggers, templates**  
See table above. Multi-workflow orchestration correlates with scheduled trigger and task/todo tools; sequential_workflow correlates negatively with those.

**Other insights**  
Orchestration and branching are directionally more successful; simplifying to "sequential" in the prompt may be associated with lower success.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 5. Data flow direction

**Classification**  
Where data moves relative to ClickUp (inbound, processing, outbound, or bidirectional).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| bidirectional | Requires both importing and exporting. | 3,409 | 723 | 3,957 | 0.49 | <span style="color:green">search_google_calendar 0.23</span>; <span style="color:green">view_tools_catalog 0.21</span> | — | <span style="color:green">external_integration_scope=email_integration 0.39</span>; <span style="color:green">external_integration_scope=multiple_external_systems 0.35</span>; <span style="color:green">output_modality=email_external_message 0.30</span> | <span style="color:#c00">external_integration_scope=clickup_only -0.52</span>; <span style="color:#c00">functional_archetype=creator -0.15</span>; <span style="color:#c00">output_modality=visual_image -0.10</span> |
| inbound | Captures external data into ClickUp. | 212 | 45 | 129 | 0.33 | — | — | <span style="color:green">output_modality=task_artifact 0.11</span>; <span style="color:green">functional_archetype=organizer 0.09</span>; <span style="color:green">domain_knowledge_depth=light 0.05</span> | — |
| outbound | Output leaves ClickUp or is new content. | 38,376 | 1,349 | 8,455 | 0.18 | <span style="color:green">post_reply 0.27</span>; <span style="color:green">generate_image 0.18</span> | <span style="color:#c00">todo_write -0.35</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.30</span>; <span style="color:#c00">load_assets -0.20</span> | <span style="color:green">functional_archetype=creator 0.65</span>; <span style="color:green">domain_knowledge_depth=moderate 0.45</span>; <span style="color:green">execution_dataset=single_user_prompt 0.44</span> | <span style="color:#c00">domain_industry_vertical=project_management_ops -0.46</span>; <span style="color:#c00">functional_archetype=organizer -0.44</span>; <span style="color:#c00">domain_knowledge_depth=light -0.36</span> |
| processing | Restructures ClickUp data; output stays in ClickUp. | 28,432 | 4,476 | 24,108 | 0.42 | <span style="color:green">todo_write 0.29</span>; <span style="color:green">retrieve_tasks_by_filters 0.28</span>; <span style="color:green">load_assets 0.19</span> | <span style="color:#c00">post_reply -0.24</span>; <span style="color:#c00">generate_image -0.15</span> | <span style="color:green">domain_industry_vertical=project_management_ops 0.45</span>; <span style="color:green">functional_archetype=organizer 0.34</span>; <span style="color:green">domain_knowledge_depth=light 0.32</span> | <span style="color:#c00">functional_archetype=creator -0.56</span>; <span style="color:#c00">execution_dataset=single_user_prompt -0.41</span>; <span style="color:#c00">domain_knowledge_depth=moderate -0.41</span> |
| unknown | Could not be determined. | 111 | 18 | 63 | 0.33 | — | — | <span style="color:green">operational_scope=unknown 0.93</span>; <span style="color:green">functional_archetype=unknown 0.79</span>; <span style="color:green">autonomy_level=unknown 0.72</span> | <span style="color:#c00">team_orientation=individual -0.16</span>; <span style="color:#c00">implied_end_date=false -0.08</span>; <span style="color:#c00">external_integration_scope=clickup_only -0.07</span> |

![Data flow direction distribution](../analysis/output/classification_dim_data_flow_direction_bar.png)

**Inference:** Outbound is most common but has the lowest success rate (18%). Processing and bidirectional have higher success rates (0.42 and 0.49). Outbound-heavy prompts are associated with lower success in the population.

**Direction (success vs fail)**

- **Population:** Bidirectional (0.49) and processing (0.42) lead; outbound (0.18) trails.
- **Prompts-only model:** data_flow_direction=outbound has high RF importance (0.041) but near-zero logistic; <span style="color:green">data_flow_direction=processing</span> and <span style="color:green">data_flow_direction=bidirectional</span> have small positive coefficients. <span style="color:#c00">data_flow_direction=unknown</span> is negative (−0.04). Direction is mixed; population signal is stronger than model coefficients for outbound.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Outbound-dominant prompts are numerous but underperform; balancing with processing or bidirectional semantics may be worth exploring.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 6. Autonomy level

**Classification**  
Whether the agent asks before acting, acts then reports, or acts silently (consultative, human_in_the_loop, autonomous, enforcer, monitor).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| autonomous | Acts without asking; handles edge cases via rules. | 25,952 | 3,818 | 20,242 | 0.40 | <span style="color:green">todo_write 0.21</span>; <span style="color:green">retrieve_tasks_by_filters 0.17</span>; <span style="color:green">retrieve_activity 0.14</span> | <span style="color:#c00">post_reply -0.18</span> | <span style="color:green">functional_archetype=monitor 0.28</span>; <span style="color:green">data_flow_direction=processing 0.18</span>; <span style="color:green">domain_industry_vertical=project_management_ops 0.15</span> | <span style="color:#c00">execution_dataset=single_user_prompt -0.22</span>; <span style="color:#c00">functional_archetype=creator -0.17</span>; <span style="color:#c00">domain_knowledge_depth=moderate -0.16</span> |
| consultative | Asks user before acting; human gates the action. | 34,320 | 1,466 | 9,130 | 0.20 | <span style="color:green">post_reply 0.24</span> | <span style="color:#c00">todo_write -0.28</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.20</span>; <span style="color:#c00">load_assets -0.14</span> | <span style="color:green">execution_dataset=single_user_prompt 0.35</span>; <span style="color:green">data_flow_direction=outbound 0.30</span>; <span style="color:green">functional_archetype=creator 0.29</span> | <span style="color:#c00">data_flow_direction=processing -0.28</span>; <span style="color:#c00">functional_archetype=monitor -0.22</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.21</span> |
| human_in_the_loop | Acts first, then reports for human review. | 10,070 | 1,294 | 7,222 | 0.39 | <span style="color:green">load_assets 0.10</span> | — | <span style="color:green">functional_archetype=organizer 0.23</span>; <span style="color:green">operational_scope=multi_workflow_orchestration 0.16</span>; <span style="color:green">output_modality=task_artifact 0.14</span> | <span style="color:#c00">data_flow_direction=outbound -0.18</span>; <span style="color:#c00">execution_dataset=single_user_prompt -0.16</span>; <span style="color:#c00">functional_archetype=creator -0.15</span> |
| unknown | Could not be determined. | 198 | 33 | 118 | 0.34 | — | — | <span style="color:green">operational_scope=unknown 0.74</span>; <span style="color:green">data_flow_direction=unknown 0.72</span>; <span style="color:green">functional_archetype=unknown 0.58</span> | <span style="color:#c00">team_orientation=individual -0.19</span>; <span style="color:#c00">implied_end_date=false -0.10</span>; <span style="color:#c00">operational_scope=branching_workflow -0.07</span> |

![Autonomy level distribution](../analysis/output/classification_dim_autonomy_level_bar.png)

**Inference:** Consultative is most common but has the lowest success rate (20%). Autonomous and human_in_the_loop have higher success rates (~0.39–0.40). More autonomous prompts associate with higher success.

**Direction (success vs fail)**

- **Population:** Autonomous and human_in_the_loop ~0.39–0.40; consultative 0.20.
- **Prompts-only model:** <span style="color:#c00">autonomy_level=consultative</span> has negative coefficient (−0.09); <span style="color:green">autonomy_level=autonomous</span> positive (+0.08). RF importance: consultative (0.023), autonomous (0.011). Direction aligns: consultative toward failure, autonomous toward success.

**Correlation with tools, triggers, templates**  
See table above. Consultative correlates with introduction or low automation; autonomous with scheduled and task/memory tools.

**Other insights**  
Consultative framing may reduce success; encouraging clearer autonomous or human-in-the-loop patterns in prompts could help.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 7. Tone and persona

**Classification**  
Communication style (professional_formal, casual_friendly, technical_precise, empathetic_supportive).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| casual_friendly | Warm, conversational, approachable. | 25,901 | 1,311 | 9,438 | 0.26 | <span style="color:green">post_reply 0.10</span>; <span style="color:green">edit_image 0.09</span> | <span style="color:#c00">todo_write -0.13</span>; <span style="color:#c00">load_assets -0.12</span>; <span style="color:#c00">load_custom_fields -0.08</span> | <span style="color:green">domain_industry_vertical=creative_design 0.24</span>; <span style="color:green">output_modality=visual_image 0.22</span>; <span style="color:green">functional_archetype=creator 0.20</span> | <span style="color:#c00">data_flow_direction=processing -0.15</span>; <span style="color:#c00">domain_knowledge_depth=deep -0.14</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.14</span> |
| empathetic_supportive | Encouraging, coaching, patient. | 8,340 | 448 | 3,366 | 0.28 | — | — | <span style="color:green">use_case_context=personal_use_case 0.35</span>; <span style="color:green">domain_industry_vertical=education_academic 0.33</span>; <span style="color:green">domain_industry_vertical=personal_productivity 0.16</span> | <span style="color:#c00">domain_industry_vertical=project_management_ops -0.17</span>; <span style="color:#c00">use_case_context=general_productivity -0.14</span>; <span style="color:#c00">use_case_context=specific_use_case -0.14</span> |
| professional_formal | Concise, structured, executive-ready. | 30,774 | 4,108 | 20,853 | 0.37 | <span style="color:green">todo_write 0.14</span>; <span style="color:green">load_assets 0.12</span>; <span style="color:green">retrieve_tasks_by_filters 0.09</span> | <span style="color:#c00">post_reply -0.10</span>; <span style="color:#c00">generate_image -0.07</span> | <span style="color:green">domain_industry_vertical=project_management_ops 0.25</span>; <span style="color:green">data_flow_direction=processing 0.20</span>; <span style="color:green">use_case_context=specific_use_case 0.16</span> | <span style="color:#c00">functional_archetype=creator -0.24</span>; <span style="color:#c00">use_case_context=personal_use_case -0.23</span>; <span style="color:#c00">data_flow_direction=outbound -0.23</span> |
| technical_precise | Data-driven, rigorous, systematic. | 4,681 | 560 | 2,427 | 0.32 | — | — | <span style="color:green">domain_industry_vertical=it_engineering 0.23</span>; <span style="color:green">functional_archetype=analyzer 0.10</span>; <span style="color:green">domain_knowledge_depth=deep 0.08</span> | <span style="color:#c00">operational_scope=branching_workflow -0.06</span>; <span style="color:#c00">domain_knowledge_depth=none -0.05</span>; <span style="color:#c00">domain_industry_vertical=education_academic -0.05</span> |
| unknown | Could not be determined. | 844 | 184 | 628 | 0.38 | — | — | <span style="color:green">autonomy_level=unknown 0.18</span>; <span style="color:green">operational_scope=single_action 0.17</span>; <span style="color:green">team_orientation=unknown 0.16</span> | <span style="color:#c00">operational_scope=branching_workflow -0.08</span>; <span style="color:#c00">implied_end_date=false -0.08</span>; <span style="color:#c00">team_orientation=individual -0.06</span> |

![Tone and persona distribution](../analysis/output/classification_dim_tone_and_persona_bar.png)

**Inference:** Professional_formal and casual_friendly dominate. Professional_formal has the highest success rate among the main categories (0.37); casual_friendly and empathetic_supportive are lower (~0.26–0.28).

**Direction (success vs fail)**

- **Population:** professional_formal (0.37) leads; casual_friendly (0.26) and empathetic_supportive (0.28) trail.
- **Prompts-only model:** RF importance is low for tone (~0.001–0.003). Logistic: <span style="color:#c00">tone_and_persona=casual_friendly</span> −0.04, <span style="color:green">tone_and_persona=professional_formal</span> +0.01, technical_precise +0.01, empathetic_supportive +0.01. Tone has modest directional signal.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Tone is a weaker driver than archetype or scope; formal tone is slightly associated with higher success.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 8. Domain industry vertical

**Classification**  
Which industry or functional area the agent serves (PM, sales, marketing, HR, legal, finance, education, personal, creative, engineering, general).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| creative_design | Graphic design, UI/UX, image generation, video. | 15,044 | 182 | 1,034 | 0.06 | <span style="color:green">edit_image 0.26</span>; <span style="color:green">generate_image 0.21</span>; <span style="color:green">post_reply 0.18</span> | <span style="color:#c00">todo_write -0.26</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.19</span>; <span style="color:#c00">load_assets -0.15</span> | <span style="color:green">output_modality=visual_image 0.65</span>; <span style="color:green">functional_archetype=creator 0.45</span>; <span style="color:green">data_flow_direction=outbound 0.39</span> | <span style="color:#c00">data_flow_direction=processing -0.33</span>; <span style="color:#c00">output_modality=messages -0.27</span>; <span style="color:#c00">functional_archetype=organizer -0.22</span> |
| education_academic | Teaching, tutoring, coursework, exam prep. | 10,670 | 151 | 1,625 | 0.13 | — | <span style="color:#c00">todo_write -0.15</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.12</span> | <span style="color:green">use_case_context=personal_use_case 0.64</span>; <span style="color:green">tone_and_persona=empathetic_supportive 0.33</span>; <span style="color:green">functional_archetype=creator 0.27</span> | <span style="color:#c00">use_case_context=general_productivity -0.23</span>; <span style="color:#c00">tone_and_persona=professional_formal -0.18</span>; <span style="color:#c00">use_case_context=specific_use_case -0.18</span> |
| finance_accounting | Budgeting, invoicing, financial reporting. | 1,991 | 215 | 1,587 | 0.42 | — | — | <span style="color:green">functional_archetype=analyzer 0.14</span>; <span style="color:green">use_case_context=specific_use_case 0.13</span>; <span style="color:green">domain_knowledge_depth=deep 0.13</span> | <span style="color:#c00">use_case_context=general_productivity -0.13</span>; <span style="color:#c00">functional_archetype=creator -0.09</span>; <span style="color:#c00">domain_knowledge_depth=light -0.08</span> |
| general_cross_functional | General-purpose or no specific vertical. | 5,712 | 308 | 1,996 | 0.25 | — | — | <span style="color:green">external_integration_scope=web_research_integration 0.12</span>; <span style="color:green">functional_archetype=communicator 0.11</span>; <span style="color:green">functional_archetype=analyzer 0.10</span> | <span style="color:#c00">external_integration_scope=clickup_only -0.11</span>; <span style="color:#c00">domain_knowledge_depth=light -0.08</span>; <span style="color:#c00">data_flow_direction=processing -0.06</span> |
| hr_people | Hiring, recruiting, onboarding, performance. | 1,210 | 140 | 764 | 0.36 | — | — | <span style="color:green">use_case_context=specific_use_case 0.09</span>; <span style="color:green">domain_knowledge_depth=deep 0.05</span> | <span style="color:#c00">use_case_context=general_productivity -0.09</span> |
| it_engineering | Software dev, coding, debugging, DevOps. | 3,065 | 208 | 1,135 | 0.26 | — | — | <span style="color:green">tone_and_persona=technical_precise 0.23</span>; <span style="color:green">domain_knowledge_depth=moderate 0.09</span>; <span style="color:green">output_modality=unknown 0.05</span> | <span style="color:#c00">domain_knowledge_depth=light -0.07</span>; <span style="color:#c00">domain_knowledge_depth=none -0.06</span>; <span style="color:#c00">tone_and_persona=professional_formal -0.05</span> |
| legal_compliance | Legal, contracts, compliance, regulatory. | 1,601 | 116 | 847 | 0.33 | — | — | <span style="color:green">domain_knowledge_depth=deep 0.32</span>; <span style="color:green">use_case_context=specific_use_case 0.14</span>; <span style="color:green">tone_and_persona=professional_formal 0.10</span> | <span style="color:#c00">use_case_context=general_productivity -0.11</span>; <span style="color:#c00">tone_and_persona=casual_friendly -0.09</span>; <span style="color:#c00">domain_knowledge_depth=light -0.09</span> |
| marketing_content | Content, social, SEO, campaigns, branding. | 9,869 | 673 | 4,695 | 0.31 | — | — | <span style="color:green">use_case_context=specific_use_case 0.30</span>; <span style="color:green">domain_knowledge_depth=moderate 0.29</span>; <span style="color:green">functional_archetype=creator 0.22</span> | <span style="color:#c00">use_case_context=general_productivity -0.23</span>; <span style="color:#c00">domain_knowledge_depth=light -0.21</span>; <span style="color:#c00">data_flow_direction=processing -0.18</span> |
| personal_productivity | Personal planning, habits, journaling. | 2,059 | 464 | 3,008 | 0.54 | <span style="color:green">retrieve_personal_priorities 0.22</span>; <span style="color:green">search_google_calendar 0.18</span> | — | <span style="color:green">use_case_context=personal_productivity 0.38</span>; <span style="color:green">external_integration_scope=calendar_integration 0.19</span>; <span style="color:green">domain_knowledge_depth=none 0.16</span> | <span style="color:#c00">use_case_context=specific_use_case -0.19</span>; <span style="color:#c00">functional_archetype=creator -0.14</span>; <span style="color:#c00">tone_and_persona=professional_formal -0.13</span> |
| project_management_ops | Projects, sprints, standups, deadlines. | 17,324 | 3,799 | 18,164 | 0.46 | <span style="color:green">todo_write 0.28</span>; <span style="color:green">retrieve_tasks_by_filters 0.26</span>; <span style="color:green">retrieve_activity 0.21</span> | <span style="color:#c00">post_reply -0.23</span>; <span style="color:#c00">generate_image -0.12</span> | <span style="color:green">use_case_context=general_productivity 0.51</span>; <span style="color:green">domain_knowledge_depth=light 0.50</span>; <span style="color:green">data_flow_direction=processing 0.45</span> | <span style="color:#c00">domain_knowledge_depth=moderate -0.54</span>; <span style="color:#c00">functional_archetype=creator -0.50</span>; <span style="color:#c00">data_flow_direction=outbound -0.46</span> |
| sales_crm | Deals, pipeline, leads, CRM, revenue. | 1,980 | 348 | 1,847 | 0.44 | — | — | <span style="color:green">use_case_context=specific_use_case 0.21</span>; <span style="color:green">data_flow_direction=bidirectional 0.08</span>; <span style="color:green">functional_archetype=organizer 0.08</span> | <span style="color:#c00">use_case_context=general_productivity -0.15</span>; <span style="color:#c00">functional_archetype=creator -0.12</span>; <span style="color:#c00">data_flow_direction=outbound -0.07</span> |
| unknown | Could not be determined. | 15 | 7 | 10 | 0.31 | — | — | <span style="color:green">domain_knowledge_depth=unknown 0.77</span>; <span style="color:green">functional_archetype=unknown 0.50</span>; <span style="color:green">data_flow_direction=unknown 0.41</span> | <span style="color:#c00">team_orientation=individual -0.08</span>; <span style="color:#c00">implied_end_date=false -0.07</span> |

![Domain industry vertical distribution](../analysis/output/classification_dim_domain_industry_vertical_bar.png)

**Inference:** creative_design and education_academic have very low success rates (0.06 and 0.13); personal_productivity and project_management_ops are higher (0.54 and 0.46). Vertical strongly differentiates success.

**Direction (success vs fail)**

- **Population:** personal_productivity (0.54), project_management_ops (0.46), sales_crm (0.44), finance_accounting (0.42) lead; creative_design (0.06), education_academic (0.13) trail.
- **Prompts-only model:** <span style="color:#c00">domain_industry_vertical=creative_design</span> has negative coefficient (−0.19), <span style="color:#c00">domain_industry_vertical=education_academic</span> (−0.13); <span style="color:green">domain_industry_vertical=marketing_content</span> (+0.14), <span style="color:green">domain_industry_vertical=personal_productivity</span> (+0.10), <span style="color:green">domain_industry_vertical=project_management_ops</span> (+0.07) positive. RF importance: creative_design (0.035), project_management_ops (0.027).

**Correlation with tools, triggers, templates**  
See table above. Vertical correlates with tool mix (e.g. creative with generate_image, PM with task tools).

**Other insights**  
Creative and education verticals underperform; PM, sales, finance, personal productivity align with success. Vertical-specific onboarding could emphasize successful verticals.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 9. External integration scope

**Classification**  
Extent of integration with systems outside ClickUp (clickup_only, email, calendar, web_research, multiple_external_systems).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| calendar_integration | Integrates with calendar. | 921 | 280 | 1,192 | 0.50 | <span style="color:green">search_google_calendar 0.46</span>; <span style="color:green">create_google_calendar_event 0.27</span>; <span style="color:green">check_calendar_availability 0.17</span> | — | <span style="color:green">data_flow_direction=bidirectional 0.26</span>; <span style="color:green">domain_industry_vertical=personal_productivity 0.19</span>; <span style="color:green">functional_archetype=organizer 0.13</span> | <span style="color:#c00">functional_archetype=creator -0.11</span>; <span style="color:#c00">domain_knowledge_depth=moderate -0.10</span>; <span style="color:#c00">data_flow_direction=outbound -0.08</span> |
| clickup_only | No external integrations; ClickUp only. | 59,726 | 5,186 | 28,713 | 0.31 | — | <span style="color:#c00">search_public_web -0.31</span>; <span style="color:#c00">load_web_pages -0.28</span>; <span style="color:#c00">search_google_calendar -0.23</span> | <span style="color:green">data_flow_direction=processing 0.31</span>; <span style="color:green">output_modality=visual_image 0.14</span>; <span style="color:green">domain_industry_vertical=creative_design 0.13</span> | <span style="color:#c00">data_flow_direction=bidirectional -0.52</span>; <span style="color:#c00">output_modality=email_external_message -0.26</span>; <span style="color:#c00">functional_archetype=communicator -0.16</span> |
| email_integration | Integrates with email. | 1,044 | 326 | 1,468 | 0.52 | <span style="color:green">gmail_create_draft 0.22</span>; <span style="color:green">view_tools_catalog 0.21</span> | — | <span style="color:green">output_modality=email_external_message 0.60</span>; <span style="color:green">data_flow_direction=bidirectional 0.39</span>; <span style="color:green">functional_archetype=communicator 0.30</span> | <span style="color:#c00">data_flow_direction=processing -0.13</span>; <span style="color:#c00">functional_archetype=creator -0.11</span>; <span style="color:#c00">data_flow_direction=outbound -0.07</span> |
| multiple_external_systems | Multiple external systems. | 1,348 | 285 | 1,541 | 0.49 | <span style="color:green">search_google_calendar 0.22</span> | — | <span style="color:green">data_flow_direction=bidirectional 0.35</span>; <span style="color:green">operational_scope=multi_workflow_orchestration 0.17</span>; <span style="color:green">domain_industry_vertical=personal_productivity 0.14</span> | <span style="color:#c00">data_flow_direction=processing -0.14</span>; <span style="color:#c00">functional_archetype=creator -0.07</span>; <span style="color:#c00">output_modality=visual_image -0.06</span> |
| unknown | Could not be determined. | 352 | 133 | 527 | 0.52 | <span style="color:green">post_slack_message 0.30</span> | — | <span style="color:green">operational_scope=unknown 0.37</span>; <span style="color:green">data_flow_direction=unknown 0.37</span>; <span style="color:green">autonomy_level=unknown 0.33</span> | <span style="color:#c00">team_orientation=individual -0.14</span> |
| web_research_integration | Uses web/search or research tools. | 7,149 | 401 | 3,271 | 0.30 | <span style="color:green">search_public_web 0.38</span>; <span style="color:green">load_web_pages 0.35</span> | <span style="color:#c00">retrieve_tasks_by_filters -0.11</span> | <span style="color:green">domain_knowledge_depth=moderate 0.16</span>; <span style="color:green">data_flow_direction=outbound 0.15</span>; <span style="color:green">execution_dataset=single_user_prompt 0.14</span> | <span style="color:#c00">data_flow_direction=processing -0.21</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.19</span>; <span style="color:#c00">use_case_context=general_productivity -0.17</span> |

![External integration scope distribution](../analysis/output/classification_dim_external_integration_scope_bar.png)

**Inference:** clickup_only dominates but has the lowest success rate (0.31). Email, calendar, and multiple_external_systems have higher success rates (0.49–0.52). External integration in the prompt associates with higher success.

**Direction (success vs fail)**

- **Population:** email_integration (0.52), calendar (0.50), multiple_external_systems (0.49) lead; clickup_only (0.31) trails.
- **Prompts-only model:** <span style="color:#c00">external_integration_scope=clickup_only</span> has negative coefficient (−0.05); <span style="color:green">external_integration_scope=web_research_integration</span> (+0.03), <span style="color:green">external_integration_scope=multiple_external_systems</span> (+0.02) positive. RF importance is modest. Direction aligns: clickup_only toward lower success, integrations toward higher.

**Correlation with tools, triggers, templates**  
See table above. Calendar/email scope correlates with calendar/email tools and possibly scheduled trigger.

**Other insights**  
Prompts that imply external integrations (email, calendar, multiple systems) associate with higher success than clickup_only.

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 10. Use case context

**Classification**  
High-level context of how the agent is used (specific workflow, general productivity, personal, entertainment, test_or_placeholder).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| entertainment | Entertainment or non-work. | 404 | 15 | 79 | 0.16 | — | — | <span style="color:green">domain_industry_vertical=creative_design 0.08</span>; <span style="color:green">data_flow_direction=outbound 0.07</span>; <span style="color:green">tone_and_persona=casual_friendly 0.06</span> | <span style="color:#c00">data_flow_direction=processing -0.06</span>; <span style="color:#c00">tone_and_persona=professional_formal -0.05</span> |
| general_productivity | General productivity assistance. | 24,106 | 3,445 | 16,502 | 0.37 | <span style="color:green">retrieve_activity 0.15</span>; <span style="color:green">retrieve_tasks_by_filters 0.14</span>; <span style="color:green">retrieve_personal_priorities 0.13</span> | <span style="color:#c00">post_reply -0.11</span>; <span style="color:#c00">search_public_web -0.10</span> | <span style="color:green">domain_industry_vertical=project_management_ops 0.51</span>; <span style="color:green">domain_knowledge_depth=light 0.38</span>; <span style="color:green">domain_knowledge_depth=none 0.32</span> | <span style="color:#c00">domain_knowledge_depth=moderate -0.44</span>; <span style="color:#c00">domain_industry_vertical=education_academic -0.23</span>; <span style="color:#c00">domain_industry_vertical=marketing_content -0.23</span> |
| personal_productivity | Personal productivity. | 3,327 | 209 | 1,792 | 0.34 | — | — | <span style="color:green">domain_industry_vertical=personal_productivity 0.38</span>; <span style="color:green">tone_and_persona=casual_friendly 0.11</span>; <span style="color:green">domain_industry_vertical=creative_design 0.09</span> | <span style="color:#c00">tone_and_persona=professional_formal -0.15</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.14</span>; <span style="color:#c00">domain_industry_vertical=education_academic -0.07</span> |
| personal_use_case | Personal use (e.g. study, habits). | 12,134 | 232 | 2,932 | 0.19 | <span style="color:green">post_reply 0.12</span> | <span style="color:#c00">todo_write -0.12</span>; <span style="color:#c00">retrieve_tasks_by_filters -0.10</span>; <span style="color:#c00">retrieve_activity -0.09</span> | <span style="color:green">domain_industry_vertical=education_academic 0.64</span>; <span style="color:green">tone_and_persona=empathetic_supportive 0.35</span>; <span style="color:green">functional_archetype=creator 0.22</span> | <span style="color:#c00">domain_industry_vertical=project_management_ops -0.27</span>; <span style="color:#c00">tone_and_persona=professional_formal -0.23</span>; <span style="color:#c00">domain_knowledge_depth=light -0.16</span> |
| specific_use_case | Tied to a specific workflow or business use case. | 30,524 | 2,703 | 15,386 | 0.32 | <span style="color:green">load_assets 0.10</span>; <span style="color:green">load_custom_fields 0.10</span> | <span style="color:#c00">retrieve_personal_priorities -0.12</span>; <span style="color:#c00">post_chat_message -0.10</span> | <span style="color:green">domain_industry_vertical=marketing_content 0.30</span>; <span style="color:green">domain_knowledge_depth=moderate 0.28</span>; <span style="color:green">domain_knowledge_depth=deep 0.21</span> | <span style="color:#c00">domain_knowledge_depth=none -0.27</span>; <span style="color:#c00">domain_knowledge_depth=light -0.25</span>; <span style="color:#c00">domain_industry_vertical=project_management_ops -0.25</span> |
| test_or_placeholder | Test or placeholder agent. | 33 | 2 | 19 | 0.35 | — | — | <span style="color:green">implied_end_date=unknown 0.38</span>; <span style="color:green">domain_industry_vertical=unknown 0.24</span>; <span style="color:green">domain_knowledge_depth=unknown 0.22</span> | <span style="color:#c00">implied_end_date=false -0.08</span> |
| unknown | Could not be determined. | 12 | 5 | 2 | 0.11 | — | — | <span style="color:green">domain_industry_vertical=unknown 0.41</span>; <span style="color:green">implied_end_date=unknown 0.32</span>; <span style="color:green">functional_archetype=unknown 0.31</span> | <span style="color:#c00">implied_end_date=false -0.06</span>; <span style="color:#c00">team_orientation=individual -0.05</span> |

![Use case context distribution](../analysis/output/classification_dim_use_case_context_bar.png)

**Inference:** general_productivity has the highest success rate among main categories (0.37); personal_use_case and entertainment are low (0.19 and 0.16). Specific and general productivity contexts perform moderately.

**Direction (success vs fail)**

- **Population:** general_productivity (0.37) leads; personal_use_case (0.19), entertainment (0.16) trail.
- **Prompts-only model:** <span style="color:#c00">use_case_context=general_productivity</span> has negative coefficient (−0.05); <span style="color:green">use_case_context=personal_use_case</span> (+0.04), <span style="color:green">use_case_context=specific_use_case</span> (+0.02) positive. RF importance is low. Direction is mixed; population and model partially align.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Use case context is a weaker driver; general productivity in the population aligns with higher success despite negative coefficient (confounding with other dimensions possible).

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

### 11. Implied end date

**Classification**  
Whether the agent's use case implies a defined end date (e.g. project end, course end).

**Distribution**

| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |
|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|
| false | No implied end date. | 67,655 | 6,456 | 35,547 | 0.32 | — | — | <span style="color:green">use_case_context=general_productivity 0.11</span>; <span style="color:green">output_modality=messages 0.06</span>; <span style="color:green">operational_scope=branching_workflow 0.06</span> | <span style="color:#c00">use_case_context=personal_use_case -0.13</span>; <span style="color:#c00">autonomy_level=unknown -0.10</span>; <span style="color:#c00">operational_scope=single_action -0.09</span> |
| true | Use case implies an end date. | 2,762 | 143 | 1,130 | 0.28 | — | — | <span style="color:green">use_case_context=personal_use_case 0.13</span>; <span style="color:green">functional_archetype=organizer 0.07</span>; <span style="color:green">domain_industry_vertical=education_academic 0.06</span> | <span style="color:#c00">use_case_context=general_productivity -0.11</span>; <span style="color:#c00">output_modality=messages -0.06</span>; <span style="color:#c00">execution_dataset=single_event_data -0.05</span> |
| unknown | Could not be determined. | 123 | 12 | 35 | 0.21 | — | — | <span style="color:green">use_case_context=test_or_placeholder 0.38</span>; <span style="color:green">domain_industry_vertical=unknown 0.34</span>; <span style="color:green">use_case_context=unknown 0.32</span> | <span style="color:#c00">team_orientation=individual -0.06</span> |

![Implied end date distribution](../analysis/output/classification_dim_implied_end_date_bar.png)

**Inference:** Most agents are false (no implied end date). Success rates are similar (0.28–0.32); implied_end_date has limited differentiation.

**Direction (success vs fail)**

- **Population:** false (0.32) slightly higher than true (0.28).
- **Prompts-only model:** <span style="color:green">implied_end_date=false</span> has small positive coefficient (+0.03); <span style="color:#c00">implied_end_date=true</span> negative (−0.03). RF importance is very low. Dimension has weak directional signal.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Implied end date is a minor lever; most impact comes from other dimensions (execution_dataset, functional_archetype, domain_industry_vertical).

**Footnotes**  
Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.

---

## Methodology and footnotes

### Analytical approach

- **Success:** Used ≥1 after **7** days and still **active**; **failure:** inactive/deleted; **dormant:** active but **no use** after 7 days.
- **Prompts-only model:** Predicts success vs non-success from **one-hot** classification columns only.
- **Heatmaps** use per-dimension slices from `leadership_corr_heatmap_map.json` (run `full_feature_readout_analysis.py`); column set is the full classified build plus tools/triggers/templates.

### Prompts-only model detail
### Prompts-only model summary

This section summarizes **Random Forest importance**, **SHAP direction**, and **Logistic regression coefficients** from the prompts-only model (classification dimensions only). **Green** = feature associated with higher success; **red** = associated with lower success.

**Commentary:** The strongest positive predictors are <span style="color:green">execution_dataset=collection_scoped</span> and <span style="color:green">functional_archetype=monitor</span> (high RF importance and positive coefficients). The strongest negative predictors are <span style="color:#c00">functional_archetype=creator</span>, <span style="color:#c00">execution_dataset=single_user_prompt</span>, and <span style="color:#c00">execution_dataset=single_asset_from_user</span>. <span style="color:green">domain_knowledge_depth=light</span> and <span style="color:#c00">domain_knowledge_depth=moderate</span> are also notable; <span style="color:#c00">domain_industry_vertical=creative_design</span> and <span style="color:#c00">education_academic</span> are negative. Below: top 15 RF features (colored by logistic direction), SHAP beeswarm, and significant logistic coefficients.

**Top 15 features by RF importance (direction from logistic regression)**

| Feature | Importance | Direction |
|---------|------------|-----------|
| execution_dataset=collection_scoped | 0.174 | <span style="color:green">positive</span> |
| functional_archetype=creator | 0.134 | <span style="color:#c00">negative</span> |
| functional_archetype=monitor | 0.090 | <span style="color:green">positive</span> |
| execution_dataset=single_user_prompt | 0.069 | <span style="color:#c00">negative</span> |
| execution_dataset=collection_unbounded | 0.047 | <span style="color:green">positive</span> |
| data_flow_direction=outbound | 0.041 | <span style="color:green">positive</span> |
| output_modality=visual_image | 0.036 | <span style="color:#c00">negative</span> |
| domain_industry_vertical=creative_design | 0.035 | <span style="color:#c00">negative</span> |
| operational_scope=multi_workflow_orchestration | 0.034 | <span style="color:green">positive</span> |
| execution_dataset=single_event_data | 0.031 | <span style="color:#c00">negative</span> |
| execution_dataset=single_asset_from_user | 0.027 | <span style="color:#c00">negative</span> |
| domain_industry_vertical=project_management_ops | 0.027 | <span style="color:green">positive</span> |
| autonomy_level=consultative | 0.023 | <span style="color:#c00">negative</span> |
| domain_knowledge_depth=moderate | 0.022 | <span style="color:#c00">negative</span> |
| data_flow_direction=processing | 0.018 | <span style="color:#c00">negative</span> |

**SHAP beeswarm (prompts-only)**

![SHAP beeswarm](../analysis/output/classification_prompts_only_shap_beeswarm.png)

**Significant logistic coefficients (|coefficient| ≥ 0.05)**

- **Positive (green):** <span style="color:green">execution_dataset=collection_scoped (0.346)</span>; <span style="color:green">execution_dataset=collection_unbounded (0.228)</span>; <span style="color:green">functional_archetype=monitor (0.218)</span>; <span style="color:green">operational_scope=multi_workflow_orchestration (0.155)</span>; <span style="color:green">domain_industry_vertical=marketing_content (0.138)</span>; <span style="color:green">domain_industry_vertical=personal_productivity (0.096)</span>; <span style="color:green">autonomy_level=autonomous (0.083)</span>; <span style="color:green">output_modality=messages (0.082)</span>; <span style="color:green">functional_archetype=communicator (0.079)</span>; <span style="color:green">domain_industry_vertical=project_management_ops (0.073)</span>; <span style="color:green">output_modality=task_artifact (0.072)</span>
- **Negative (red):** <span style="color:#c00">state_persistence=unknown (-0.054)</span>; <span style="color:#c00">execution_dataset=single_event_data (-0.068)</span>; <span style="color:#c00">autonomy_level=consultative (-0.092)</span>; <span style="color:#c00">operational_scope=sequential_workflow (-0.115)</span>; <span style="color:#c00">domain_industry_vertical=education_academic (-0.131)</span>; <span style="color:#c00">domain_industry_vertical=creative_design (-0.190)</span>; <span style="color:#c00">functional_archetype=creator (-0.200)</span>; <span style="color:#c00">output_modality=visual_image (-0.202)</span>; <span style="color:#c00">execution_dataset=single_asset_from_user (-0.258)</span>; <span style="color:#c00">execution_dataset=single_user_prompt (-0.273)</span>


### Success vs failure criteria
- **Parameters:** `analysis_reference_date` (cohort_metadata.yaml); `days_post_creation` = 7.
### Assumptions
- Classified cohort only.
- Correlation is agent-level (primary trigger/template; average tool calls per run).
### Limitations
- **Correlation ≠ causation.**
- Pearson **r**; top pairs in tables typically |r| ≥ **0.05**.
- Tool/trigger/template coverage depends on the agent-level extract.
### Correlation color code (dimension tables)
- **Green** = positive association with that dimension value; **red** = negative.
