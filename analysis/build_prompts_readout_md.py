#!/usr/bin/env python3
"""Build the prompts classification readout markdown and HTML: 11 dimensions, reordered, with new distribution tables and bar charts."""
import html
import re
import numpy as np
import pandas as pd
from pathlib import Path

from _utils import OUTPUT_DIR

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

# Order: 1=functional_archetype, 2=execution_dataset, ... 11=implied_end_date
DIMS_ORDER = [
    "functional_archetype", "execution_dataset", "domain_knowledge_depth", "operational_scope",
    "data_flow_direction", "autonomy_level", "tone_and_persona", "domain_industry_vertical",
    "external_integration_scope", "use_case_context", "implied_end_date",
]

# Clear one-line definitions per value (from semantic_layer/models/agent_classifications.md)
DEFINITIONS = {
    "functional_archetype": {
        "communicator": "Drafts and sends messages (emails, DMs, notifications).",
        "analyzer": "Produces insights, metrics, or recommendations from data.",
        "organizer": "Structures, routes, or categorizes existing work items.",
        "creator": "Generates new content (writing, images, docs, code).",
        "monitor": "Observes and reports; does not create or enforce.",
        "enforcer": "Enforces rules, compliance, or corrections.",
        "unknown": "Could not be determined.",
    },
    "execution_dataset": {
        "single_event_data": "Triggered by one ClickUp automation event.",
        "single_user_prompt": "User sends a request; agent creates in response.",
        "single_asset_from_user": "User provides material; agent parses/transforms it.",
        "collection_scoped": "Queries a defined scope (lists, time windows).",
        "collection_unbounded": "Searches broadly with no predetermined boundary.",
        "messages": "Comments, DMs, or chat messages.",
        "unknown": "Could not be determined.",
    },
    "domain_knowledge_depth": {
        "none": "Generic instructions only; no domain references.",
        "light": "Domain is the setting, not the skill.",
        "moderate": "Domain craft knowledge essential; techniques, frameworks.",
        "deep": "Formal procedural knowledge; lifecycle, compliance.",
        "unknown": "Could not be determined.",
    },
    "operational_scope": {
        "single_action": "One discrete action per invocation.",
        "sequential_workflow": "Multi-step linear pipeline; guard clauses only.",
        "branching_workflow": "Core logic diverges by input or business rules.",
        "multi_workflow_orchestration": "Two or more independent sub-workflows.",
        "unknown": "Could not be determined.",
    },
    "data_flow_direction": {
        "inbound": "Captures external data into ClickUp.",
        "processing": "Restructures ClickUp data; output stays in ClickUp.",
        "outbound": "Output leaves ClickUp or is new content.",
        "bidirectional": "Requires both importing and exporting.",
        "unknown": "Could not be determined.",
    },
    "autonomy_level": {
        "consultative": "Asks user before acting; human gates the action.",
        "human_in_the_loop": "Acts first, then reports for human review.",
        "autonomous": "Acts without asking; handles edge cases via rules.",
        "enforcer": "Validates compliance and corrects violations.",
        "monitor": "Surfaces alerts without fixing.",
        "unknown": "Could not be determined.",
    },
    "tone_and_persona": {
        "professional_formal": "Concise, structured, executive-ready.",
        "casual_friendly": "Warm, conversational, approachable.",
        "technical_precise": "Data-driven, rigorous, systematic.",
        "empathetic_supportive": "Encouraging, coaching, patient.",
        "unknown": "Could not be determined.",
    },
    "domain_industry_vertical": {
        "project_management_ops": "Projects, sprints, standups, deadlines.",
        "sales_crm": "Deals, pipeline, leads, CRM, revenue.",
        "marketing_content": "Content, social, SEO, campaigns, branding.",
        "hr_people": "Hiring, recruiting, onboarding, performance.",
        "legal_compliance": "Legal, contracts, compliance, regulatory.",
        "finance_accounting": "Budgeting, invoicing, financial reporting.",
        "education_academic": "Teaching, tutoring, coursework, exam prep.",
        "personal_productivity": "Personal planning, habits, journaling.",
        "creative_design": "Graphic design, UI/UX, image generation, video.",
        "it_engineering": "Software dev, coding, debugging, DevOps.",
        "general_cross_functional": "General-purpose or no specific vertical.",
        "unknown": "Could not be determined.",
    },
    "external_integration_scope": {
        "clickup_only": "No external integrations; ClickUp only.",
        "email_integration": "Integrates with email.",
        "calendar_integration": "Integrates with calendar.",
        "web_research_integration": "Uses web/search or research tools.",
        "multiple_external_systems": "Multiple external systems.",
        "unknown": "Could not be determined.",
    },
    "use_case_context": {
        "specific_use_case": "Tied to a specific workflow or business use case.",
        "general_productivity": "General productivity assistance.",
        "personal_use_case": "Personal use (e.g. study, habits).",
        "personal_productivity": "Personal productivity.",
        "entertainment": "Entertainment or non-work.",
        "test_or_placeholder": "Test or placeholder agent.",
        "unknown": "Could not be determined.",
    },
    "implied_end_date": {
        "true": "Use case implies an end date.",
        "false": "No implied end date.",
        "unknown": "Could not be determined.",
    },
}

