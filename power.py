"""Step 4: how small an effect could this test see, and do the tests cry wolf on this data?

    ./venv/bin/python power.py

1. Minimum detectable effect (80% power, 5% two-sided) for each metric with ~21,300 customers per group.
2. Customers per group needed to detect the men's-vs-women's spend gap that was observed.
3. A/A test: split the no-e-mail group in half at random 1,000 times. Nothing differs, so about 5% of tests
   should come out "significant". Much more would mean the methods are wrong for this data (e.g. spend's long tail).
   Purchases are rare (about 61 per half), so Fisher's exact test runs alongside the z-test.

results/power.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from abstats import CONTROL, Z95, fisher, load, mde_mean, mde_rate, means, proportions

HERE = Path(__file__).parent


def main():
    d = load()
    c = d[d["segment"] == CONTROL]
    n = int(d["segment"].value_counts().min())
    mde = {
        "visit": mde_rate(c["visit"].mean(), n), "conversion": mde_rate(c["conversion"].mean(), n),
        "spend": mde_mean(c["spend"].std(ddof=1), n),
    }
    eff = pd.read_csv(HERE / "results" / "effects.csv")
    gap = eff[(eff["treated_group"] == "Mens E-Mail") & (eff["control_group"] == "Womens E-Mail") & (eff["metric"] == "spend")].iloc[0]
    sd = d.loc[d["segment"] != CONTROL, "spend"].std(ddof=1)
    n_needed = 2 * ((Z95 + stats.norm.ppf(0.8)) * sd / gap["diff"]) ** 2
    power_for_gap = stats.norm.cdf(gap["diff"] / (sd * np.sqrt(2 / n)) - Z95)

    rng = np.random.default_rng(0)
    hits = {"visit": 0, "conversion": 0, "conversion_fisher": 0, "spend": 0}
    reps = 1000
    for _ in range(reps):
        half = rng.permutation(len(c)) < len(c) // 2
        a, b = c[half], c[~half]
        hits["spend"] += means(a["spend"], b["spend"])["p"] < 0.05
        for m in ["visit", "conversion"]:
            hits[m] += proportions(a[m].sum(), len(a), b[m].sum(), len(b))["p"] < 0.05
        hits["conversion_fisher"] += fisher(a["conversion"], b["conversion"]) < 0.05

    out = {
        "n_per_group": n,
        "control_rates": {m: round(float(c[m].mean()), 6) for m in ["visit", "conversion", "spend"]},
        "mde": {m: round(float(v), 6) for m, v in mde.items()},
        "mde_relative": {m: round(float(mde[m] / c[m].mean()), 4) for m in mde},
        "mens_vs_womens_spend_gap": round(float(gap["diff"]), 5),
        "customers_per_group_to_detect_gap": int(np.ceil(n_needed)),
        "power_for_gap_at_this_size": round(float(power_for_gap), 3),
        "aa_reps": reps, "aa_false_positive_rate": {m: hits[m] / reps for m in hits},
    }
    (HERE / "results" / "power.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
