# E-mail A/B test readout (statistics)

A real randomized experiment, analysed the way a product or marketing analyst would report it. 64,000 customers
who bought in the last year were split at random three ways: a men's merchandise e-mail, a women's merchandise
e-mail, or no e-mail. Did the e-mails change visits, purchases and spend over the next two weeks? Which one should
be sent, and to whom?

**Readout:** [report.html](report.html) (live: https://mrrishit909.github.io/projects/email-ab-test/report.html)

## Steps

| Step | File | What it does |
|---|---|---|
| 1 | `download.py` | fetches the data (4 MB, not committed) |
| 2 | `randomization.py` | is the test fair? Sample-ratio test on group sizes; balance on 18 pre-e-mail traits |
| 3 | `effects.py` | each e-mail vs none, and head to head: difference, 95% CI, lift, Holm-adjusted p; bootstrap CI for spend; Fisher's exact test for purchases |
| 4 | `power.py` | smallest effect the design could catch; power for the head-to-head gap; 1,000-split A/A test |
| 5 | `segments.py` | exploratory: effects by past purchases, with one interaction chosen before looking and one spotted after |
| 6 | `report.py` → `report.html` | one-page readout: recommendation first, then evidence and limits |
| 7 | `check.py` | hand-written formulas vs scipy; every saved effect recomputed from the raw file; A/A rates within 3–7% |

`abstats.py` holds the formulas (two-proportion CI and z-test, Welch's t, bootstrap, Holm, Fisher, sample-ratio
test, minimum detectable effect), each a few readable lines.

## Run it

```
python3 -m venv venv && ./venv/bin/pip install pandas scipy matplotlib
./venv/bin/python download.py
./venv/bin/python randomization.py && ./venv/bin/python effects.py && ./venv/bin/python power.py
./venv/bin/python segments.py && ./venv/bin/python report.py
./venv/bin/python check.py          # prints OK or fails
```

## Results

| vs no e-mail | Spend per customer | Visited the site | Bought anything |
|---|---:|---:|---:|
| No e-mail (baseline) | $0.65 | 10.6% | 0.57% |
| Men's e-mail | **+$0.77** (95% CI +$0.49 to +$1.05) | **+7.7 pts** (+7.0 to +8.3) | **+0.68 pts** (+0.50 to +0.86) |
| Women's e-mail | +$0.42 (+$0.17 to +$0.68) | +4.5 pts (+3.9 to +5.2) | +0.31 pts (+0.15 to +0.47) |

All six effects stay significant after Holm adjustment (largest adjusted p = 0.0011).

- **Fair test:** group sizes 21,307 / 21,387 / 21,306 (sample-ratio p = 0.90); largest imbalance on 18 traits 0.016 SD.
- **Men's beats women's** on spend by $0.35 (95% CI $0.03 to $0.66, Holm p = 0.030). But the test had only 58% power
  for a gap that size, so the true gap is probably smaller. 35,761 customers per group would give 80% power.
- **The tests behave on this data:** in 1,000 A/A splits of the no-e-mail group, 4.9% of visit tests and 5.2% of
  spend tests came out "significant", as they should (5%). The purchase z-test ran a little hot (6.8%) because buyers are rare;
  Fisher's exact test gave 4.7%, and both purchase effects pass it.
- **Who responds (exploratory):** the women's e-mail barely moved customers who had only bought men's merchandise
  (+1.1 pts visits vs +7.4 pts for women's-only buyers). I spotted this after looking at the table, so it's a lead for the
  next test. The one segment test chosen in advance found no difference (p = 0.81).

**Recommendation:** send the men's e-mail (about $769 more two-week revenue per 1,000 customers e-mailed, vs $424 for
the women's), and test the women's e-mail on women's-merchandise buyers only.

## Data

Kevin Hillstrom, *MineThatData E-Mail Analytics and Data Mining Challenge* (2008):
http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv,
64,000 customers, released publicly for the challenge. The raw file isn't redistributed here; `download.py` fetches it.

## Not done

- Profit: e-mail cost, margins and returns aren't in the data, so the recommendation is about revenue.
- Effects beyond two weeks (repeat sends, unsubscribes).
- Uplift modelling (predicting each customer's individual response). The segment table is the simple version.
- The data is from 2008; today's customers may respond differently.