# Section body text (Inference, Direction, Correlation, Other insights) - keyed by dimension
SECTION_BODIES = {
    "functional_archetype": """**Inference:** Creator is the most common but has the lowest success rate (12%). Monitor has the highest success rate (67%). Organizer and analyzer are common with moderate success (~0.38–0.39).

**Direction (success vs fail)**

- **Population:** Monitor (0.67) and communicator (0.49) lead; creator (0.12) trails.
- **Prompts-only model:** {{RED:functional_archetype=creator}} has high importance (0.134) and strong negative coefficient (−0.20); {{GREEN:functional_archetype=monitor}} has high importance (0.090) and strong positive coefficient (+0.22). Creator pushes toward failure, monitor toward success.

**Correlation with tools, triggers, templates**  
See table above for top tools and other prompt categories (|r| ≥ 0.05). Monitor correlates with scheduled trigger and task/todo tools; creator with post_reply and introduction.

**Other insights**  
Creator-heavy prompts dominate but underperform; monitor and communicator are strong success levers. Product could favor monitor/communicator patterns where appropriate.""",
    "execution_dataset": """**Inference:** single_user_prompt and single_asset_from_user have very low success rates (0.11 and 0.08). collection_scoped and collection_unbounded have the highest (0.57 and 0.59). Collection-based execution is strongly associated with success.

**Direction (success vs fail)**

- **Population:** collection_scoped (0.57) and collection_unbounded (0.59) lead; single_user_prompt (0.11) and single_asset_from_user (0.08) trail.
- **Prompts-only model:** {{GREEN:execution_dataset=collection_scoped}} has the highest RF importance (0.174) and strong positive coefficient (+0.35); {{RED:execution_dataset=single_user_prompt}} and {{RED:execution_dataset=single_asset_from_user}} are strongly negative (−0.27, −0.26). Direction is very clear: collection-scoped toward success, single-user-prompt/asset toward failure.

**Correlation with tools, triggers, templates**  
See table above. collection_scoped correlates with scheduled and task/retrieval tools; single_user_prompt with introduction.

**Other insights**  
Execution dataset is one of the strongest predictors. Shifting prompts toward collection-scoped or unbounded semantics and away from single-user-prompt/asset may improve success.""",
    "domain_knowledge_depth": """**Inference:** Moderate is the most common but has the lowest success rate (22%). Light and none have the highest success rates (~43–44%). Deeper domain depth in the prompt is associated with lower success in raw counts.

**Direction (success vs fail)**

- **Population:** Success rate highest for none and light (~0.43–0.44); lowest for moderate (0.22).
- **Prompts-only model:** {{RED:domain_knowledge_depth=moderate}} has notable RF importance (0.022) and negative logistic coefficient (−0.044); {{GREEN:domain_knowledge_depth=light}} is positive (+0.035). So moderate pushes toward failure, light toward success, consistent with population.

**Correlation with tools, triggers, templates**  
See table above. Moderate may correlate with trigger=introduction or creator-heavy tools; light/none with scheduled and task-retrieval tools.

**Other insights**  
Agents with moderate domain depth dominate the cohort but underperform; simplifying or clarifying prompts (e.g. toward light) may be worth testing.""",
    "operational_scope": """**Inference:** Multi_workflow_orchestration has the highest success rate (59%) and is a minority; branching is most common with moderate success rate (33%); sequential has the lowest success rate (22%).

**Direction (success vs fail)**

- **Population:** multi_workflow_orchestration (0.59) and branching (0.33) lead; sequential (0.22) and single_action (0.19) trail.
- **Prompts-only model:** {{GREEN:operational_scope=multi_workflow_orchestration}} has high RF importance (0.034) and strong positive logistic (+0.155); {{RED:operational_scope=sequential_workflow}} is negative (−0.115). SHAP direction aligns: multi_workflow positive, sequential negative.

**Correlation with tools, triggers, templates**  
See table above. Multi-workflow orchestration correlates with scheduled trigger and task/todo tools; sequential_workflow correlates negatively with those.

**Other insights**  
Orchestration and branching are directionally more successful; simplifying to "sequential" in the prompt may be associated with lower success.""",
    "data_flow_direction": """**Inference:** Outbound is most common but has the lowest success rate (18%). Processing and bidirectional have higher success rates (0.42 and 0.49). Outbound-heavy prompts are associated with lower success in the population.

**Direction (success vs fail)**

- **Population:** Bidirectional (0.49) and processing (0.42) lead; outbound (0.18) trails.
- **Prompts-only model:** data_flow_direction=outbound has high RF importance (0.041) but near-zero logistic; {{GREEN:data_flow_direction=processing}} and {{GREEN:data_flow_direction=bidirectional}} have small positive coefficients. {{RED:data_flow_direction=unknown}} is negative (−0.04). Direction is mixed; population signal is stronger than model coefficients for outbound.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Outbound-dominant prompts are numerous but underperform; balancing with processing or bidirectional semantics may be worth exploring.""",
    "autonomy_level": """**Inference:** Consultative is most common but has the lowest success rate (20%). Autonomous and human_in_the_loop have higher success rates (~0.39–0.40). More autonomous prompts associate with higher success.

**Direction (success vs fail)**

- **Population:** Autonomous and human_in_the_loop ~0.39–0.40; consultative 0.20.
- **Prompts-only model:** {{RED:autonomy_level=consultative}} has negative coefficient (−0.09); {{GREEN:autonomy_level=autonomous}} positive (+0.08). RF importance: consultative (0.023), autonomous (0.011). Direction aligns: consultative toward failure, autonomous toward success.

**Correlation with tools, triggers, templates**  
See table above. Consultative correlates with introduction or low automation; autonomous with scheduled and task/memory tools.

**Other insights**  
Consultative framing may reduce success; encouraging clearer autonomous or human-in-the-loop patterns in prompts could help.""",
    "tone_and_persona": """**Inference:** Professional_formal and casual_friendly dominate. Professional_formal has the highest success rate among the main categories (0.37); casual_friendly and empathetic_supportive are lower (~0.26–0.28).

**Direction (success vs fail)**

- **Population:** professional_formal (0.37) leads; casual_friendly (0.26) and empathetic_supportive (0.28) trail.
- **Prompts-only model:** RF importance is low for tone (~0.001–0.003). Logistic: {{RED:tone_and_persona=casual_friendly}} −0.04, {{GREEN:tone_and_persona=professional_formal}} +0.01, technical_precise +0.01, empathetic_supportive +0.01. Tone has modest directional signal.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Tone is a weaker driver than archetype or scope; formal tone is slightly associated with higher success.""",
    "domain_industry_vertical": """**Inference:** creative_design and education_academic have very low success rates (0.06 and 0.13); personal_productivity and project_management_ops are higher (0.54 and 0.46). Vertical strongly differentiates success.

**Direction (success vs fail)**

- **Population:** personal_productivity (0.54), project_management_ops (0.46), sales_crm (0.44), finance_accounting (0.42) lead; creative_design (0.06), education_academic (0.13) trail.
- **Prompts-only model:** {{RED:domain_industry_vertical=creative_design}} has negative coefficient (−0.19), {{RED:domain_industry_vertical=education_academic}} (−0.13); {{GREEN:domain_industry_vertical=marketing_content}} (+0.14), {{GREEN:domain_industry_vertical=personal_productivity}} (+0.10), {{GREEN:domain_industry_vertical=project_management_ops}} (+0.07) positive. RF importance: creative_design (0.035), project_management_ops (0.027).

**Correlation with tools, triggers, templates**  
See table above. Vertical correlates with tool mix (e.g. creative with generate_image, PM with task tools).

**Other insights**  
Creative and education verticals underperform; PM, sales, finance, personal productivity align with success. Vertical-specific onboarding could emphasize successful verticals.""",
    "external_integration_scope": """**Inference:** clickup_only dominates but has the lowest success rate (0.31). Email, calendar, and multiple_external_systems have higher success rates (0.49–0.52). External integration in the prompt associates with higher success.

**Direction (success vs fail)**

- **Population:** email_integration (0.52), calendar (0.50), multiple_external_systems (0.49) lead; clickup_only (0.31) trails.
- **Prompts-only model:** {{RED:external_integration_scope=clickup_only}} has negative coefficient (−0.05); {{GREEN:external_integration_scope=web_research_integration}} (+0.03), {{GREEN:external_integration_scope=multiple_external_systems}} (+0.02) positive. RF importance is modest. Direction aligns: clickup_only toward lower success, integrations toward higher.

**Correlation with tools, triggers, templates**  
See table above. Calendar/email scope correlates with calendar/email tools and possibly scheduled trigger.

**Other insights**  
Prompts that imply external integrations (email, calendar, multiple systems) associate with higher success than clickup_only.""",
    "use_case_context": """**Inference:** general_productivity has the highest success rate among main categories (0.37); personal_use_case and entertainment are low (0.19 and 0.16). Specific and general productivity contexts perform moderately.

**Direction (success vs fail)**

- **Population:** general_productivity (0.37) leads; personal_use_case (0.19), entertainment (0.16) trail.
- **Prompts-only model:** {{RED:use_case_context=general_productivity}} has negative coefficient (−0.05); {{GREEN:use_case_context=personal_use_case}} (+0.04), {{GREEN:use_case_context=specific_use_case}} (+0.02) positive. RF importance is low. Direction is mixed; population and model partially align.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Use case context is a weaker driver; general productivity in the population aligns with higher success despite negative coefficient (confounding with other dimensions possible).""",
    "implied_end_date": """**Inference:** Most agents are false (no implied end date). Success rates are similar (0.28–0.32); implied_end_date has limited differentiation.

**Direction (success vs fail)**

- **Population:** false (0.32) slightly higher than true (0.28).
- **Prompts-only model:** {{GREEN:implied_end_date=false}} has small positive coefficient (+0.03); {{RED:implied_end_date=true}} negative (−0.03). RF importance is very low. Dimension has weak directional signal.

**Correlation with tools, triggers, templates**  
See table above.

**Other insights**  
Implied end date is a minor lever; most impact comes from other dimensions (execution_dataset, functional_archetype, domain_industry_vertical).""",
}

