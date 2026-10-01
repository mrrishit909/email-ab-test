"""Step 2: before reading any result, check the experiment itself: right group sizes, similar customers in each.

    ./venv/bin/python randomization.py

results/randomization.json and results/balance.csv
"""
import json
from pathlib import Path

import pandas as pd

from abstats import CONTROL, GROUPS, load, smd, srm

HERE = Path(__file__).parent


def covariates(d):
    """Everything known about a customer before the e-mail, as numbers (categories become 0/1 columns)."""
    x = d[["recency", "history", "mens", "womens", "newbie"]].copy()
    for col in ["zip_code", "channel", "history_segment"]:
        x = x.join(pd.get_dummies(d[col], prefix=col, dtype=float))
    return x


def main():
    d = load()
    counts = d["segment"].value_counts().reindex(list(GROUPS))
    chi2, p = srm(counts.values, [1 / 3] * 3)
    x = covariates(d)
    rows = []
    for g in GROUPS:
        if g == CONTROL:
            continue
        for col in x.columns:
            rows.append({"group": g, "covariate": col, "treated": x.loc[d["segment"] == g, col].mean(),
                         "control": x.loc[d["segment"] == CONTROL, col].mean(),
                         "smd": smd(x.loc[d["segment"] == g, col], x.loc[d["segment"] == CONTROL, col])})
    bal = pd.DataFrame(rows)
    worst = bal.loc[bal["smd"].abs().idxmax()]
    out = {"counts": counts.to_dict(), "srm_chi2": round(chi2, 3), "srm_p": round(p, 4),
           "covariates_checked": int(x.shape[1]), "max_abs_smd": round(abs(worst["smd"]), 4),
           "max_abs_smd_at": f"{worst['covariate']} ({worst['group']})"}
    (HERE / "results").mkdir(exist_ok=True)
    bal.round(5).to_csv(HERE / "results" / "balance.csv", index=False)
    (HERE / "results" / "randomization.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    assert p > 0.01, "group sizes don't match a 1/3 split: stop and investigate before reading results"
    assert abs(worst["smd"]) < 0.1, "groups differ before the e-mail: randomization looks broken"


if __name__ == "__main__":
    main()
