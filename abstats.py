"""The statistics, written out so each formula can be read and checked (check.py compares them with scipy)."""
import numpy as np
import pandas as pd
from scipy import stats

Z95 = stats.norm.ppf(0.975)
GROUPS = {"Mens E-Mail": "Men's e-mail", "Womens E-Mail": "Women's e-mail", "No E-Mail": "No e-mail"}
CONTROL = "No E-Mail"


def load():
    from pathlib import Path
    return pd.read_csv(Path(__file__).parent / "data" / "raw" / "hillstrom.csv")


def srm(counts, shares):
    """Sample-ratio mismatch: chi-square test that group sizes match the planned split."""
    counts = np.asarray(counts, float)
    expected = counts.sum() * np.asarray(shares, float)
    chi2 = ((counts - expected) ** 2 / expected).sum()
    return chi2, stats.chi2.sf(chi2, len(counts) - 1)


def smd(t, c):
    """Standardized mean difference of a covariate between two groups (|SMD| < 0.1 = well balanced)."""
    return (t.mean() - c.mean()) / np.sqrt((t.var(ddof=1) + c.var(ddof=1)) / 2)


def proportions(x1, n1, x0, n0):
    """Difference in rates: 95% CI from the unpooled standard error, p-value from the pooled z-test."""
    p1, p0 = x1 / n1, x0 / n0
    diff = p1 - p0
    se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    pool = (x1 + x0) / (n1 + n0)
    z = diff / np.sqrt(pool * (1 - pool) * (1 / n1 + 1 / n0))
    return {"treated": p1, "control": p0, "diff": diff, "lo": diff - Z95 * se, "hi": diff + Z95 * se,
            "lift": diff / p0, "p": 2 * stats.norm.sf(abs(z))}


def means(a, b):
    """Difference in means with Welch's t (no equal-variance assumption)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    diff, se = a.mean() - b.mean(), np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    q = stats.t.ppf(0.975, df)
    return {"treated": a.mean(), "control": b.mean(), "diff": diff, "lo": diff - q * se, "hi": diff + q * se,
            "lift": diff / b.mean(), "p": 2 * stats.t.sf(abs(diff / se), df)}


def bootstrap(a, b, reps=5000, seed=0):
    """Percentile 95% CI for a difference in means by resampling customers. No normality assumed:
    spend is 99% zeros with a long tail, so this is the cross-check on Welch."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    diffs = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(reps)])
    return np.percentile(diffs, [2.5, 97.5])


def holm(pvals):
    """Holm's step-down adjustment: keeps the chance of any false 'win' across all tests at 5%."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj


def mde_rate(p0, n, power=0.8):
    """Smallest true difference in a rate the test would catch with the given power (two arms of n)."""
    return (Z95 + stats.norm.ppf(power)) * np.sqrt(2 * p0 * (1 - p0) / n)


def mde_mean(sd, n, power=0.8):
    return (Z95 + stats.norm.ppf(power)) * sd * np.sqrt(2 / n)