TITLES = {
    "functional_archetype": "Functional archetype",
    "execution_dataset": "Execution dataset",
    "domain_knowledge_depth": "Domain knowledge depth",
    "operational_scope": "Operational scope",
    "data_flow_direction": "Data flow direction",
    "autonomy_level": "Autonomy level",
    "tone_and_persona": "Tone and persona",
    "domain_industry_vertical": "Domain industry vertical",
    "external_integration_scope": "External integration scope",
    "use_case_context": "Use case context",
    "implied_end_date": "Implied end date",
}

CLASSIFICATION_LINE = {
    "functional_archetype": "The agent's primary job function (creator, organizer, analyzer, communicator, monitor, enforcer).",
    "execution_dataset": "What the agent works on per invocation (single event, user prompt, asset, collection_scoped, collection_unbounded, messages).",
    "domain_knowledge_depth": "How much specialized field expertise is baked into the prompt (generic vs craft knowledge vs formal processes).",
    "operational_scope": "How complex the agent's workflow is per run (one action vs linear pipeline vs branching vs multiple workflows).",
    "data_flow_direction": "Where data moves relative to ClickUp (inbound, processing, outbound, or bidirectional).",
    "autonomy_level": "Whether the agent asks before acting, acts then reports, or acts silently (consultative, human_in_the_loop, autonomous, enforcer, monitor).",
    "tone_and_persona": "Communication style (professional_formal, casual_friendly, technical_precise, empathetic_supportive).",
    "domain_industry_vertical": "Which industry or functional area the agent serves (PM, sales, marketing, HR, legal, finance, education, personal, creative, engineering, general).",
    "external_integration_scope": "Extent of integration with systems outside ClickUp (clickup_only, email, calendar, web_research, multiple_external_systems).",
    "use_case_context": "High-level context of how the agent is used (specific workflow, general productivity, personal, entertainment, test_or_placeholder).",
    "implied_end_date": "Whether the agent's use case implies a defined end date (e.g. project end, course end).",
}


