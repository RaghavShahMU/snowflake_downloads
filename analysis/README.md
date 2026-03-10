# Agent success and retention analysis

Pipeline to identify which agent types are more successful and retained: success criteria, trigger sources, ClickUp tools, and prompt classifications (with Random Forest + SHAP and cohort/statistical tests).

## Setup

From repo root:

```bash
pip install -r requirements.txt   # or use .venv
```

## Run

**Option 1 — run all steps in order:**

```bash
python analysis/run_all_analysis.py
```

**Option 2 — run steps individually (from repo root):**

```bash
cd analysis
export MPLCONFIGDIR=../analysis/output   # optional, for matplotlib cache
python define_success_cohort.py
python trigger_success_analysis.py
python tool_success_analysis.py
python classification_success_analysis.py
```

## Config

Edit `analysis/config.yaml`:

- `analysis_reference_date`: set to `YYYY-MM-DD` or leave `null` to use max run date in data
- `days_post_creation`: 7 (used for success = “used after 7 days and still active”)

## Outputs

All outputs go to `analysis/output/`:

- **Cohort:** `cohort.csv`, `cohort_segment_counts.csv`, `cohort_metadata.yaml`, `cohort_segment_distribution.png`
- **Triggers:** `trigger_taxonomy.csv`, `trigger_by_segment.csv`, `trigger_rf_importance.csv`, `trigger_shap_summary.csv`, `trigger_by_segment.png`, `trigger_shap_bar.png`
- **Tools:** `tool_taxonomy.csv`, `tool_by_segment.csv`, `tool_cohort_comparison.csv`, `tool_rf_importance.csv`, `tool_shap_bar.png`, `tool_by_segment.png`
- **Classifications:** `classification_coverage.csv`, `classification_dim_*.csv`, `classification_trigger_by_segment.csv`, `classification_template_by_segment.csv`, `classification_rf_importance.csv`, `classification_shap_bar.png`, `classification_operational_scope_success_rate.png`

## Readout

Update `docs/agent_success_retention_readout.md` with results, commentary, and recommended actions after each run. The readout is the C-suite-facing document (methodology, sample metadata, results with tables/graphs, and exhaustive appendix).
