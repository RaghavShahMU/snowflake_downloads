# Snowflake Downloads

A data analysis repository for building **semantic layers** over exported datasets and running complex analytics on top of them.

## Overview

This repo holds four CSV datasets (in `data/`) that will be modeled with semantic layers and used for in-depth analysis. Detailed documentation for each file and the analysis plan will be added as we go.

## Repository structure

```
.
├── data/                    # Source CSV datasets
│   ├── agent_classifications.csv
│   ├── super_agents.csv
│   ├── super_agent_tools.csv
│   └── super_agent_run.csv
├── semantic_layer/          # Semantic layer (Markdown + YAML)
│   ├── README.md
│   └── models/
│       ├── index.yml
│       ├── super_agents.md
│       └── super_agents.yml
├── scripts/                 # Python utilities
├── README.md
└── .gitignore
```

## Data files

| File | Description |
|------|-------------|
| `agent_classifications.csv` | Agent taxonomy: team orientation, domain knowledge, autonomy, archetype, vertical, use case, etc. |
| `super_agents.csv` | Super agent metadata: workspace, status, schedules, memory, tools, knowledge, and asset counts. |
| `super_agent_tools.csv` | Agent–tool configuration and usage. |
| `super_agent_run.csv` | Agent run / execution records. |

*(In-depth descriptions and semantic layer design for each file will be documented here.)*

## Analysis (agent success and retention)

The **analysis/** pipeline identifies which agent types are more successful and retained:

1. **Success cohort** — Define success / failure / dormant / unknown (used after 7 days and still active = success).
2. **Trigger sources** — Trigger taxonomy, trigger × segment (normalized %), Random Forest + SHAP.
3. **ClickUp tools** — Tool × segment (avg per run), RF + SHAP, cohort comparison with statistical significance.
4. **Prompts (classifications)** — One-hot classifications + trigger + template, RF + SHAP, per-dimension analysis.

Run: `python analysis/run_all_analysis.py`. Outputs in `analysis/output/`. C-suite readout: `docs/agent_success_retention_readout.md`.

## Public readouts (view in browser)

Three HTML readouts with embedded tables, charts, and graphs are published via GitHub Pages. No sign-in required.

| Readout | Description | Link |
|--------|-------------|------|
| **Agent success and retention** | Success criteria, triggers, tools, prompts (classifications), retention insights | [View readout](https://raghavshahmu.github.io/snowflake_downloads/docs/agent_success_retention_readout_plain.html) |
| **Prompts-only classification** | 14 classification dimensions: distribution, direction (RF/SHAP/logistic), correlation with tools/triggers/templates | [View readout](https://raghavshahmu.github.io/snowflake_downloads/docs/prompts_classification_readout_plain.html) |
| **Full-feature exhaustive** | All features (prompts, triggers, templates, tools): distribution, RF, SHAP, logistic, correlation matrices | [View readout](https://raghavshahmu.github.io/snowflake_downloads/docs/full_feature_readout_plain.html) |

*Links work after the repo is pushed and GitHub Pages is enabled (Settings → Pages → Source: Deploy from branch → main → / (root)).*

## Planned work

1. **Semantic layers** – Define consistent business concepts, metrics, and dimensions on top of the raw CSVs.
2. **Analysis** – Run complicated, reproducible analysis using those semantic layers (see above).

## Getting started

- **Clone** the repo. To run the analysis locally, add the `data/` folder (CSVs) separately; it is not stored in the repo (see `.gitignore`).
- **Semantic layer** and **analysis** tooling and setup will be documented once chosen (e.g. dbt, Cube, Metabase, or code-based).

## Contributing

Standard GitHub workflow: open issues for ideas and PRs for changes. Keep `data/` as the single source of truth for the four CSVs.
