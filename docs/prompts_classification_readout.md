# Prompts-only classification readout

**Last updated:** 2026-03-10  
**Scope:** Classification dimensions only (no triggers or tools in the success model). Correlation sections add tools, triggers, and templates for context.  
**Data:** Classified cohort (agents in `agent_classifications.csv` with success_segment from cohort). Success/failure/dormant definitions match the main agent success readout.  
**Value meanings:** See [semantic_layer/models/agent_classifications.md](semantic_layer/models/agent_classifications.md).

---

## 1. Team orientation

**Classification**  
Whether the agent is framed for an individual, small team, or larger team.

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| individual | 68,878 | 6,024 | 33,906 | 0.31 |
| larger_team | 371 | 246 | 1,081 | 0.64 |
| small_team | 941 | 294 | 1,538 | 0.55 |
| unknown | 350 | 47 | 187 | 0.32 |

**What each value means:** *individual* = agent oriented to a single user; *small_team* = small team; *larger_team* = larger team; *unknown* = could not be determined.

**Inference:** Most agents are individual-oriented (majority of cohort). Larger_team and small_team have materially higher success rates (64% and 55%) than individual (31%), suggesting team-oriented prompts are associated with more success in the population.

**Direction (success vs fail)**

- **Population:** Higher success rate for larger_team (0.64) and small_team (0.55); lowest for individual (0.31).
- **Prompts-only model:** RF importance is low for this dimension (team_orientation=individual ~0.004). Logistic: individual −0.02, small_team +0.02, larger_team +0.01. Direction aligns with population: team orientation (small/larger) slightly positive vs individual.

**Correlation with tools, triggers, templates (top positive and negative)**

| Classification feature | External feature | Correlation |
|------------------------|------------------|-------------|
| team_orientation=larger_team | post_chat_message | 0.19 |
| team_orientation=larger_team | search_users_and_teams | 0.13 |
| team_orientation=larger_team | trigger=scheduled | 0.09 |
| team_orientation=individual | post_chat_message | −0.18 |
| team_orientation=individual | search_users_and_teams | −0.13 |
| team_orientation=individual | trigger=scheduled | −0.09 |

**Commentary:** Larger-team agents correlate with post_chat_message and scheduled trigger; individual correlates negatively with those. Suggests team-oriented agents tend to use chat and scheduled runs more than individual-oriented ones.

**Other insights**  
Team-oriented agents are a minority but show stronger success rates; product and onboarding could emphasize team use cases where applicable.

**Footnotes**  
Correlations are agent-level Pearson; primary trigger/template and avg tool usage per run.

---

## 2. Domain knowledge depth

**Classification**  
How much specialized field expertise is baked into the prompt (generic vs craft knowledge vs formal processes).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| moderate | 41,878 | 1,830 | 12,405 | 0.22 |
| light | 18,570 | 3,444 | 16,673 | 0.43 |
| none | 4,962 | 885 | 4,544 | 0.44 |
| deep | 5,120 | 449 | 3,084 | 0.36 |
| unknown | 10 | 3 | 6 | 0.32 |

**What each value means:** *none* = generic only; *light* = domain as setting; *moderate* = domain craft essential; *deep* = formal procedural knowledge; *unknown* = could not be determined.

**Inference:** Moderate is the most common but has the lowest success rate (22%). Light and none have the highest success rates (~43–44%). Deeper domain depth in the prompt is associated with lower success in raw counts.

**Direction (success vs fail)**

