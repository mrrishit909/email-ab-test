"""Step 3: what did each e-mail do in the two weeks after it was sent?

    ./venv/bin/python effects.py

Primary metric: spend per customer (what the business keeps). Secondary: visited the site, bought anything.
Each e-mail vs no e-mail = 6 tests, Holm-adjusted as one family; men's vs women's e-mail = 3 more, a second family.
Spend gets a bootstrap CI next to Welch's, because 99% of customers spent $0.

results/effects.csv
"""
from pathlib import Path

import pandas as pd

from abstats import CONTROL, GROUPS, bootstrap, fisher, holm, load, means, proportions

HERE = Path(__file__).parent
METRICS = {"spend": "Spend per customer ($)", "visit": "Visited the site", "conversion": "Bought anything"}


def compare(d, treated, control):
    a, b = d[d["segment"] == treated], d[d["segment"] == control]
    rows = []
    for m in METRICS:
        if m == "spend":
            r = means(a[m], b[m])
            r["boot_lo"], r["boot_hi"] = bootstrap(a[m].values, b[m].values)
        else:
            r = proportions(a[m].sum(), len(a), b[m].sum(), len(b))
            r["p_fisher"] = fisher(a[m], b[m])
        rows.append({"treated_group": treated, "control_group": control, "metric": m, "n_treated": len(a),
                     "n_control": len(b), **r})
    return rows


def main():
    d = load()
    vs_none = pd.DataFrame(compare(d, "Mens E-Mail", CONTROL) + compare(d, "Womens E-Mail", CONTROL))
    vs_none["p_holm"] = holm(vs_none["p"])
    head = pd.DataFrame(compare(d, "Mens E-Mail", "Womens E-Mail"))
    head["p_holm"] = holm(head["p"])
    out = pd.concat([vs_none, head], ignore_index=True)
    for g in GROUPS:
        out.loc[out["treated_group"] == g, "treated_label"] = GROUPS[g]
        out.loc[out["control_group"] == g, "control_label"] = GROUPS[g]
    (HERE / "results").mkdir(exist_ok=True)
    out.round(8).to_csv(HERE / "results" / "effects.csv", index=False)
    show = out[["treated_label", "control_label", "metric", "treated", "control", "diff", "lo", "hi", "lift", "p_holm", "p_fisher", "boot_lo", "boot_hi"]]
    print(show.round(5).to_string(index=False))


if __name__ == "__main__":
    main()
