#!/usr/bin/env python3
"""
Build the prompts SHAP full-sample readout from classification_success_analysis.py outputs.
Run after classification_success_analysis.py (with full-cohort SHAP). Writes docs/prompts_shap_full_sample_readout.md and docs/prompts_shap_full_sample_readout_plain.html.
"""
import html as html_module
import pandas as pd
from pathlib import Path

from _utils import REPO_ROOT, OUTPUT_DIR

DOCS_DIR = REPO_ROOT / "docs"
READOUT_MD = DOCS_DIR / "prompts_shap_full_sample_readout.md"
READOUT_HTML = DOCS_DIR / "prompts_shap_full_sample_readout_plain.html"
TOP_N_DIRECTION = 25
TOP_N_BY_VALUE = 15  # rows to show from shap_by_value (value=1, sorted by |mean_shap|)

HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Prompts SHAP – full sample readout</title>
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
    img { max-width: 100%; height: auto; margin: 12px 0; display: block; }
    .corr-pos { color: green; }
    .corr-neg { color: #c00; }
    nav#contents { margin: 16px 0; padding: 12px; background: #f8f8f8; border: 1px solid #ddd; }
    nav#contents ul { list-style: none; padding-left: 0; }
    nav#contents li { margin: 6px 0; }
    nav#contents a { color: #0066cc; text-decoration: none; }
    nav#contents a:hover { text-decoration: underline; }
    .note { font-size: 0.9em; color: #555; margin-top: 24px; }
  </style>
</head>
<body>

<h1>Prompts SHAP – full sample readout</h1>
<p><strong>Last updated:</strong> Generated from analysis outputs.</p>
<p><strong>Scope:</strong> SHAP for the <strong>prompts-only</strong> model (one-hot encoded classification dimensions only) computed on the <strong>full classified cohort</strong> — all agents with classifications, no sample cap.</p>
<p><em>To copy into Word or Google Docs: open this file in a browser (from project folder so images load), Select All and Paste.</em></p>

<hr>
<nav id="contents"><h2>Contents</h2><ul>
<li><a href="#methodology">1. Methodology</a></li>
<li><a href="#shap-direction">2. SHAP direction (full cohort)</a></li>
<li><a href="#shap-beeswarm">3. SHAP beeswarm</a></li>
<li><a href="#shap-bar">4. SHAP bar</a></li>
<li><a href="#shap-by-value">5. Average SHAP per feature value</a></li>
</ul></nav>
<hr>
"""


def main():
    shap_dir_path = OUTPUT_DIR / "classification_prompts_only_shap_direction.csv"
    shap_by_val_path = OUTPUT_DIR / "classification_prompts_only_shap_by_value.csv"
    beeswarm_path = OUTPUT_DIR / "classification_prompts_only_shap_beeswarm.png"
    bar_path = OUTPUT_DIR / "classification_prompts_only_shap_bar.png"

    lines = [
        "# Prompts SHAP — full sample readout",
        "",
        "**Last updated:** Generated from analysis outputs.",
        "**Scope:** SHAP for the **prompts-only** model (one-hot encoded classification dimensions only) computed on the **full classified cohort** — all agents with classifications, no sample cap.",
        "",
        "---",
        "",
        "## 1. Methodology",
        "",
        "- **Model:** Random Forest (n_estimators=100, max_depth=10) predicting success vs non-success. Features = one-hot encoded classification dimensions (14 dimensions, `business_items` excluded); `unknown` kept as a category.",
        "- **SHAP:** TreeExplainer with background and `shap_values` computed on the **full** feature matrix (all agents in the classified cohort). No 500-agent or other sample limit.",
        "- **Outputs:** Mean SHAP and mean |SHAP| per feature over all agents; beeswarm and bar plots include **all** one-hot prompt features; average SHAP per feature value (value=0 vs value=1) over full cohort.",
        "- **Cohort:** Same as main agent success readout (success = used at least once after 7 days and still active; failure = inactive/deleted; dormant = active but no use after 7 days). Only agents in `agent_classifications.csv` are included.",
        "",
        "---",
        "",
        "## 2. SHAP direction (full cohort)",
        "",
        "Mean signed SHAP and mean absolute SHAP per feature over **all** agents. Positive mean SHAP → feature associated with higher success; negative → lower success.",
        "",
    ]

    if shap_dir_path.exists():
        df = pd.read_csv(shap_dir_path)
        df = df.sort_values("mean_abs_shap", ascending=False)
        lines.append(f"Full table: [classification_prompts_only_shap_direction.csv](../analysis/output/classification_prompts_only_shap_direction.csv).")
        lines.append("")
        lines.append(f"**Top {TOP_N_DIRECTION} features by mean absolute SHAP**")
        lines.append("")
        lines.append("| Feature | mean_shap | mean_abs_shap |")
        lines.append("|---------|-----------|---------------|")
        for _, r in df.head(TOP_N_DIRECTION).iterrows():
            lines.append(f"| {r['feature']} | {r['mean_shap']:.4f} | {r['mean_abs_shap']:.4f} |")
        lines.append("")
    else:
        lines.append("*Run `classification_success_analysis.py` to generate classification_prompts_only_shap_direction.csv.*")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. SHAP beeswarm",
        "",
        "Beeswarm plot: SHAP value (x) vs feature (y) for **all** one-hot prompt features. Each point is one agent (full cohort).",
        "",
    ])
    if beeswarm_path.exists():
        lines.append("![SHAP beeswarm – prompts-only, full sample](../analysis/output/classification_prompts_only_shap_beeswarm.png)")
    else:
        lines.append("*Run `classification_success_analysis.py` to generate classification_prompts_only_shap_beeswarm.png.*")
    lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. SHAP bar (mean |SHAP|)",
        "",
        "Bar plot of mean absolute SHAP per feature — **all** prompt features included.",
        "",
    ])
    if bar_path.exists():
        lines.append("![SHAP bar – prompts-only, full sample](../analysis/output/classification_prompts_only_shap_bar.png)")
    else:
        lines.append("*Run `classification_success_analysis.py` to generate classification_prompts_only_shap_bar.png.*")
    lines.append("")

    lines.extend([
        "---",
        "",
        "## 5. Average SHAP per feature value",
        "",
        "For each one-hot feature: mean SHAP when **value=0** vs **value=1** over the full cohort. Value=1 with positive mean_shap → feature pushes toward success; value=1 with negative mean_shap → toward failure.",
        "",
    ])
    if shap_by_val_path.exists():
        by_val = pd.read_csv(shap_by_val_path)
        # Show value=1 rows, sorted by |mean_shap| descending
        v1 = by_val[by_val["value"] == 1].copy()
        v1["abs_mean_shap"] = v1["mean_shap"].abs()
        v1 = v1.sort_values("abs_mean_shap", ascending=False).head(TOP_N_BY_VALUE)
        lines.append("Full table: [classification_prompts_only_shap_by_value.csv](../analysis/output/classification_prompts_only_shap_by_value.csv).")
        lines.append("")
        lines.append(f"**Top {TOP_N_BY_VALUE} features (value=1) by |mean SHAP|**")
        lines.append("")
        lines.append("| Feature | value | mean_shap | n_agents |")
        lines.append("|---------|-------|-----------|----------|")
        for _, r in v1.iterrows():
            lines.append(f"| {r['feature']} | {int(r['value'])} | {r['mean_shap']:.4f} | {int(r['n_agents'])} |")
        lines.append("")
    else:
        lines.append("*Run `classification_success_analysis.py` to generate classification_prompts_only_shap_by_value.csv.*")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Readout built by analysis/build_prompts_shap_full_sample_readout.py from classification_success_analysis.py outputs.*")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    READOUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {READOUT_MD}")

    # Build HTML (same data as MD)
    html_parts = []
    html_parts.append('<h2 id="methodology">1. Methodology</h2>')
    html_parts.append("<ul>")
    html_parts.append("<li><strong>Model:</strong> Random Forest (n_estimators=100, max_depth=10) predicting success vs non-success. Features = one-hot encoded classification dimensions (14 dimensions, <code>business_items</code> excluded); <code>unknown</code> kept as a category.</li>")
    html_parts.append("<li><strong>SHAP:</strong> TreeExplainer with background and <code>shap_values</code> computed on the <strong>full</strong> feature matrix (all agents in the classified cohort). No 500-agent or other sample limit.</li>")
    html_parts.append("<li><strong>Outputs:</strong> Mean SHAP and mean |SHAP| per feature over all agents; beeswarm and bar plots include <strong>all</strong> one-hot prompt features; average SHAP per feature value (value=0 vs value=1) over full cohort.</li>")
    html_parts.append("<li><strong>Cohort:</strong> Same as main agent success readout (success = used at least once after 7 days and still active; failure = inactive/deleted; dormant = active but no use after 7 days). Only agents in <code>agent_classifications.csv</code> are included.</li>")
    html_parts.append("</ul>")
    html_parts.append("<hr>")
    html_parts.append('<h2 id="shap-direction">2. SHAP direction (full cohort)</h2>')
    html_parts.append("<p>Mean signed SHAP and mean absolute SHAP per feature over <strong>all</strong> agents. Positive mean SHAP → feature associated with higher success; negative → lower success.</p>")
    if shap_dir_path.exists():
        df = pd.read_csv(shap_dir_path)
        df = df.sort_values("mean_abs_shap", ascending=False)
        html_parts.append('<p>Full table: <a href="../analysis/output/classification_prompts_only_shap_direction.csv">classification_prompts_only_shap_direction.csv</a>.</p>')
        html_parts.append(f"<h3>Top {TOP_N_DIRECTION} features by mean absolute SHAP</h3>")
        html_parts.append("<table><tr><th>Feature</th><th>mean_shap</th><th>mean_abs_shap</th></tr>")
        for _, r in df.head(TOP_N_DIRECTION).iterrows():
            feat = html_module.escape(str(r["feature"]))
            html_parts.append(f"<tr><td>{feat}</td><td>{r['mean_shap']:.4f}</td><td>{r['mean_abs_shap']:.4f}</td></tr>")
        html_parts.append("</table>")
    else:
        html_parts.append("<p><em>Run <code>classification_success_analysis.py</code> to generate classification_prompts_only_shap_direction.csv.</em></p>")
    html_parts.append("<hr>")
    html_parts.append('<h2 id="shap-beeswarm">3. SHAP beeswarm</h2>')
    html_parts.append("<p>Beeswarm plot: SHAP value (x) vs feature (y) for <strong>all</strong> one-hot prompt features. Each point is one agent (full cohort).</p>")
    if beeswarm_path.exists():
        html_parts.append('<p><img src="../analysis/output/classification_prompts_only_shap_beeswarm.png" alt="SHAP beeswarm – prompts-only, full sample" width="800"></p>')
    else:
        html_parts.append("<p><em>Run <code>classification_success_analysis.py</code> to generate the beeswarm image.</em></p>")
    html_parts.append("<hr>")
    html_parts.append('<h2 id="shap-bar">4. SHAP bar (mean |SHAP|)</h2>')
    html_parts.append("<p>Bar plot of mean absolute SHAP per feature — <strong>all</strong> prompt features included.</p>")
    if bar_path.exists():
        html_parts.append('<p><img src="../analysis/output/classification_prompts_only_shap_bar.png" alt="SHAP bar – prompts-only, full sample" width="800"></p>')
    else:
        html_parts.append("<p><em>Run <code>classification_success_analysis.py</code> to generate the bar image.</em></p>")
    html_parts.append("<hr>")
    html_parts.append('<h2 id="shap-by-value">5. Average SHAP per feature value</h2>')
    html_parts.append("<p>For each one-hot feature: mean SHAP when <strong>value=0</strong> vs <strong>value=1</strong> over the full cohort. Value=1 with positive mean_shap → feature pushes toward success; value=1 with negative mean_shap → toward failure.</p>")
    if shap_by_val_path.exists():
        by_val = pd.read_csv(shap_by_val_path)
        v1 = by_val[by_val["value"] == 1].copy()
        v1["abs_mean_shap"] = v1["mean_shap"].abs()
        v1 = v1.sort_values("abs_mean_shap", ascending=False).head(TOP_N_BY_VALUE)
        html_parts.append('<p>Full table: <a href="../analysis/output/classification_prompts_only_shap_by_value.csv">classification_prompts_only_shap_by_value.csv</a>.</p>')
        html_parts.append(f"<h3>Top {TOP_N_BY_VALUE} features (value=1) by |mean SHAP|</h3>")
        html_parts.append("<table><tr><th>Feature</th><th>value</th><th>mean_shap</th><th>n_agents</th></tr>")
        for _, r in v1.iterrows():
            feat = html_module.escape(str(r["feature"]))
            html_parts.append(f"<tr><td>{feat}</td><td>{int(r['value'])}</td><td>{r['mean_shap']:.4f}</td><td>{int(r['n_agents'])}</td></tr>")
        html_parts.append("</table>")
    else:
        html_parts.append("<p><em>Run <code>classification_success_analysis.py</code> to generate classification_prompts_only_shap_by_value.csv.</em></p>")
    html_parts.append("<hr>")
    html_parts.append('<p class="note">Readout built by analysis/build_prompts_shap_full_sample_readout.py from classification_success_analysis.py outputs.</p>')
    html_full = HTML_HEADER + "\n".join(html_parts) + "\n</body>\n</html>"
    READOUT_HTML.write_text(html_full, encoding="utf-8")
    print(f"Wrote {READOUT_HTML}")


if __name__ == "__main__":
    main()