- **Population:** Success rate highest for none and light (~0.43–0.44); lowest for moderate (0.22).
- **Prompts-only model:** domain_knowledge_depth=moderate has notable RF importance (0.022) and negative logistic coefficient (−0.044); light is positive (+0.035). So moderate pushes toward failure, light toward success, consistent with population.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_domain_knowledge_depth.csv` for top 10 positive and negative. Report only highly significant: e.g. moderate may correlate with trigger=introduction or creator-heavy tools; light/none with scheduled and task-retrieval tools.

**Other insights**  
Agents with moderate domain depth dominate the cohort but underperform; simplifying or clarifying prompts (e.g. toward light) may be worth testing.

**Footnotes**  
Same as §1.

---

## 3. Operational scope

**Classification**  
How complex the agent's workflow is per run (one action vs linear pipeline vs branching vs multiple workflows).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| branching_workflow | 42,705 | 4,002 | 23,223 | 0.33 |
| sequential_workflow | 23,841 | 1,742 | 7,228 | 0.22 |
| multi_workflow_orchestration | 3,503 | 820 | 6,095 | 0.59 |
| single_action | 377 | 30 | 97 | 0.19 |
| unknown | 114 | 17 | 69 | 0.34 |

**What each value means:** *single_action* = one discrete action per invocation; *sequential_workflow* = multi-step linear pipeline; *branching_workflow* = logic diverges by input/rules; *multi_workflow_orchestration* = two or more independent sub-workflows; *unknown* = could not be determined.

**Inference:** Multi_workflow_orchestration has the highest success rate (59%) and is a minority; branching is most common with moderate success rate (33%); sequential has the lowest success rate (22%).

**Direction (success vs fail)**

- **Population:** multi_workflow_orchestration (0.59) and branching (0.33) lead; sequential (0.22) and single_action (0.19) trail.
- **Prompts-only model:** operational_scope=multi_workflow_orchestration has high RF importance (0.034) and strong positive logistic (+0.155); sequential_workflow is negative (−0.115). SHAP direction aligns: multi_workflow positive, sequential negative.

**Correlation with tools, triggers, templates (top)**

| Classification feature | External feature | Correlation |
|------------------------|------------------|-------------|
| operational_scope=multi_workflow_orchestration | trigger=scheduled | 0.19 |
| operational_scope=multi_workflow_orchestration | todo_write | 0.16 |
| operational_scope=multi_workflow_orchestration | retrieve_tasks_by_filters | 0.15 |
| operational_scope=sequential_workflow | trigger=scheduled | −0.16 |
| operational_scope=multi_workflow_orchestration | post_reply | −0.14 |
| operational_scope=sequential_workflow | retrieve_tasks_by_filters | −0.10 |

**Commentary:** Multi-workflow orchestration correlates with scheduled trigger and task/todo tools; sequential_workflow correlates negatively with those. Suggests orchestration-style prompts pair with scheduled, task-heavy usage.

**Other insights**  
Orchestration and branching are directionally more successful; simplifying to “sequential” in the prompt may be associated with lower success.

**Footnotes**  
Same as §1.

---

## 4. Data flow direction

**Classification**  
Where data moves relative to ClickUp (inbound, processing, outbound, or bidirectional).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| outbound | 38,376 | 1,349 | 8,455 | 0.18 |
| processing | 28,432 | 4,476 | 24,108 | 0.42 |
| bidirectional | 3,409 | 723 | 3,957 | 0.49 |
| inbound | 212 | 45 | 129 | 0.33 |
| unknown | 111 | 18 | 63 | 0.33 |

**What each value means:** *inbound* = captures external data into ClickUp; *processing* = restructures ClickUp data, output stays in ClickUp; *outbound* = output leaves ClickUp or is new content; *bidirectional* = both import and export; *unknown* = could not be determined.

**Inference:** Outbound is most common but has the lowest success rate (18%). Processing and bidirectional have higher success rates (0.42 and 0.49). Outbound-heavy prompts are associated with lower success in the population.

**Direction (success vs fail)**

- **Population:** Bidirectional (0.49) and processing (0.42) lead; outbound (0.18) trails.
- **Prompts-only model:** data_flow_direction=outbound has high RF importance (0.041) but near-zero logistic; processing and bidirectional have small positive coefficients. data_flow_direction=unknown is negative (−0.04). Direction is mixed; population signal is stronger than model coefficients for outbound.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_data_flow_direction.csv`. Top correlations will show which triggers/tools pair with inbound vs outbound vs processing.

**Other insights**  
Outbound-dominant prompts are numerous but underperform; balancing with processing or bidirectional semantics may be worth exploring.

**Footnotes**  
Same as §1.

---

## 5. Autonomy level

**Classification**  
Whether the agent asks before acting, acts then reports, or acts silently (consultative, human_in_the_loop, autonomous, enforcer, monitor).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| consultative | 34,320 | 1,466 | 9,130 | 0.20 |
| autonomous | 25,952 | 3,818 | 20,242 | 0.40 |
| human_in_the_loop | 10,070 | 1,294 | 7,222 | 0.39 |
| unknown | 198 | 33 | 118 | 0.34 |

**What each value means:** *consultative* = asks user before acting; *human_in_the_loop* = acts then reports; *autonomous* = acts without asking; *enforcer* = validates compliance; *monitor* = surfaces alerts; *unknown* = could not be determined.