def build_executive_summary():
    """Build Executive Summary (~1 A4): approach, classification QA, distribution, top features + chart."""
    pop_path = OUTPUT_DIR / "full_feature_population.csv"
    rf_path = OUTPUT_DIR / "classification_prompts_only_rf_importance.csv"
    beeswarm_path = OUTPUT_DIR / "classification_prompts_only_shap_beeswarm.png"
    md_out = []
    html_out = []
    # Load population for distribution
    if pop_path.exists():
        pop = pd.read_csv(pop_path)
        total = pop["count"].sum()
        # Segment counts: typically dormant, success, failure
        rows = list(pop.to_dict("records"))
    else:
        total = 113_863  # fallback from docs
        rows = [
            {"success_segment": "dormant", "count": 70_540, "success_rate": 0.32},
            {"success_segment": "success", "count": 36_712, "success_rate": 0.32},
            {"success_segment": "failure", "count": 6_611, "success_rate": 0.32},
        ]
    n_classified = sum(r.get("count", 0) for r in rows) if rows else total
    # Top features from RF (top 5 by importance)
    top_positive = []
    top_negative = []
    if rf_path.exists():
        rf = pd.read_csv(rf_path)
        lr_path = OUTPUT_DIR / "classification_prompts_only_logistic_coefficients.csv"
        if lr_path.exists():
            lr = pd.read_csv(lr_path)
            lr_map = dict(zip(lr["feature"], lr["coefficient"]))
            for _, r in rf.head(10).iterrows():
                f = r["feature"]
                coef = lr_map.get(f)
                if coef is not None:
                    if coef > 0:
                        top_positive.append((f, r["importance"]))
                    else:
                        top_negative.append((f, r["importance"]))
            top_positive = top_positive[:5]
            top_negative = top_negative[:5]
    md_out.append("## Executive Summary")
    md_out.append("")
    md_out.append("**Analytical approach.** This readout analyzes how prompt-level classifications relate to agent success. We use the same cohort and success definitions as the main agent success readout: agents are assigned to **success** (used at least once after 7 days and still active), **failure** (inactive or deleted), or **dormant** (active but no use after 7 days). The prompts-only model uses only one-hot encoded classification dimensions (no trigger or template) to predict success vs non-success. We report Random Forest importance, SHAP direction, and logistic regression coefficients, plus per-dimension distributions and correlations with tools and other prompt categories.")
    md_out.append("")
    md_out.append("**Agent classifications.** Classification logic was iterated and manually QAed on a small sample of prompts. After validation, the analysis was run on the full set of classified agents (~114K prompts). This readout covers 11 dimensions: functional archetype, execution dataset, domain knowledge depth, operational scope, data flow direction, autonomy level, tone and persona, domain industry vertical, external integration scope, use case context, and implied end date. (Team orientation, output modality, and state persistence are excluded from this readout.)")
    md_out.append("")
    md_out.append("**Distribution of agents (classified cohort).**")
    md_out.append("")
    md_out.append("| Segment | Count | Share | Success rate |")
    md_out.append("|---------|-------|-------|--------------|")
    for r in rows:
        seg = r.get("success_segment", "")
        cnt = int(r.get("count", 0))
        share = (cnt / n_classified * 100) if n_classified else 0
        rate = r.get("success_rate", 0)
        if isinstance(rate, float):
            rate = f"{rate:.2f}"
        md_out.append(f"| {seg} | {cnt:,} | {share:.1f}% | {rate} |")
    md_out.append("")
    md_out.append("**Top prompt features for success and failure.** The most important predictors from the prompts-only model are:")
    md_out.append("")
    if top_positive:
        md_out.append("- **Toward success (positive):** " + "; ".join(f"<span style=\"color:green\">{f}</span> (RF importance {imp:.3f})" for f, imp in top_positive))
    else:
        md_out.append("- **Toward success (positive):** <span style=\"color:green\">execution_dataset=collection_scoped</span>; <span style=\"color:green\">functional_archetype=monitor</span>; <span style=\"color:green\">execution_dataset=collection_unbounded</span>; <span style=\"color:green\">operational_scope=multi_workflow_orchestration</span>; <span style=\"color:green\">domain_industry_vertical=project_management_ops</span>.")
    if top_negative:
        md_out.append("- **Toward failure (negative):** " + "; ".join(f"<span style=\"color:#c00\">{f}</span> (RF importance {imp:.3f})" for f, imp in top_negative))
    else:
        md_out.append("- **Toward failure (negative):** <span style=\"color:#c00\">functional_archetype=creator</span>; <span style=\"color:#c00\">execution_dataset=single_user_prompt</span>; <span style=\"color:#c00\">execution_dataset=single_asset_from_user</span>; <span style=\"color:#c00\">domain_industry_vertical=creative_design</span>; <span style=\"color:#c00\">autonomy_level=consultative</span>.")
    md_out.append("")
    md_out.append("The chart below summarizes SHAP direction across all prompt features; green indicates higher success, red lower success. See the *Prompts-only model summary* section for the full RF importance table and significant logistic coefficients.")
    md_out.append("")
    if beeswarm_path.exists():
        md_out.append("![SHAP beeswarm – prompts-only](../analysis/output/classification_prompts_only_shap_beeswarm.png)")
        md_out.append("")
    md_out.append("---")
    md_out.append("")
    # HTML
    html_out.append('<h2 id="executive-summary">Executive Summary</h2>')
    html_out.append("<p><strong>Analytical approach.</strong> This readout analyzes how prompt-level classifications relate to agent success. We use the same cohort and success definitions as the main agent success readout: agents are assigned to <strong>success</strong> (used at least once after 7 days and still active), <strong>failure</strong> (inactive or deleted), or <strong>dormant</strong> (active but no use after 7 days). The prompts-only model uses only one-hot encoded classification dimensions (no trigger or template) to predict success vs non-success. We report Random Forest importance, SHAP direction, and logistic regression coefficients, plus per-dimension distributions and correlations with tools and other prompt categories.</p>")
    html_out.append("<p><strong>Agent classifications.</strong> Classification logic was iterated and manually QAed on a small sample of prompts. After validation, the analysis was run on the full set of classified agents (~114K prompts). This readout covers 11 dimensions: functional archetype, execution dataset, domain knowledge depth, operational scope, data flow direction, autonomy level, tone and persona, domain industry vertical, external integration scope, use case context, and implied end date. (Team orientation, output modality, and state persistence are excluded from this readout.)</p>")
    html_out.append("<p><strong>Distribution of agents (classified cohort).</strong></p>")
    html_out.append("<table><tr><th>Segment</th><th>Count</th><th>Share</th><th>Success rate</th></tr>")
    for r in rows:
        seg = r.get("success_segment", "")
        cnt = int(r.get("count", 0))
        share = (cnt / n_classified * 100) if n_classified else 0
        rate = r.get("success_rate", 0)
        if isinstance(rate, float):
            rate = f"{rate:.2f}"
        html_out.append(f"<tr><td>{html.escape(seg)}</td><td>{cnt:,}</td><td>{share:.1f}%</td><td>{rate}</td></tr>")
    html_out.append("</table>")
    html_out.append("<p><strong>Top prompt features for success and failure.</strong> The most important predictors from the prompts-only model are:</p>")
    if top_positive:
        html_out.append("<p><strong>Toward success (positive):</strong> " + "; ".join(f'<span class="corr-pos">{html.escape(f)}</span> (RF importance {imp:.3f})' for f, imp in top_positive) + "</p>")
    else:
        html_out.append('<p><strong>Toward success:</strong> <span class="corr-pos">execution_dataset=collection_scoped</span>; <span class="corr-pos">functional_archetype=monitor</span>; <span class="corr-pos">execution_dataset=collection_unbounded</span>; <span class="corr-pos">operational_scope=multi_workflow_orchestration</span>; <span class="corr-pos">domain_industry_vertical=project_management_ops</span>.</p>')
    if top_negative:
        html_out.append("<p><strong>Toward failure (negative):</strong> " + "; ".join(f'<span class="corr-neg">{html.escape(f)}</span> (RF importance {imp:.3f})' for f, imp in top_negative) + "</p>")
    else:
        html_out.append('<p><strong>Toward failure:</strong> <span class="corr-neg">functional_archetype=creator</span>; <span class="corr-neg">execution_dataset=single_user_prompt</span>; <span class="corr-neg">execution_dataset=single_asset_from_user</span>; <span class="corr-neg">domain_industry_vertical=creative_design</span>; <span class="corr-neg">autonomy_level=consultative</span>.</p>')
    html_out.append("<p>The chart below summarizes SHAP direction across all prompt features; green indicates higher success, red lower success. See the <em>Prompts-only model summary</em> section for the full RF importance table and significant logistic coefficients.</p>")
    if beeswarm_path.exists():
        html_out.append('<p><img src="../analysis/output/classification_prompts_only_shap_beeswarm.png" alt="SHAP beeswarm prompts-only"></p>')
    html_out.append("<hr>")
    return md_out, html_out


