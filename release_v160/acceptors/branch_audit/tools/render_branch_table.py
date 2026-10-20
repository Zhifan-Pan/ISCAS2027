"""Render the descriptive S14 table from an independently generated audit.json."""
import argparse
import json
from pathlib import Path


def render(audit):
    lines = [
        r"\begin{center}\small",
        r"\textbf{Table S15 (continued).} H3-minus-H4 branch contributions (pp). "
        r"Each term retains the full-language reference denominators.\\[4pt]",
        r"\begin{tabular}{@{}llrrr@{}}\toprule",
        r"Corpus & Checkpoint & Complete $S$ gap & Nontrigger & Trigger ($T$ gap)\\\midrule",
    ]
    for panel in audit["branch_comparisons"]:
        for index, row in enumerate(panel["checkpoint"], 1):
            lines.append(
                f"{panel['corpus']} & {index} & "
                f"{row['complete_difference_pp']:.6f} & "
                f"{row['nontrigger_contribution_pp']:.6f} & "
                f"{row['trigger_contribution_pp']:.6f}" + r"\\"
            )
        row = panel["average"]
        lines.append(
            f"{panel['corpus']} & Mean & "
            f"{row['complete_difference_pp']:.6f} & "
            f"{row['nontrigger_contribution_pp']:.6f} & "
            f"{row['trigger_contribution_pp']:.6f}" + r"\\"
        )
        if panel["corpus"] == "FLEURS":
            lines.append(r"\midrule")
    lines.append(r"\bottomrule\end{tabular}\end{center}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render(json.loads(args.audit.read_text())), encoding="utf-8")