**Inference:** Consultative is most common but has the lowest success rate (20%). Autonomous and human_in_the_loop have higher success rates (~0.39–0.40). More autonomous prompts associate with higher success.

**Direction (success vs fail)**

- **Population:** Autonomous and human_in_the_loop ~0.39–0.40; consultative 0.20.
- **Prompts-only model:** autonomy_level=consultative has negative coefficient (−0.09); autonomous positive (+0.08). RF importance: consultative (0.023), autonomous (0.011). Direction aligns: consultative toward failure, autonomous toward success.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_autonomy_level.csv`. Expect consultative to correlate with introduction or low automation; autonomous with scheduled and task/memory tools.

**Other insights**  
Consultative framing may reduce success; encouraging clearer autonomous or human-in-the-loop patterns in prompts could help.

**Footnotes**  
Same as §1.

---

## 6. Functional archetype

**Classification**  
The agent's primary job function (creator, organizer, analyzer, communicator, monitor, enforcer).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| creator | 38,672 | 734 | 5,307 | 0.12 |
| organizer | 17,770 | 2,373 | 12,265 | 0.38 |
| analyzer | 6,656 | 867 | 4,884 | 0.39 |
| monitor | 3,297 | 1,750 | 10,049 | 0.67 |
| communicator | 2,129 | 500 | 2,528 | 0.49 |
| enforcer | 1,947 | 375 | 1,640 | 0.41 |
| unknown | 69 | 12 | 39 | 0.32 |

**What each value means:** *communicator* = drafts/sends messages; *analyzer* = insights/metrics; *organizer* = structures/routes work; *creator* = generates content; *monitor* = observes/reports; *enforcer* = enforces rules; *unknown* = could not be determined.

**Inference:** Creator is the most common but has the lowest success rate (12%). Monitor has the highest success rate (67%). Organizer and analyzer are common with moderate success (~0.38–0.39).

**Direction (success vs fail)**

- **Population:** Monitor (0.67) and communicator (0.49) lead; creator (0.12) trails.
- **Prompts-only model:** functional_archetype=creator has high importance (0.134) and strong negative coefficient (−0.20); monitor has high importance (0.090) and strong positive coefficient (+0.22). Creator pushes toward failure, monitor toward success.

**Correlation with tools, triggers, templates (top)**

| Classification feature | External feature | Correlation |
|------------------------|------------------|-------------|
| functional_archetype=monitor | trigger=scheduled | 0.37 |
| functional_archetype=monitor | retrieve_tasks_by_filters | 0.36 |
| functional_archetype=creator | post_reply | 0.33 |
| functional_archetype=monitor | todo_write | 0.33 |
| functional_archetype=creator | trigger=scheduled | −0.40 |
| functional_archetype=creator | todo_write | −0.40 |
| functional_archetype=creator | retrieve_tasks_by_filters | −0.36 |

**Commentary:** Monitor strongly correlates with scheduled trigger and task/todo tools; creator correlates negatively with those and positively with post_reply and introduction. Monitor-style prompts align with scheduled, task-heavy usage; creator with reply/introduction.

**Other insights**  
Creator-heavy prompts dominate but underperform; monitor and communicator are strong success levers. Product could favor monitor/communicator patterns where appropriate.

**Footnotes**  
Same as §1.

---

## 7. Tone and persona

**Classification**  
Communication style (professional_formal, casual_friendly, technical_precise, empathetic_supportive).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| professional_formal | 30,774 | 4,108 | 20,853 | 0.37 |
| casual_friendly | 25,901 | 1,311 | 9,438 | 0.26 |
| technical_precise | 4,681 | 560 | 2,427 | 0.32 |
| empathetic_supportive | 8,340 | 448 | 3,366 | 0.28 |
| unknown | 844 | 184 | 628 | 0.38 |

**What each value means:** *professional_formal* = concise, executive-ready; *casual_friendly* = warm, conversational; *technical_precise* = data-driven, systematic; *empathetic_supportive* = encouraging, coaching; *unknown* = could not be determined.

**Inference:** Professional_formal and casual_friendly dominate. Professional_formal has the highest success rate among the main categories (0.37); casual_friendly and empathetic_supportive are lower (~0.26–0.28).

**Direction (success vs fail)**

- **Population:** professional_formal (0.37) leads; casual_friendly (0.26) and empathetic_supportive (0.28) trail.
- **Prompts-only model:** RF importance is low for tone (~0.001–0.003). Logistic: casual_friendly −0.04, professional_formal +0.01, technical_precise +0.01, empathetic_supportive +0.01. Tone has modest directional signal.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_tone_and_persona.csv`.