def build_prompts_only_summary():
    """Build MD and HTML for the Prompts-only model summary section (RF, SHAP beeswarm, Logistic) with green/red highlighting."""
    rf_path = OUTPUT_DIR / "classification_prompts_only_rf_importance.csv"
    lr_path = OUTPUT_DIR / "classification_prompts_only_logistic_coefficients.csv"
    shap_path = OUTPUT_DIR / "classification_prompts_only_shap_direction.csv"
    beeswarm_path = OUTPUT_DIR / "classification_prompts_only_shap_beeswarm.png"
    md_out = []
    html_out = []
    if not rf_path.exists() or not lr_path.exists():
        md_out.extend([
            "## Prompts-only model summary",
            "",
            "*(Run classification_success_analysis.py to generate RF, SHAP, and logistic outputs.)*",
            "",
            "---",
            "",
        ])
        html_out.append('<h2 id="prompts-only-model-summary">Prompts-only model summary</h2><p><em>Run classification_success_analysis.py to generate RF, SHAP, and logistic outputs.</em></p><hr>')
        return md_out, html_out
    rf = pd.read_csv(rf_path)
    lr = pd.read_csv(lr_path)
    shap = pd.read_csv(shap_path) if shap_path.exists() else None
    lr_map = dict(zip(lr["feature"], lr["coefficient"]))
    # Top 15 by RF importance with direction from logistic
    rf_top = rf.head(15).copy()
    rf_top["coef"] = rf_top["feature"].map(lr_map)
    rf_top["positive"] = (rf_top["coef"] > 0)
    # Significant logistic: |coef| >= 0.05
    lr_sig = lr[np.abs(lr["coefficient"]) >= 0.05].sort_values("coefficient", ascending=False)
    lr_pos = lr_sig[lr_sig["coefficient"] > 0]
    lr_neg = lr_sig[lr_sig["coefficient"] < 0]
    md_out.append("## Prompts-only model summary")
    md_out.append("")
    md_out.append("This section summarizes **Random Forest importance**, **SHAP direction**, and **Logistic regression coefficients** from the prompts-only model (classification dimensions only). **Green** = feature associated with higher success; **red** = associated with lower success.")
    md_out.append("")
    md_out.append("**Commentary:** The strongest positive predictors are <span style=\"color:green\">execution_dataset=collection_scoped</span> and <span style=\"color:green\">functional_archetype=monitor</span> (high RF importance and positive coefficients). The strongest negative predictors are <span style=\"color:#c00\">functional_archetype=creator</span>, <span style=\"color:#c00\">execution_dataset=single_user_prompt</span>, and <span style=\"color:#c00\">execution_dataset=single_asset_from_user</span>. <span style=\"color:green\">domain_knowledge_depth=light</span> and <span style=\"color:#c00\">domain_knowledge_depth=moderate</span> are also notable; <span style=\"color:#c00\">domain_industry_vertical=creative_design</span> and <span style=\"color:#c00\">education_academic</span> are negative. Below: top 15 RF features (colored by logistic direction), SHAP beeswarm, and significant logistic coefficients.")
    md_out.append("")
    md_out.append("**Top 15 features by RF importance (direction from logistic regression)**")
    md_out.append("")
    md_out.append("| Feature | Importance | Direction |")
    md_out.append("|---------|------------|-----------|")
    for _, r in rf_top.iterrows():
        coef = r.get("coef")
        if pd.isna(coef):
            direction = "—"
        else:
            direction = "<span style=\"color:green\">positive</span>" if coef > 0 else "<span style=\"color:#c00\">negative</span>"
        md_out.append(f"| {r['feature']} | {r['importance']:.3f} | {direction} |")
    md_out.append("")
    if beeswarm_path.exists():
        md_out.append("**SHAP beeswarm (prompts-only)**")
        md_out.append("")
        md_out.append("![SHAP beeswarm](../analysis/output/classification_prompts_only_shap_beeswarm.png)")
        md_out.append("")
    md_out.append("**Significant logistic coefficients (|coefficient| ≥ 0.05)**")
    md_out.append("")
    md_out.append("- **Positive (green):** " + "; ".join(f"<span style=\"color:green\">{f} ({c:.3f})</span>" for _, (f, c) in lr_pos[["feature", "coefficient"]].iterrows()))
    md_out.append("- **Negative (red):** " + "; ".join(f"<span style=\"color:#c00\">{f} ({c:.3f})</span>" for _, (f, c) in lr_neg[["feature", "coefficient"]].iterrows()))
    md_out.append("")
    md_out.append("---")
    md_out.append("")
    # HTML
    html_out.append('<h2 id="prompts-only-model-summary">Prompts-only model summary</h2>')
    html_out.append("<p>This section summarizes <strong>Random Forest importance</strong>, <strong>SHAP direction</strong>, and <strong>Logistic regression coefficients</strong> from the prompts-only model. <span class=\"corr-pos\">Green</span> = feature associated with higher success; <span class=\"corr-neg\">Red</span> = associated with lower success.</p>")
    html_out.append("<p><strong>Commentary:</strong> The strongest positive predictors are <span class=\"corr-pos\">execution_dataset=collection_scoped</span> and <span class=\"corr-pos\">functional_archetype=monitor</span>. Strongest negative: <span class=\"corr-neg\">functional_archetype=creator</span>, <span class=\"corr-neg\">execution_dataset=single_user_prompt</span>, <span class=\"corr-neg\">execution_dataset=single_asset_from_user</span>. <span class=\"corr-pos\">domain_knowledge_depth=light</span> is positive; <span class=\"corr-neg\">domain_knowledge_depth=moderate</span>, <span class=\"corr-neg\">domain_industry_vertical=creative_design</span>, and <span class=\"corr-neg\">education_academic</span> are negative.</p>")
    html_out.append("<h3>Top 15 features by RF importance (direction from logistic)</h3>")
    html_out.append("<table><tr><th>Feature</th><th>Importance</th><th>Direction</th></tr>")
    for _, r in rf_top.iterrows():
        coef = r.get("coef")
        if pd.isna(coef):
            direction = "—"
        else:
            direction = '<span class="corr-pos">positive</span>' if coef > 0 else '<span class="corr-neg">negative</span>'
        html_out.append(f"<tr><td>{html.escape(r['feature'])}</td><td>{r['importance']:.3f}</td><td>{direction}</td></tr>")
    html_out.append("</table>")
    if beeswarm_path.exists():
        html_out.append("<p><strong>SHAP beeswarm (prompts-only)</strong></p>")
        html_out.append('<p><img src="../analysis/output/classification_prompts_only_shap_beeswarm.png" alt="SHAP beeswarm"></p>')
    html_out.append("<h3>Significant logistic coefficients (|coefficient| ≥ 0.05)</h3>")
    html_out.append("<p><strong>Positive:</strong> " + "; ".join(f'<span class="corr-pos">{html.escape(f)} ({c:.3f})</span>' for _, (f, c) in lr_pos[["feature", "coefficient"]].iterrows()) + "</p>")
    html_out.append("<p><strong>Negative:</strong> " + "; ".join(f'<span class="corr-neg">{html.escape(f)} ({c:.3f})</span>' for _, (f, c) in lr_neg[["feature", "coefficient"]].iterrows()) + "</p>")
    html_out.append("<hr>")
    return md_out, html_out


