"""Step 6: the experiment readout, one page for the people who decide (report.html).

    ./venv/bin/python report.py

Every number is read from results/ (written by steps 2-5). Charts are inline SVG, no libraries.
"""
import json
from html import escape
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
RES = HERE / "results"
MENS, WOMENS = "#3987e5", "#d95926"            # same validated pair as the SQL project, on #0b0b0b
COLOR = {"Men's e-mail": MENS, "Women's e-mail": WOMENS}


def j(name):
    return json.loads((RES / name).read_text())


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def pts(x, d=1):
    return f"{100 * x:+.{d}f} pts"


def usd(x, sign=False):
    return f"{'+' if sign and x >= 0 else ''}{'-' if x < 0 else ''}${abs(x):,.2f}"


def forest(rows, fmt, title, width=880):
    """Dot = estimated effect, line = 95% confidence interval, dashed line = no effect."""
    lo = min(0, min(r["lo"] for r in rows))
    hi = max(r["hi"] for r in rows)
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    left, right, row_h, top = 200, 120, 34, 30
    x = lambda v: left + (v - lo) / (hi - lo) * (width - left - right)
    h = top + row_h * len(rows) + 10
    s = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="{escape(title)}">',
         f'<text x="0" y="16" class="t">{escape(title)}</text>',
         f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{top - 6}" y2="{h - 6}" class="z"/>']
    for i, r in enumerate(rows):
        y = top + row_h * i + row_h / 2
        c = r["color"]
        s += [f'<text x="0" y="{y + 4:.1f}" class="l">{escape(r["label"])}</text>',
              f'<line x1="{x(r["lo"]):.1f}" x2="{x(r["hi"]):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{c}" stroke-width="2"/>',
              f'<circle cx="{x(r["diff"]):.1f}" cy="{y:.1f}" r="6" fill="{c}" stroke="#0b0b0b" stroke-width="2"><title>'
              f'{escape(r["label"])}: {fmt(r["diff"])} (95% CI {fmt(r["lo"])} to {fmt(r["hi"])})</title></circle>',
              f'<text x="{width - right + 12}" y="{y + 4:.1f}" class="v">{fmt(r["diff"])}</text>']
    return "".join(s) + "</svg>"