**Other insights**  
Tone is a weaker driver than archetype or scope; formal tone is slightly associated with higher success.

**Footnotes**  
Same as §1.

---

## 8. Execution dataset

**Classification**  
What the agent works on per invocation (single event, user prompt, asset, collection_scoped, collection_unbounded, messages).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| single_user_prompt | 25,106 | 594 | 3,061 | 0.11 |
| single_event_data | 19,695 | 1,529 | 7,100 | 0.25 |
| single_asset_from_user | 10,795 | 194 | 999 | 0.08 |
| collection_scoped | 11,213 | 3,125 | 18,728 | 0.57 |
| collection_unbounded | 3,458 | 1,134 | 6,593 | 0.59 |
| unknown | 273 | 35 | 231 | 0.43 |

**What each value means:** *single_event_data* = one automation event; *single_user_prompt* = user request, agent creates; *single_asset_from_user* = user provides material; *collection_scoped* = defined scope (lists, time windows); *collection_unbounded* = broad search; *messages* = comments/DMs; *unknown* = could not be determined.

**Inference:** single_user_prompt and single_asset_from_user have very low success rates (0.11 and 0.08). collection_scoped and collection_unbounded have the highest (0.57 and 0.59). Collection-based execution is strongly associated with success.

**Direction (success vs fail)**

- **Population:** collection_scoped (0.57) and collection_unbounded (0.59) lead; single_user_prompt (0.11) and single_asset_from_user (0.08) trail.
- **Prompts-only model:** execution_dataset=collection_scoped has the highest RF importance (0.174) and strong positive coefficient (+0.35); single_user_prompt and single_asset_from_user are strongly negative (−0.27, −0.26). Direction is very clear: collection-scoped toward success, single-user-prompt/asset toward failure.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_execution_dataset.csv`. Expect collection_scoped to correlate with scheduled and task/retrieval tools; single_user_prompt with introduction.

**Other insights**  
Execution dataset is one of the strongest predictors. Shifting prompts toward collection-scoped or unbounded semantics and away from single-user-prompt/asset may improve success.

**Footnotes**  
Same as §1.

---

## 9. Output modality

**Classification**  
Type of artifact the agent primarily produces (structured_document, task_artifact, visual_image, email_external_message, messages).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| messages | 29,874 | 4,204 | 23,490 | 0.41 |
| visual_image | 14,222 | 175 | 726 | 0.05 |
| structured_document | 12,575 | 689 | 4,206 | 0.24 |
| task_artifact | 12,149 | 1,291 | 6,963 | 0.34 |
| email_external_message | 670 | 168 | 879 | 0.51 |
| unknown | 1,050 | 84 | 448 | 0.28 |

**What each value means:** *structured_document* = Docs/Doc Pages; *task_artifact* = tasks, subtasks, checklists; *visual_image* = AI-generated images; *email_external_message* = email or external messages; *messages* = comments, DMs; *unknown* = could not be determined.

**Inference:** visual_image has the lowest success rate (5%); messages and email_external_message are higher (0.41 and 0.51). Image-heavy output modality is strongly associated with lower success.

**Direction (success vs fail)**

- **Population:** email_external_message (0.51) and messages (0.41) lead; visual_image (0.05) trails.
- **Prompts-only model:** output_modality=visual_image has high importance (0.036) and strong negative coefficient (−0.20); messages and task_artifact are positive (+0.08, +0.07). Visual_image pushes toward failure; messages/task_artifact toward success.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_output_modality.csv`. Expect visual_image to correlate with generate_image and possibly introduction; messages with post_chat_message, post_reply.

**Other insights**  
Prompts framed around visual image generation underperform; message- and task-oriented outputs align with success.

**Footnotes**  
Same as §1.

---

## 10. Domain industry vertical

**Classification**  
Which industry or functional area the agent serves (PM, sales, marketing, HR, legal, finance, education, personal, creative, engineering, general).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| creative_design | 15,044 | 182 | 1,034 | 0.06 |
| education_academic | 10,670 | 151 | 1,625 | 0.13 |
| marketing_content | 9,869 | 673 | 4,695 | 0.31 |
| project_management_ops | 17,324 | 3,799 | 18,164 | 0.46 |
| personal_productivity | 2,059 | 464 | 3,008 | 0.54 |
| finance_accounting | 1,991 | 215 | 1,587 | 0.42 |
| sales_crm | 1,980 | 348 | 1,847 | 0.44 |
| general_cross_functional | 5,712 | 308 | 1,996 | 0.25 |
| hr_people | 1,210 | 140 | 764 | 0.36 |
| it_engineering | 3,065 | 208 | 1,135 | 0.26 |
| legal_compliance | 1,601 | 116 | 847 | 0.33 |
| unknown | 15 | 7 | 10 | 0.31 |