def load_dim_df(dim):
    """Load classification_dim CSV and merge top_tools and top_prompts; return DataFrame with value, definition, counts, correlation columns."""
    dim_path = OUTPUT_DIR / f"classification_dim_{dim}.csv"
    if not dim_path.exists():
        return None
    df = pd.read_csv(dim_path)
    val_col = df.columns[0]
    df = df.rename(columns={val_col: "value"})
    df["value"] = df["value"].astype(str)
    tools_path = OUTPUT_DIR / f"prompts_readout_top_tools_{dim}.csv"
    prompts_path = OUTPUT_DIR / f"prompts_readout_top_prompts_{dim}.csv"
    if tools_path.exists():
        tools_df = pd.read_csv(tools_path)
        tools_df["value"] = tools_df["value"].astype(str)
        df = df.merge(tools_df[["value", "top_tools_pos", "top_tools_neg"]], on="value", how="left")
    else:
        df["top_tools_pos"] = "—"
        df["top_tools_neg"] = "—"
    if prompts_path.exists():
        prompts_df = pd.read_csv(prompts_path)
        prompts_df["value"] = prompts_df["value"].astype(str)
        df = df.merge(prompts_df[["value", "top_prompts_pos", "top_prompts_neg"]], on="value", how="left")
    else:
        df["top_prompts_pos"] = "—"
        df["top_prompts_neg"] = "—"
    df["top_tools_pos"] = df["top_tools_pos"].fillna("—")
    df["top_tools_neg"] = df["top_tools_neg"].fillna("—")
    df["top_prompts_pos"] = df["top_prompts_pos"].fillna("—")
    df["top_prompts_neg"] = df["top_prompts_neg"].fillna("—")
    defs = DEFINITIONS.get(dim, {})
    df["definition"] = df["value"].map(lambda v: defs.get(v, "Could not be determined."))
    return df


def _color_corr_cell(cell_text: str, positive: bool, for_html: bool) -> str:
    """Wrap each 'feature r' segment in a green (positive) or red (negative) span. cell_text like 'a 0.1; b -0.2' or '—'."""
    if not cell_text or str(cell_text).strip() == "—":
        return cell_text if for_html else str(cell_text)
    segments = [s.strip() for s in str(cell_text).split(";") if s.strip()]
    if not segments:
        return cell_text if for_html else str(cell_text)
    if for_html:
        cls = "corr-pos" if positive else "corr-neg"
        return "; ".join(f'<span class="{cls}">{html.escape(seg)}</span>' for seg in segments)
    # Markdown: inline HTML for color
    color = "green" if positive else "#c00"
    return "; ".join(f'<span style="color:{color}">{seg.replace("|", "\\|")}</span>' for seg in segments)


def _md_bold_to_html(s):
    """Replace **text** with <strong>text</strong> and escape the rest."""
    out = []
    i = 0
    while i < len(s):
        if s[i:i + 2] == "**":
            j = s.find("**", i + 2)
            if j != -1:
                out.append("<strong>")
                out.append(html.escape(s[i + 2:j]))
                out.append("</strong>")
                i = j + 2
                continue
        out.append(html.escape(s[i]))
        i += 1
    return "".join(out)


