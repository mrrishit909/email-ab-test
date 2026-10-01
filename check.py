"""The project's check: the hand-written statistics agree with scipy, and every saved result recomputes.

    ./venv/bin/python check.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from abstats import CONTROL, holm, load, mde_rate, means, proportions, srm

HERE = Path(__file__).parent
RES = HERE / "results"


def main():
    d = load()
    assert len(d) == 64_000 and d["conversion"].eq(d["spend"].gt(0).astype(int)).all(), "a buyer always has spend > 0"

    # 1. formulas vs scipy
    c, m = d[d["segment"] == CONTROL], d[d["segment"] == "Mens E-Mail"]
    assert np.isclose(means(m["spend"], c["spend"])["p"], stats.ttest_ind(m["spend"], c["spend"], equal_var=False).pvalue)
    for col in ["visit", "conversion"]:
        table = [[m[col].sum(), len(m) - m[col].sum()], [c[col].sum(), len(c) - c[col].sum()]]
        assert np.isclose(proportions(m[col].sum(), len(m), c[col].sum(), len(c))["p"],
                          stats.chi2_contingency(table, correction=False)[1]), col
    counts = d["segment"].value_counts().values
    assert np.isclose(srm(counts, [1 / 3] * 3)[1], stats.chisquare(counts).pvalue)
    assert np.allclose(holm([0.01, 0.04, 0.03, 0.005]), [0.03, 0.06, 0.06, 0.02]), "Holm worked example"
    p0, n = 0.1, 20_000
    delta = mde_rate(p0, n)
    se = np.sqrt(2 * p0 * (1 - p0) / n)
    assert np.isclose(stats.norm.cdf(delta / se - stats.norm.ppf(0.975)), 0.8), "MDE gives 80% power by construction"

    # 2. saved results recompute from the raw file
    eff = pd.read_csv(RES / "effects.csv")
    for r in eff.itertuples():
        t, k = d[d["segment"] == r.treated_group][r.metric], d[d["segment"] == r.control_group][r.metric]
        assert np.isclose(r.treated, t.mean()) and np.isclose(r.control, k.mean()) and r.n_treated == len(t), r
        assert r.lo < r.diff < r.hi
    spend = eff[eff["metric"] == "spend"]
    assert ((spend["boot_lo"] - spend["lo"]).abs() < 0.05).all() and ((spend["boot_hi"] - spend["hi"]).abs() < 0.05).all(), \
        "bootstrap and Welch intervals should nearly agree"
    vs_none = eff[eff["control_group"] == CONTROL]
    assert (vs_none["p_holm"] < 0.05).all() and (vs_none["p_holm"] >= vs_none["p"]).all()

    rnd = json.loads((RES / "randomization.json").read_text())
    assert rnd["srm_p"] > 0.01 and rnd["max_abs_smd"] < 0.1 and sum(rnd["counts"].values()) == 64_000

    aa = json.loads((RES / "power.json").read_text())["aa_false_positive_rate"]
    for k in ["visit", "spend", "conversion_fisher"]:
        assert 0.03 <= aa[k] <= 0.07, f"A/A false-positive rate for {k} is {aa[k]}: the test is miscalibrated"

    seg = pd.read_csv(RES / "segments.csv")
    assert seg["n_email"].sum() + seg.groupby("segment")["n_none"].first().sum() == 64_000 - (d["mens"].eq(0) & d["womens"].eq(0)).sum()

    html = (HERE / "report.html").read_text()
    men = vs_none[(vs_none["treated_group"] == "Mens E-Mail") & (vs_none["metric"] == "spend")].iloc[0]
    assert f"${men['diff']:.2f}" in html, "report is stale: rerun report.py"

    print(f"OK: formulas match scipy, {len(eff)} effects recompute from the raw file, randomization holds, "
          f"A/A false-positive rates {aa['visit']:.1%} / {aa['spend']:.1%} / {aa['conversion_fisher']:.1%}")


if __name__ == "__main__":
    main()