**What each value means:** See [agent_classifications.md](semantic_layer/models/agent_classifications.md) for full option list (project_management_ops, sales_crm, marketing_content, hr_people, legal_compliance, finance_accounting, education_academic, personal_productivity, creative_design, it_engineering, general_cross_functional, unknown).

**Inference:** creative_design and education_academic have very low success rates (0.06 and 0.13); personal_productivity and project_management_ops are higher (0.54 and 0.46). Vertical strongly differentiates success.

**Direction (success vs fail)**

- **Population:** personal_productivity (0.54), project_management_ops (0.46), sales_crm (0.44), finance_accounting (0.42) lead; creative_design (0.06), education_academic (0.13) trail.
- **Prompts-only model:** domain_industry_vertical=creative_design has negative coefficient (−0.19), education_academic (−0.13); marketing_content (+0.14), personal_productivity (+0.10), project_management_ops (+0.07) positive. RF importance: creative_design (0.035), project_management_ops (0.027).

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_domain_industry_vertical.csv`. Vertical will correlate with tool mix (e.g. creative with generate_image, PM with task tools).

**Other insights**  
Creative and education verticals underperform; PM, sales, finance, personal productivity align with success. Vertical-specific onboarding could emphasize successful verticals.

**Footnotes**  
Same as §1.

---

## 11. State persistence

**Classification**  
Whether and how the agent keeps state across invocations (stateless, state_referencing, state_accumulating).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| unknown | 58,887 | 5,415 | 28,801 | 0.31 |
| state_accumulating | 6,867 | 764 | 5,487 | 0.42 |
| state_referencing | 4,538 | 408 | 2,332 | 0.32 |
| stateless | 248 | 24 | 92 | 0.25 |

**What each value means:** *stateless* = no state across calls; *state_referencing* = references existing state, does not accumulate; *state_accumulating* = accumulates state across invocations; *unknown* = could not be determined.

**Inference:** Most agents are unknown for this dimension. state_accumulating has the highest success rate (0.42); stateless the lowest (0.25). State-accumulating prompts associate with higher success.

**Direction (success vs fail)**

- **Population:** state_accumulating (0.42) leads; stateless (0.25) trails.
- **Prompts-only model:** state_persistence=state_accumulating has positive coefficient (+0.05); state_referencing (+0.02); unknown negative (−0.05). RF importance is low. Direction aligns: state_accumulating toward success.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_state_persistence.csv`.

**Other insights**  
State semantics are a weaker lever; clarifying state_accumulating in prompts may still help where applicable.

**Footnotes**  
Same as §1.

---

## 12. External integration scope

**Classification**  
Extent of integration with systems outside ClickUp (clickup_only, email, calendar, web_research, multiple_external_systems).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| clickup_only | 59,726 | 5,186 | 28,713 | 0.31 |
| web_research_integration | 7,149 | 401 | 3,271 | 0.30 |
| multiple_external_systems | 1,348 | 285 | 1,541 | 0.49 |
| email_integration | 1,044 | 326 | 1,468 | 0.52 |
| calendar_integration | 921 | 280 | 1,192 | 0.50 |
| unknown | 352 | 133 | 527 | 0.52 |

**What each value means:** *clickup_only* = no external integrations; *email_integration* = email; *calendar_integration* = calendar; *web_research_integration* = web/search; *multiple_external_systems* = multiple systems; *unknown* = could not be determined.

**Inference:** clickup_only dominates but has the lowest success rate (0.31). Email, calendar, and multiple_external_systems have higher success rates (0.49–0.52). External integration in the prompt associates with higher success.

**Direction (success vs fail)**

