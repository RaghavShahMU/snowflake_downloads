#!/usr/bin/env python3
"""Regenerate dimension tables in prompts_classification_readout_plain.html; CEO-oriented pass (glossary rekey, appendix fold, Finding 3 drop)."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pandas as pd

from _utils import OUTPUT_DIR

REPO = Path(__file__).resolve().parents[1]
HTML_PATH = REPO / "docs" / "prompts_classification_readout_plain.html"
MD_PATH = REPO / "semantic_layer" / "models" / "agent_classifications.md"

SECTIONS = [
    ("2-execution-dataset", "execution_dataset"),
    ("1-functional-archetype", "functional_archetype"),
    ("domain-knowledge-depth", "domain_knowledge_depth"),
    ("operational-scope", "operational_scope"),
    ("data-flow-direction", "data_flow_direction"),
    ("autonomy-level", "autonomy_level"),
    ("tone-and-persona", "tone_and_persona"),
    ("domain-industry-vertical", "domain_industry_vertical"),
    ("external-integration-scope", "external_integration_scope"),
    ("use-case-context", "use_case_context"),
    ("implied-end-date", "implied_end_date"),
]

DIM_REGEX = re.compile(
    r"### \d+\. `([a-z_]+)`\s*\n+.*?"
    r"\n\| Option \| Description \|\n\|(?:[-\s|]+)\|\n"
    r"((?:\| `[^`]+` \| [^\n]*\|\n)+)",
    re.DOTALL,
)


def parse_md_descriptions(md_path: Path) -> dict[str, dict[str, str]]:
    text = md_path.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {}
    for m in DIM_REGEX.finditer(text):
        dim = m.group(1)
        block = m.group(2)
        out.setdefault(dim, {})
        for line in block.strip().split("\n"):
            line = line.strip()
            if not line.startswith("| `"):
                continue
            parts = [x.strip() for x in line.split("|")]
            if len(parts) < 3:
                continue
            opt_raw = parts[1]
            desc = parts[2] if len(parts) > 2 else ""
            om = re.match(r"`([^`]+)`", opt_raw)
            if om:
                out[dim][om.group(1)] = desc
    return out


def fmt_multiline_cell(s: str) -> str:
    if pd.isna(s) or str(s).strip() in ("", "—"):
        return "—"
    raw = str(s).strip()
    parts = [html.escape(p.strip()) for p in raw.split(";") if p.strip()]
    return "<br>".join(parts)


def build_table_rows(dim: str, descriptions: dict[str, dict[str, str]]) -> str:
    cdf_path = OUTPUT_DIR / f"classification_dim_{dim}.csv"
    if not cdf_path.exists():
        return ""
    cdf = pd.read_csv(cdf_path)
    val_col = cdf.columns[0]
    cdf = cdf.rename(columns={val_col: "value"})
    dim_desc = descriptions.get(dim, {})

    tpath = OUTPUT_DIR / f"prompts_readout_top_tools_{dim}.csv"
    ppath = OUTPUT_DIR / f"prompts_readout_top_prompts_{dim}.csv"
    tdf = pd.read_csv(tpath) if tpath.exists() else pd.DataFrame()
    pdf = pd.read_csv(ppath) if ppath.exists() else pd.DataFrame()
    if not tdf.empty:
        tdf = tdf.set_index("value")
    if not pdf.empty:
        pdf = pdf.set_index("value")

    lines = [
        '  <tr><th>Value</th><th>What each value means</th><th>Dormant</th><th>Failure</th>'
        '<th>Success</th><th>Success rate</th><th>Related tools (positive r)</th>'
        '<th>Related tools (negative r)</th><th>Related prompt patterns (positive r)</th>'
        '<th>Related prompt patterns (negative r)</th></tr>',
    ]
    gloss_prefix = dim + "_"
    for _, row in cdf.iterrows():
        v = str(row["value"])
        term = gloss_prefix + v.replace(" ", "_")
        tp = tdf.loc[v, "top_tools_pos"] if not tdf.empty and v in tdf.index else "—"
        tn = tdf.loc[v, "top_tools_neg"] if not tdf.empty and v in tdf.index else "—"
        pp = pdf.loc[v, "top_prompts_pos"] if not pdf.empty and v in pdf.index else "—"
        pn = pdf.loc[v, "top_prompts_neg"] if not pdf.empty and v in pdf.index else "—"
        desc = dim_desc.get(v, "—")
        sr = row.get("success_rate", 0)
        try:
            sr_f = float(sr)
        except (TypeError, ValueError):
            sr_f = 0.0
        lines.append(
            f'\n  <tr><td><span class="glossary" data-term="{html.escape(term)}">{html.escape(v)}</span></td>'
            f"<td>{html.escape(desc)}</td>"
            f"<td>{int(row.get('dormant', 0))}</td><td>{int(row.get('failure', 0))}</td>"
            f"<td>{int(row.get('success', 0))}</td><td>{sr_f:.2f}</td>"
            f"<td>{fmt_multiline_cell(tp)}</td><td>{fmt_multiline_cell(tn)}</td>"
            f"<td>{fmt_multiline_cell(pp)}</td><td>{fmt_multiline_cell(pn)}</td></tr>"
        )
    return "".join(lines)


def remove_finding_3(text: str) -> str:
    return re.sub(
        r"<details><summary><strong>Finding 3.*?</details>\s*",
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )


def rekey_glossary_json(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        raw = m.group(1)
        data = json.loads(raw)
        new_data = {k.replace("=", "_"): v for k, v in data.items()}
        return (
            '<script type="application/json" id="glossary-data">'
            + json.dumps(new_data, separators=(",", ":"))
            + "</script>"
        )

    return re.sub(
        r'<script type="application/json" id="glossary-data">(.*?)</script>',
        repl,
        text,
        count=1,
        flags=re.DOTALL,
    )


def dim_value_labels(text: str) -> str:
    dims = (
        r"functional_archetype|execution_dataset|domain_knowledge_depth|operational_scope|"
        r"data_flow_direction|autonomy_level|tone_and_persona|domain_industry_vertical|"
        r"external_integration_scope|use_case_context|implied_end_date|team_orientation|"
        r"state_persistence|output_modality"
    )
    text = re.sub(rf"\b({dims})=([a-z0-9_]+)\b", r"\1_\2", text)
    text = re.sub(r"\btrigger=([a-z0-9_]+)\b", r"trigger_\1", text)
    return text


def patch_distribution_tables(text: str, descriptions: dict[str, dict[str, str]]) -> str:
    for h3_id, dim in SECTIONS:
        table_body = build_table_rows(dim, descriptions)
        if not table_body:
            continue
        pat = (
            rf'(<h3 id="{re.escape(h3_id)}">.*?</h3>\s*'
            r"<h4>Classification</h4>\s*<p>.*?</p>\s*"
            r'<h4>Distribution</h4>\s*<table>\s*)(.*?)(\s*</table>)'
        )
        text_new, n = re.subn(pat, rf"\1\n{table_body}\n\3", text, count=1, flags=re.DOTALL)
        if n != 1:
            raise RuntimeError(f"Could not patch table for {h3_id} ({dim})")
        text = text_new
    return text


def wrap_appendix(text: str) -> str:
    if "Full detail — additional dimensions" in text:
        return text
    start = text.find('<h2 id="other-classification-dimensions">')
    if start == -1:
        return text
    end = text.find('<h2 id="methodology-and-footnotes">', start)
    if end == -1:
        return text
    block = text[start:end]
    inner = block.replace(
        '<h2 id="other-classification-dimensions">Other classification dimensions</h2>',
        "",
        1,
    )
    wrapped = (
        '<h2 id="other-classification-dimensions">Other classification dimensions</h2>\n'
        "<details><summary><strong>Full detail — additional dimensions</strong> "
        "(open only if you need the full tables)</summary>\n"
        + inner.strip()
        + "\n</details>\n\n"
    )
    return text[:start] + wrapped + text[end:]


def main():
    descriptions = parse_md_descriptions(MD_PATH)
    text = HTML_PATH.read_text(encoding="utf-8")
    text = remove_finding_3(text)
    text = rekey_glossary_json(text)
    text = patch_distribution_tables(text, descriptions)
    text = dim_value_labels(text)
    text = wrap_appendix(text)
    HTML_PATH.write_text(text, encoding="utf-8")
    print(f"Updated {HTML_PATH}")


if __name__ == "__main__":
    main()
