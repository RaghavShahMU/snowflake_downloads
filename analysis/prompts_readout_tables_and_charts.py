#!/usr/bin/env python3
"""
Build per-dimension, per-value: top 3 tools (pos/neg), top 3 other-prompts (pos/neg) with |r|>=0.05,
and bar charts (count + success rate) for the prompts classification readout.
Outputs: prompts_readout_top_tools_<dim>.csv, prompts_readout_top_prompts_<dim>.csv, classification_dim_<dim>_bar.png
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

from _utils import OUTPUT_DIR

# 11 dimensions kept in readout (after removing team_orientation, output_modality, state_persistence)
DIMS_11 = [
    "functional_archetype", "execution_dataset", "domain_knowledge_depth", "operational_scope",
    "data_flow_direction", "autonomy_level", "tone_and_persona", "domain_industry_vertical",
    "external_integration_scope", "use_case_context", "implied_end_date",
]
THRESHOLD = 0.05
TOP_N = 3


def fmt_corr(rows):
    """Format list of (name, r) as 'name r; name r'."""
    return "; ".join(f"{name} {r:.2f}" for name, r in rows[:TOP_N])


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Top tools per value (from prompts_readout_correlation_<dim>.csv, tools only) ---
    for dim in DIMS_11:
        path = OUTPUT_DIR / f"prompts_readout_correlation_{dim}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        # Tools = external_feature not starting with trigger= or template=
        tools_df = df[
            ~df["external_feature"].str.startswith("trigger=") & ~df["external_feature"].str.startswith("template=")
        ].copy()
        tools_df["value"] = tools_df["classification_feature"].str.replace(f"{dim}=", "", regex=False)
        rows_out = []
        for value, grp in tools_df.groupby("value"):
            pos = grp[grp["correlation"] >= THRESHOLD].nlargest(TOP_N, "correlation")[
                ["external_feature", "correlation"]
            ].values.tolist()
            neg = grp[grp["correlation"] <= -THRESHOLD].nsmallest(TOP_N, "correlation")[
                ["external_feature", "correlation"]
            ].values.tolist()
            rows_out.append({
                "value": value,
                "top_tools_pos": fmt_corr([(x[0], x[1]) for x in pos]) if pos else "—",
                "top_tools_neg": fmt_corr([(x[0], x[1]) for x in neg]) if neg else "—",
            })
        pd.DataFrame(rows_out).to_csv(OUTPUT_DIR / f"prompts_readout_top_tools_{dim}.csv", index=False)
    print("Wrote prompts_readout_top_tools_<dim>.csv")

    # --- Top other-prompts per value (from full_feature_corr_prompts_vs_prompts.csv) ---
    corr_pp_path = OUTPUT_DIR / "full_feature_corr_prompts_vs_prompts.csv"
    if not corr_pp_path.exists():
        print("Skip top prompts: full_feature_corr_prompts_vs_prompts.csv not found")
    else:
        corr_pp = pd.read_csv(corr_pp_path, index_col=0)
        for dim in DIMS_11:
            prefix = f"{dim}="
            my_cols = [c for c in corr_pp.index if c.startswith(prefix)]
            other_cols = [c for c in corr_pp.columns if not c.startswith(prefix)]
            if not my_cols or not other_cols:
                continue
            rows_out = []
            for feat in my_cols:
                value = feat.replace(prefix, "")
                row = corr_pp.loc[feat, other_cols]
                if isinstance(row, pd.Series):
                    row = row.astype(float)
                else:
                    continue
                pos = row[row >= THRESHOLD].nlargest(TOP_N)
                neg = row[row <= -THRESHOLD].nsmallest(TOP_N)
                rows_out.append({
                    "value": value,
                    "top_prompts_pos": fmt_corr([(k, v) for k, v in pos.items()]) if len(pos) else "—",
                    "top_prompts_neg": fmt_corr([(k, v) for k, v in neg.items()]) if len(neg) else "—",
                })
            pd.DataFrame(rows_out).to_csv(OUTPUT_DIR / f"prompts_readout_top_prompts_{dim}.csv", index=False)
        print("Wrote prompts_readout_top_prompts_<dim>.csv")

    # --- Bar chart per dimension (count + success rate) ---
    for dim in DIMS_11:
        path = OUTPUT_DIR / f"classification_dim_{dim}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        # First column is value name (dim name as header)
        val_col = df.columns[0]
        df = df.rename(columns={val_col: "value"})
        df["total"] = df.get("dormant", 0) + df.get("failure", 0) + df.get("success", 0)
        df = df.sort_values("total", ascending=True)  # so first value at bottom
        values = df["value"].tolist()
        totals = df["total"].tolist()
        rates = (df["success_rate"] * 100).tolist()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, max(4, len(values) * 0.5)))
        y = np.arange(len(values))
        ax1.barh(y, totals, color="steelblue", alpha=0.8)
        ax1.set_yticks(y)
        ax1.set_yticklabels(values, fontsize=9)
        ax1.set_xlabel("Number of agents")
        ax1.set_title(f"{dim}: agent count by value")
        ax1.invert_yaxis()

        ax2.barh(y, rates, color="seagreen", alpha=0.8)
        ax2.set_yticks(y)
        ax2.set_yticklabels(values, fontsize=9)
        ax2.set_xlabel("Success rate (%)")
        ax2.set_title(f"{dim}: success rate by value")
        ax2.invert_yaxis()
        ax2.axvline(100 * 0.32, color="gray", linestyle="--", alpha=0.7, label="cohort avg")
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"classification_dim_{dim}_bar.png", dpi=150, bbox_inches="tight")
        plt.close()
    print("Wrote classification_dim_<dim>_bar.png")
    print("Done.")


if __name__ == "__main__":
    main()