- **Population:** email_integration (0.52), calendar (0.50), multiple_external_systems (0.49) lead; clickup_only (0.31) trails.
- **Prompts-only model:** external_integration_scope=clickup_only has negative coefficient (−0.05); web_research_integration (+0.03), multiple_external_systems (+0.02) positive. RF importance is modest. Direction aligns: clickup_only toward lower success, integrations toward higher.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_external_integration_scope.csv`. Expect calendar/email scope to correlate with calendar/email tools and possibly scheduled trigger.

**Other insights**  
Prompts that imply external integrations (email, calendar, multiple systems) associate with higher success than clickup_only.

**Footnotes**  
Same as §1.

---

## 13. Use case context

**Classification**  
High-level context of how the agent is used (specific workflow, general productivity, personal, entertainment, test_or_placeholder).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| specific_use_case | 30,524 | 2,703 | 15,386 | 0.32 |
| general_productivity | 24,106 | 3,445 | 16,502 | 0.37 |
| personal_use_case | 12,134 | 232 | 2,932 | 0.19 |
| personal_productivity | 3,327 | 209 | 1,792 | 0.34 |
| entertainment | 404 | 15 | 79 | 0.16 |
| test_or_placeholder | 33 | 2 | 19 | 0.35 |
| unknown | 12 | 5 | 2 | 0.11 |

**What each value means:** *specific_use_case* = specific workflow/business use case; *general_productivity* = general productivity; *personal_use_case* = personal (e.g. study, habits); *personal_productivity* = personal productivity; *entertainment* = non-work; *test_or_placeholder* = test/placeholder; *unknown* = could not be determined.

**Inference:** general_productivity has the highest success rate among main categories (0.37); personal_use_case and entertainment are low (0.19 and 0.16). Specific and general productivity contexts perform moderately.

**Direction (success vs fail)**

- **Population:** general_productivity (0.37) leads; personal_use_case (0.19), entertainment (0.16) trail.
- **Prompts-only model:** use_case_context=general_productivity has negative coefficient (−0.05); personal_use_case (+0.04), specific_use_case (+0.02) positive. RF importance is low. Direction is mixed; population and model partially align.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_use_case_context.csv`.

**Other insights**  
Use case context is a weaker driver; general productivity in the population aligns with higher success despite negative coefficient (confounding with other dimensions possible).

**Footnotes**  
Same as §1.

---

## 14. Implied end date

**Classification**  
Whether the agent's use case implies a defined end date (e.g. project end, course end).

**Distribution**

| Value | Dormant | Failure | Success | Success rate |
|-------|---------|---------|---------|--------------|
| false | 67,655 | 6,456 | 35,547 | 0.32 |
| true | 2,762 | 143 | 1,130 | 0.28 |
| unknown | 123 | 12 | 35 | 0.21 |

**What each value means:** *true* = use case implies an end date; *false* = no implied end date; *unknown* = could not be determined.

**Inference:** Most agents are false (no implied end date). Success rates are similar (0.28–0.32); implied_end_date has limited differentiation.

**Direction (success vs fail)**

- **Population:** false (0.32) slightly higher than true (0.28).
- **Prompts-only model:** implied_end_date=false has small positive coefficient (+0.03); true negative (−0.03). RF importance is very low. Dimension has weak directional signal.

**Correlation with tools, triggers, templates**  
See `analysis/output/prompts_readout_correlation_implied_end_date.csv`.

**Other insights**  
Implied end date is a minor lever; most impact comes from other dimensions (execution_dataset, functional_archetype, domain_industry_vertical).

**Footnotes**  
Same as §1.

---

## Document-level footnotes

**Success vs failure criteria**  
- **Success:** After 7 days of creation, the agent has been used at least once and is still **active** as of the analysis date.  
- **Failure:** Agent is **inactive** and/or **deleted**.  
- **Dormant:** Created, not deleted, **active**, but **no usage post 7 days** of creation.  
- **Parameters:** analysis_reference_date (see cohort_metadata.yaml); days_post_creation = 7.

**Assumptions**  
- Classified cohort only (agents in agent_classifications.csv).  
- Prompts-only model excludes trigger and template; direction (RF/SHAP/logistic) is from this model.  
- Correlation is agent-level: primary trigger and primary template from runs; tool usage = average calls per run per tool.  
- Value meanings and option lists from [agent_classifications.md](semantic_layer/models/agent_classifications.md).

**Limitations**  
- Correlation does not imply causation.  
- Pearson correlation used for consistency; one-hot encoding for classification dimensions.  
- Top correlations are by magnitude; statistical significance (e.g. p-values) can be added in a future run.  
- Tools/triggers/templates in the correlation dataset are limited to those available in the agent-level build (same as in the main analysis pipeline).