def section_body_to_html(body_text):
    """Convert markdown-ish section body to simple HTML (paragraphs and lists)."""
    lines = body_text.strip().split("\n")
    out = []
    in_list = False
    for line in lines:
        s = line.strip()
        if not s:
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        if s.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_md_bold_to_html(s[2:])}</li>")
        elif s.startswith("**"):
            if in_list:
                out.append("</ul>")
                in_list = False
            # "**Inference:** text" (no closing **) or "**Direction (success vs fail)**"
            if ":**" in s:
                idx = s.index(":**")
                label = s[2:idx]
                rest = s[idx + 2:].strip()
                out.append(f"<p><strong>{html.escape(label)}</strong> {_md_bold_to_html(rest)}</p>")
            elif s.endswith("**") and s.count("**") >= 2:
                label = s[2:-2]
                out.append(f"<p><strong>{html.escape(label)}</strong></p>")
            else:
                out.append(f"<p>{_md_bold_to_html(s)}</p>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{_md_bold_to_html(s)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def main():
    md_lines = [
        "# Prompts-only classification readout",
        "",
        "**Last updated:** 2026-03-11  ",
        "**Scope:** Classification dimensions only (no triggers or tools in the success model). Correlation sections add tools, triggers, and templates for context.  ",
        "**Data:** Classified cohort (agents in `agent_classifications.csv` with success_segment from cohort). Success/failure/dormant definitions match the main agent success readout.  ",
        "**Value meanings:** See [semantic_layer/models/agent_classifications.md](semantic_layer/models/agent_classifications.md).",
        "",
    ]
    html_parts = []
    exec_md, exec_html = build_executive_summary()
    md_lines.extend(exec_md)
    # Index (table of contents) with anchor links to all h2 sections
    index_entries = [
        ("executive-summary", "Executive Summary"),
        ("prompts-only-model-summary", "Prompts-only model summary"),
    ]
    for num, dim in enumerate(DIMS_ORDER, 1):
        title = TITLES[dim]
        slug = dim.replace("_", "-")
        index_entries.append((f"{num}-{slug}", f"{num}. {title}"))
    index_entries.append(("document-level-footnotes", "Document-level footnotes"))
    index_lines = ['<nav id="contents"><h2>Contents</h2><ul>']
    for aid, label in index_entries:
        index_lines.append(f'<li><a href="#{aid}">{html.escape(label)}</a></li>')
    index_lines.append("</ul></nav><hr>")
    html_index = "\n".join(index_lines)
    html_header = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Prompts-only classification readout – plain</title>
  <style>
    body { font-family: Georgia, 'Times New Roman', serif; max-width: 900px; margin: 32px auto; padding: 0 16px; line-height: 1.5; color: #222; }
    h1 { font-size: 1.5em; border-bottom: 1px solid #ccc; padding-bottom: 6px; }
    h2 { font-size: 1.25em; margin-top: 24px; }
    h3 { font-size: 1.1em; margin-top: 16px; }
    p { margin: 8px 0; }
    ul { margin: 8px 0; padding-left: 24px; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.9em; }
    th, td { border: 1px solid #999; padding: 6px 8px; text-align: left; vertical-align: top; }
    th { background: #f0f0f0; font-weight: bold; }
    img { max-width: 100%; height: auto; }
    .corr-pos { color: green; }
    .corr-neg { color: #c00; }
    nav#contents { margin: 16px 0; padding: 12px; background: #f8f8f8; border: 1px solid #ddd; }
    nav#contents ul { list-style: none; padding-left: 0; }
    nav#contents li { margin: 6px 0; }
    nav#contents a { color: #0066cc; text-decoration: none; }
    nav#contents a:hover { text-decoration: underline; }
  </style>
</head>
<body>

<h1>Prompts-only classification readout</h1>
<p><strong>Last updated:</strong> 2026-03-11</p>
<p><strong>Scope:</strong> Classification dimensions only (no triggers or tools in the success model). Correlation sections add tools, triggers, and templates for context.</p>
<p><strong>Data:</strong> Classified cohort (agents in agent_classifications.csv with success_segment from cohort). Success/failure/dormant definitions match the main agent success readout.</p>
<p><strong>Value meanings:</strong> See semantic_layer/models/agent_classifications.md in the repo.</p>
<p><em>To copy into Word or Google Docs: open this file in a web browser, then Select All (Ctrl/Cmd+A) and Paste into your document.</em></p>

<hr>
""" + html_index
    html_footer = """
<hr>
<h2 id="document-level-footnotes">Document-level footnotes</h2>
<h3>Success vs failure criteria</h3>
<ul>
  <li><strong>Success:</strong> After 7 days of creation, the agent has been used at least once and is still <strong>active</strong> as of the analysis date.</li>
  <li><strong>Failure:</strong> Agent is <strong>inactive</strong> and/or <strong>deleted</strong>.</li>
  <li><strong>Dormant:</strong> Created, not deleted, <strong>active</strong>, but <strong>no usage post 7 days</strong> of creation.</li>
  <li><strong>Parameters:</strong> analysis_reference_date (see cohort_metadata.yaml); days_post_creation = 7.</li>
</ul>
<h3>Assumptions</h3>
<ul>
  <li>Classified cohort only (agents in agent_classifications.csv).</li>
  <li>Prompts-only model excludes trigger and template; direction (RF/SHAP/logistic) is from this model.</li>
  <li>Correlation is agent-level: primary trigger and primary template from runs; tool usage = average calls per run per tool.</li>
  <li>Value meanings and option lists from semantic_layer/models/agent_classifications.md.</li>
</ul>
<h3>Limitations</h3>
<ul>
  <li>Correlation does not imply causation.</li>
  <li>Pearson correlation used for consistency; one-hot encoding for classification dimensions.</li>
  <li>Top correlations use threshold |r| ≥ 0.05.</li>
  <li>Tools/triggers/templates in the correlation dataset are limited to those available in the agent-level build.</li>
</ul>
<h3>Correlation color code (in distribution tables)</h3>
<ul>
  <li><span class="corr-pos"><strong>Green</strong></span> = positive correlation with that dimension value.</li>
  <li><span class="corr-neg"><strong>Red</strong></span> = negative correlation.</li>
</ul>

</body>
</html>
"""
    summary_md, summary_html = build_prompts_only_summary()
    md_lines.extend(summary_md)
    html_parts.extend(exec_html)
    html_parts.extend(summary_html)
    for num, dim in enumerate(DIMS_ORDER, 1):
        title = TITLES[dim]
        df = load_dim_df(dim)
        if df is None:
            md_lines.append(f"## {num}. {title}")
            md_lines.append("")
            md_lines.append("*(Data not found.)*")
            md_lines.append("")
            continue
        # Markdown
        md_lines.append(f"## {num}. {title}")
        md_lines.append("")
        md_lines.append("**Classification**  ")
        md_lines.append(CLASSIFICATION_LINE[dim])
        md_lines.append("")
        md_lines.append("**Distribution**")
        md_lines.append("")
        md_lines.append("| Value | What each value means | Dormant | Failure | Success | Success rate | Top 3 tools (pos; r) | Top 3 tools (neg; r) | Top 3 prompts (pos; r) | Top 3 prompts (neg; r) |")
        md_lines.append("|-------|------------------------|---------|---------|---------|--------------|----------------------|----------------------|------------------------|------------------------|")
        for _, row in df.iterrows():
            dorm = int(row.get("dormant", 0))
            fail = int(row.get("failure", 0))
            succ = int(row.get("success", 0))
            rate = row.get("success_rate", 0)
            if isinstance(rate, float):
                rate = f"{rate:.2f}"
            defn = str(row["definition"]).replace("|", "\\|")
            tpos = _color_corr_cell(str(row["top_tools_pos"]), True, False)
            tneg = _color_corr_cell(str(row["top_tools_neg"]), False, False)
            ppos = _color_corr_cell(str(row["top_prompts_pos"]), True, False)
            pneg = _color_corr_cell(str(row["top_prompts_neg"]), False, False)
            md_lines.append(f"| {row['value']} | {defn} | {dorm:,} | {fail:,} | {succ:,} | {rate} | {tpos} | {tneg} | {ppos} | {pneg} |")
        md_lines.append("")
        md_lines.append("**Bar chart (agent count and success rate by value)**")
        md_lines.append("")
        md_lines.append(f"![{title} distribution](../analysis/output/classification_dim_{dim}_bar.png)")
        md_lines.append("")
        body_md = re.sub(r"\{\{RED:([^}]+)\}\}", r'<span style="color:#c00">\1</span>', SECTION_BODIES[dim])
        body_md = re.sub(r"\{\{GREEN:([^}]+)\}\}", r'<span style="color:green">\1</span>', body_md)
        md_lines.append(body_md)
        md_lines.append("")
        md_lines.append("**Footnotes**  ")
        md_lines.append("Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. **Correlation color code:** Green = positive correlation with this dimension value; Red = negative correlation.")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        # HTML
        section_id = f'{num}-{dim.replace("_", "-")}'
        html_parts.append(f'<h2 id="{section_id}">{num}. {html.escape(title)}</h2>')
        html_parts.append("<h3>Classification</h3>")
        html_parts.append(f"<p>{html.escape(CLASSIFICATION_LINE[dim])}</p>")
        html_parts.append("<h3>Distribution</h3>")
        html_parts.append("""<table>
  <tr><th>Value</th><th>What each value means</th><th>Dormant</th><th>Failure</th><th>Success</th><th>Success rate</th><th>Top 3 tools (pos; r)</th><th>Top 3 tools (neg; r)</th><th>Top 3 prompts (pos; r)</th><th>Top 3 prompts (neg; r)</th></tr>
""")
        for _, row in df.iterrows():
            dorm = int(row.get("dormant", 0))
            fail = int(row.get("failure", 0))
            succ = int(row.get("success", 0))
            rate = row.get("success_rate", 0)
            if isinstance(rate, float):
                rate = f"{rate:.2f}"
            defn = html.escape(str(row["definition"]))
            tpos = _color_corr_cell(str(row["top_tools_pos"]), True, True)
            tneg = _color_corr_cell(str(row["top_tools_neg"]), False, True)
            ppos = _color_corr_cell(str(row["top_prompts_pos"]), True, True)
            pneg = _color_corr_cell(str(row["top_prompts_neg"]), False, True)
            html_parts.append(f"  <tr><td>{html.escape(row['value'])}</td><td>{defn}</td><td>{dorm:,}</td><td>{fail:,}</td><td>{succ:,}</td><td>{rate}</td><td>{tpos}</td><td>{tneg}</td><td>{ppos}</td><td>{pneg}</td></tr>\n")
        html_parts.append("</table>")
        html_parts.append("<p><strong>Bar chart (agent count and success rate by value)</strong></p>")
        html_parts.append(f'<p><img src="../analysis/output/classification_dim_{dim}_bar.png" alt="{html.escape(title)} distribution"></p>')
        body_html = section_body_to_html(SECTION_BODIES[dim])
        body_html = re.sub(r"\{\{RED:([^}]+)\}\}", r'<span class="corr-neg">\1</span>', body_html)
        body_html = re.sub(r"\{\{GREEN:([^}]+)\}\}", r'<span class="corr-pos">\1</span>', body_html)
        html_parts.append(body_html)
        html_parts.append("<p><strong>Footnotes:</strong> Correlations are agent-level Pearson (|r| ≥ 0.05); primary trigger/template and avg tool usage per run. <strong>Correlation color code:</strong> <span class=\"corr-pos\">Green</span> = positive correlation with this dimension value; <span class=\"corr-neg\">Red</span> = negative correlation.</p>")
        html_parts.append("<hr>")
    md_lines.extend([
        "## Document-level footnotes",
        "",
        "**Success vs failure criteria**  ",
        "- **Success:** After 7 days of creation, the agent has been used at least once and is still **active** as of the analysis date.  ",
        "- **Failure:** Agent is **inactive** and/or **deleted**.  ",
        "- **Dormant:** Created, not deleted, **active**, but **no usage post 7 days** of creation.  ",
        "- **Parameters:** analysis_reference_date (see cohort_metadata.yaml); days_post_creation = 7.",
        "",
        "**Assumptions**  ",
        "- Classified cohort only (agents in agent_classifications.csv).  ",
        "- Prompts-only model excludes trigger and template; direction (RF/SHAP/logistic) is from this model.  ",
        "- Correlation is agent-level: primary trigger and primary template from runs; tool usage = average calls per run per tool.  ",
        "- Value meanings and option lists from [agent_classifications.md](semantic_layer/models/agent_classifications.md).",
        "",
        "**Limitations**  ",
        "- Correlation does not imply causation.  ",
        "- Pearson correlation used for consistency; one-hot encoding for classification dimensions.  ",
        "- Top correlations use threshold |r| ≥ 0.05.  ",
        "- Tools/triggers/templates in the correlation dataset are limited to those available in the agent-level build.",
        "",
        "**Correlation color code (in distribution tables)**  ",
        "- **Green** = positive correlation with that dimension value.  ",
        "- **Red** = negative correlation.  ",
        "",
    ])
    (DOCS_DIR / "prompts_classification_readout.md").write_text("\n".join(md_lines), encoding="utf-8")
    print("Wrote docs/prompts_classification_readout.md")
    html_full = html_header + "\n".join(html_parts) + html_footer
    (DOCS_DIR / "prompts_classification_readout_plain.html").write_text(html_full, encoding="utf-8")
    print("Wrote docs/prompts_classification_readout_plain.html")


if __name__ == "__main__":
    main()
