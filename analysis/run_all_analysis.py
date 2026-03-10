#!/usr/bin/env python3
"""
Run the full agent success and retention analysis pipeline in order:
1. Define success cohort
2. Trigger success analysis
3. Tool success analysis
4. Classification success analysis

Run from repo root: python analysis/run_all_analysis.py
Or from analysis/: python run_all_analysis.py
"""
import sys
from pathlib import Path

# Ensure we can import analysis modules
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

def main():
    print("=" * 60)
    print("1. Defining success cohort...")
    print("=" * 60)
    from define_success_cohort import main as run_cohort
    run_cohort()

    print("\n" + "=" * 60)
    print("2. Trigger success analysis...")
    print("=" * 60)
    from trigger_success_analysis import main as run_trigger
    run_trigger()

    print("\n" + "=" * 60)
    print("3. Tool success analysis...")
    print("=" * 60)
    from tool_success_analysis import main as run_tool
    run_tool()

    print("\n" + "=" * 60)
    print("4. Classification success analysis...")
    print("=" * 60)
    from classification_success_analysis import main as run_class
    run_class()

    print("\n" + "=" * 60)
    print("Done. Outputs in analysis/output/. Update docs/agent_success_retention_readout.md with results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
