"""Step 5 (exploratory): does each e-mail work differently depending on what the customer bought before?

    ./venv/bin/python segments.py

Customers are split by past purchases: men's merchandise only, women's only, or both. Within each segment the
e-mail is still randomized, so each effect is fair; but with 6 segment effects per metric, a "surprise" could
be luck, so these are leads for the next test, not conclusions. The interaction test asks whether the men's
e-mail's effect on spend really differs between men's-only and women's-only buyers.

results/segments.csv and results/segments.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from abstats import CONTROL, GROUPS, load, means, proportions

HERE = Path(__file__).parent
SEGMENTS = {"Bought men's only": (1, 0), "Bought women's only": (0, 1), "Bought both": (1, 1)}


def main():
    d = load()
    rows = []
    for seg, (m, w) in SEGMENTS.items():
        s = d[(d["mens"] == m) & (d["womens"] == w)]
        for g in ["Mens E-Mail", "Womens E-Mail"]:
            a, b = s[s["segment"] == g], s[s["segment"] == CONTROL]
            sp = means(a["spend"], b["spend"])
            vi = proportions(a["visit"].sum(), len(a), b["visit"].sum(), len(b))
            rows.append({"segment": seg, "email": GROUPS[g], "n_email": len(a), "n_none": len(b),
                         "spend_diff": sp["diff"], "spend_lo": sp["lo"], "spend_hi": sp["hi"], "spend_p": sp["p"],
                         "visit_diff": vi["diff"], "visit_lo": vi["lo"], "visit_hi": vi["hi"], "visit_p": vi["p"]})
    seg = pd.DataFrame(rows)

    def interaction(email, metric, seg1, seg2):
        """Does the e-mail's effect differ between two segments? z-test on the difference of the two effects."""
        e = seg[seg["email"] == email].set_index("segment")
        a, b = e.loc[seg1], e.loc[seg2]
        se = lambda r: (r[f"{metric}_hi"] - r[f"{metric}_lo"]) / (2 * stats.norm.ppf(0.975))
        gap = a[f"{metric}_diff"] - b[f"{metric}_diff"]
        return {"email": email, "metric": metric, "segments": f"{seg1} minus {seg2}", "gap": round(float(gap), 4),
                "p": round(float(2 * stats.norm.sf(abs(gap / np.sqrt(se(a) ** 2 + se(b) ** 2)))), 6)}

    out = {
        # written into this script before the segment table was first run
        "chosen_before_looking": interaction("Men's e-mail", "spend", "Bought men's only", "Bought women's only"),
        # spotted in the table afterwards: a lead for the next test, not a finding
        "spotted_after_looking": interaction("Women's e-mail", "visit", "Bought women's only", "Bought men's only"),
    }
    seg.round(6).to_csv(HERE / "results" / "segments.csv", index=False)
    (HERE / "results" / "segments.json").write_text(json.dumps(out, indent=2) + "\n")
    print(seg[["segment", "email", "n_email", "spend_diff", "spend_lo", "spend_hi", "visit_diff", "visit_lo", "visit_hi"]].round(4).to_string(index=False))
    print(out)


if __name__ == "__main__":
    main()