def main():
    rnd, power, seg_tests = j("randomization.json"), j("power.json"), j("segments.json")
    eff = pd.read_csv(RES / "effects.csv")
    seg = pd.read_csv(RES / "segments.csv")
    vs = eff[eff["control_group"] == "No E-Mail"]
    head = eff[eff["treated_group"].eq("Mens E-Mail") & eff["control_group"].eq("Womens E-Mail")].set_index("metric")
    get = lambda t, m: vs[(vs["treated_label"] == t) & (vs["metric"] == m)].iloc[0]
    men_sp, wom_sp = get("Men's e-mail", "spend"), get("Women's e-mail", "spend")
    ctrl = power["control_rates"]
    aa = power["aa_false_positive_rate"]

    fmts = {"spend": lambda v: usd(v, True), "visit": lambda v: pts(v), "conversion": lambda v: pts(v, 2)}
    titles = {"spend": "Spend per customer, vs no e-mail", "visit": "Visited the site, vs no e-mail",
              "conversion": "Bought anything, vs no e-mail"}
    charts = "".join(
        f'<figure>{forest([{"label": t, "color": COLOR[t], **get(t, m)} for t in COLOR], fmts[m], titles[m])}</figure>'
        for m in ["spend", "visit", "conversion"])

    who = {"Bought men's only": "Men's-only buyers", "Bought women's only": "Women's-only buyers", "Bought both": "Bought both"}
    seg_rows = [{"label": f"{who[r.segment]} · {r.email.split()[0].lower()}", "color": COLOR[r.email],
                 "diff": r.visit_diff, "lo": r.visit_lo, "hi": r.visit_hi} for r in seg.itertuples()]
    seg_chart = forest(seg_rows, lambda v: pts(v), "Visited the site, vs no e-mail, by what the customer bought before")

    rows = []
    for t in COLOR:
        for m, name in [("spend", "Spend per customer"), ("visit", "Visited the site"), ("conversion", "Bought anything")]:
            r = get(t, m)
            f = fmts[m] if m != "spend" else (lambda v: usd(v, True))
            base = usd(r["control"]) if m == "spend" else pct(r["control"], 2 if m == "conversion" else 1)
            got = usd(r["treated"]) if m == "spend" else pct(r["treated"], 2 if m == "conversion" else 1)
            p = r["p_holm"]
            rows.append(f'<tr><td>{t}</td><td>{name}</td><td class="n">{base}</td><td class="n">{got}</td>'
                        f'<td class="n">{f(r["diff"])}</td><td class="n">{f(r["lo"])} to {f(r["hi"])}</td>'
                        f'<td class="n">{pct(r["lift"], 0)}</td><td class="n">{"&lt; 0.001" if p < 0.001 else f"{p:.3f}"}</td></tr>')
    table = ('<div class="tw"><table><thead><tr><th>E-mail</th><th>Metric</th><th class="n">No e-mail</th>'
             '<th class="n">E-mail</th><th class="n">Difference</th><th class="n">95% CI</th><th class="n">Lift</th>'
             '<th class="n">p (Holm)</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")

    before, after = seg_tests["chosen_before_looking"], seg_tests["spotted_after_looking"]
    wseg = seg[seg["email"] == "Women's e-mail"].set_index("segment")
    hs = head.loc["spend"]
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>E-mail Test Readout</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500&family=Geist+Mono&display=swap">
<style>
:root{{--bg:#000;--card:#0b0b0b;--fg:#f2f2f0;--dim:#8a8a87;--faint:#5c5c5a;--line:#1d1d1d}}
*{{box-sizing:border-box}}html{{background:var(--bg);color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:Geist,"Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.6;padding:32px 40px 60px;-webkit-font-smoothing:antialiased}}
main{{max-width:1000px;margin:0 auto}}a{{color:var(--fg)}}
.cap{{font-size:12px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}}
h1{{margin:10px 0 14px;font-size:clamp(40px,7vw,80px);line-height:.98;font-weight:500;letter-spacing:-.045em}}
.lede{{margin:0;max-width:62ch;color:var(--dim);font-size:clamp(16px,1.7vw,19px)}}
.decision{{margin:28px 0 0;padding:18px 20px;background:var(--card);border:1px solid var(--line);border-left:3px solid {MENS};border-radius:10px;max-width:80ch}}
.decision p{{margin:6px 0 0;color:#d6d6d3}}
section{{margin-top:36px;padding:26px 0 0;border-top:1px solid var(--line)}}
h2{{margin:0 0 8px;font-size:22px;font-weight:500;letter-spacing:-.015em}}
section p,section li{{max-width:74ch;color:#c9c9c6}}
.tw{{overflow-x:auto;margin:14px 0}}
table{{border-collapse:collapse;font-size:14px;min-width:100%}}
th,td{{padding:7px 14px 7px 0;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}
th{{font-size:12px;font-weight:500;letter-spacing:.06em;text-transform:uppercase;color:var(--dim)}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
figure{{margin:14px 0;padding:16px;background:var(--card);border:1px solid var(--line);border-radius:12px}}
svg{{display:block;width:100%;height:auto}}
.t{{fill:#f2f2f0;font:500 14px Geist,sans-serif}}.l{{fill:#c9c9c6;font:13px Geist,sans-serif}}.v{{fill:#f2f2f0;font:13px Geist,sans-serif;font-variant-numeric:tabular-nums}}
.z{{stroke:#5c5c5a;stroke-width:1;stroke-dasharray:4 3}}
.lg{{display:flex;gap:18px;margin:0 0 6px;font-size:13px;color:var(--dim)}}.lg i{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:6px;vertical-align:-1px}}
footer{{margin-top:48px;color:var(--faint)}}
@media (max-width:640px){{body{{padding:20px 20px 40px}}}}
</style></head>
<body><main>
<nav class="cap" style="display:flex;gap:28px;margin-bottom:6vh"><a style="text-decoration:none" href="https://mrrishit909.github.io/projects/email-ab-test/">&larr; How this was built</a><a style="text-decoration:none" href="https://mrrishit909.github.io/projects/">All projects</a></nav>
<p class="cap">Experiment readout · MineThatData e-mail test · 64,000 customers · 2-week window</p>
<h1>The men's e-mail won</h1>
<p class="lede">Customers who bought in the last year were split at random into three groups: a men's merchandise e-mail,
a women's merchandise e-mail, or no e-mail. Two weeks later, did the e-mails change what they did?</p>
<div class="decision"><span class="cap">Recommendation</span>
<p>Send the <b>men's e-mail</b>. It raised spend by {usd(men_sp["diff"])} per customer (95% CI {usd(men_sp["lo"])} to {usd(men_sp["hi"])}),
about {usd(1000 * men_sp["diff"]).split(".")[0]} more two-week revenue per 1,000 customers e-mailed, vs {usd(1000 * wom_sp["diff"]).split(".")[0]} for the women's e-mail.
That is revenue, not profit: the e-mail's cost and margins aren't in the data. Next, test the women's e-mail only on customers
who have bought women's merchandise (see section 4).</p></div>

<section><h2>1 · Was the test fair?</h2>
<p>Yes. Group sizes were {", ".join(f"{v:,}" for v in rnd["counts"].values())}: what a random one-third split produces
(sample-ratio test p = {rnd["srm_p"]:.2f}). Across {rnd["covariates_checked"]} things known before the e-mail (recency, past spend, channel,
area, new customer…), the groups differ by at most {rnd["max_abs_smd"]:.3f} standard deviations; 0.1 is the usual warning line.
So differences after the e-mail are caused by the e-mail.</p></section>

<section><h2>2 · What each e-mail did</h2>
<div class="lg"><span><i style="background:{MENS}"></i>Men's e-mail</span><span><i style="background:{WOMENS}"></i>Women's e-mail</span></div>
{charts}
{table}
<p>Dots are the measured effect; lines are 95% confidence intervals; the dashed line is "no effect". p-values are Holm-adjusted across
these six comparisons, so the chance of even one false "win" stays at 5%. Spend is $0 for 99% of customers, so its interval was also
computed by resampling customers (bootstrap): men's {usd(men_sp["boot_lo"])} to {usd(men_sp["boot_hi"])}, women's {usd(wom_sp["boot_lo"])} to {usd(wom_sp["boot_hi"])}, almost the same.</p></section>

<section><h2>3 · Men's vs women's e-mail, head to head</h2>
<p>The men's e-mail beat the women's on every metric: spend {usd(hs["diff"], True)} per customer (95% CI {usd(hs["lo"], True)} to {usd(hs["hi"], True)}, p = {hs["p_holm"]:.3f} after Holm),
visits {pts(head.loc["visit", "diff"])}, purchases {pts(head.loc["conversion", "diff"], 2)}. One caution on spend: with ~{power["n_per_group"]:,} customers per group the test had only
{pct(power["power_for_gap_at_this_size"], 0)} power for a gap that size ({power["customers_per_group_to_detect_gap"]:,} per group would give 80%). Gaps that clear the bar
in under-powered tests tend to be overstated, so the true difference is probably smaller than {usd(hs["diff"])}.</p></section>

<section><h2>4 · Who responds? (exploratory)</h2>
<div class="lg"><span><i style="background:{MENS}"></i>Men's e-mail</span><span><i style="background:{WOMENS}"></i>Women's e-mail</span></div>
<figure>{seg_chart}</figure>
<p>The men's e-mail lifted visits in every group. The women's e-mail barely moved customers who had only ever bought men's merchandise
({pts(wseg.loc["Bought men's only", "visit_diff"])}) but worked as well as the men's e-mail on women's-only buyers ({pts(wseg.loc["Bought women's only", "visit_diff"])}).
That gap ({pts(after["gap"])}, p &lt; 0.001) was <b>spotted after looking</b> at this table, so it's a lead for the next test, not a finding.
The one segment test chosen in advance (does the men's e-mail's spend effect differ between men's-only and women's-only buyers?) found
no difference ({usd(before["gap"], True)}, p = {before["p"]:.2f}).</p></section>

<section><h2>5 · Could the tests be fooling us?</h2>
<p>Each method was run 1,000 times on two random halves of the no-e-mail group, where nothing differs. A sound test calls about 5% of those
"significant". Visits: {pct(aa["visit"])}. Spend: {pct(aa["spend"])}, so Welch's t holds up despite the long tail. Purchases: {pct(aa["conversion"])} with the z-test,
a little hot because buyers are rare (about 61 per half), and {pct(aa["conversion_fisher"])} with Fisher's exact test. Both purchase effects in section 2 also pass
Fisher's test (larger p = {vs[vs["metric"] == "conversion"]["p_fisher"].max():.4f}).</p>
<p>Smallest effect this design could reliably catch (80% power): {pts(power["mde"]["visit"])} on visits ({pct(power["mde_relative"]["visit"], 0)} of the
{pct(ctrl["visit"])} base), {pts(power["mde"]["conversion"], 2)} on purchases ({pct(power["mde_relative"]["conversion"], 0)} of {pct(ctrl["conversion"], 2)}),
{usd(power["mde"]["spend"])} on spend ({pct(power["mde_relative"]["spend"], 0)} of {usd(ctrl["spend"])}).</p></section>

<section><h2>What this test can't tell us</h2><ul>
<li>Profit: e-mail cost, margins and returns aren't in the data.</li>
<li>Anything after two weeks, including unsubscribes or e-mail fatigue from sending every week.</li>
<li>Today's customers: the data is from 2008 (released by Kevin Hillstrom for the MineThatData challenge).</li>
</ul></section>
<footer class="cap">Built by Rishit Mathur · code: github.com/mrrishit909/email-ab-test</footer>
</main></body></html>
"""
    (HERE / "report.html").write_text(html)
    print(f"report.html ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
