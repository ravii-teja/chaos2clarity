"""
Chaos 2 Clarity — Statistical Significance Tests
McNemar's test for EA/RC paired comparisons.
Mann-Whitney U for latency distributions.
"""

import numpy as np
from typing import List, Dict


def mcnemar_test(results_a: list, results_b: list, metric: str = 'result_correct') -> dict:
    """
    McNemar's test for EA/RC differences between two systems on paired questions.
    Null hypothesis: both systems have the same error rate.

    Args:
        results_a, results_b: Lists of QueryResult objects (or dicts with metric key)
        metric: 'execution_success' for EA, 'result_correct' for RC
    """
    from scipy.stats import binomtest

    assert len(results_a) == len(results_b), "Paired test requires equal question sets"

    # Build 2x2 contingency table
    # [a_correct & b_correct, a_correct & b_wrong]
    # [a_wrong & b_correct,   a_wrong & b_wrong  ]
    n00 = n01 = n10 = n11 = 0

    for a, b in zip(results_a, results_b):
        a_val = getattr(a, metric, None) if hasattr(a, metric) else a.get(metric)
        b_val = getattr(b, metric, None) if hasattr(b, metric) else b.get(metric)

        if a_val and b_val:
            n11 += 1
        elif a_val and not b_val:
            n10 += 1
        elif not a_val and b_val:
            n01 += 1
        else:
            n00 += 1

    # McNemar's test focuses on discordant pairs (n01 + n10)
    n_discordant = n01 + n10
    if n_discordant == 0:
        return {
            'statistic': 0.0,
            'p_value': 1.0,
            'significant': False,
            'table': [[n11, n10], [n01, n00]],
            'n_discordant': 0,
            'note': 'No discordant pairs — systems agree perfectly'
        }

    # Exact McNemar (binomial test) — appropriate for small samples
    p_value = binomtest(n01, n_discordant, 0.5).pvalue

    # Chi-squared approximation for larger samples
    if n_discordant >= 25:
        chi2 = (abs(n01 - n10) - 1) ** 2 / n_discordant  # with continuity correction
        from scipy.stats import chi2 as chi2_dist
        p_value_chi2 = 1 - chi2_dist.cdf(chi2, df=1)
    else:
        chi2 = None
        p_value_chi2 = None

    return {
        'statistic': chi2 if chi2 is not None else float(n01),
        'p_value': p_value,
        'p_value_chi2': p_value_chi2,
        'significant': p_value < 0.05,
        'table': [[n11, n10], [n01, n00]],
        'n_discordant': n_discordant,
        'a_better': n10,  # times A succeeded but B failed
        'b_better': n01,  # times B succeeded but A failed
    }


def mann_whitney_latency(results_a: list, results_b: list) -> dict:
    """Mann-Whitney U test for latency distributions."""
    from scipy.stats import mannwhitneyu

    latencies_a = [getattr(r, 'latency_ms', r.get('latency_ms', 0)) if isinstance(r, dict)
                    else r.latency_ms for r in results_a]
    latencies_b = [getattr(r, 'latency_ms', r.get('latency_ms', 0)) if isinstance(r, dict)
                    else r.latency_ms for r in results_b]

    stat, p = mannwhitneyu(latencies_a, latencies_b, alternative='two-sided')

    return {
        'statistic': stat,
        'p_value': p,
        'significant': p < 0.05,
        'median_a': np.median(latencies_a),
        'median_b': np.median(latencies_b),
        'mean_a': np.mean(latencies_a),
        'mean_b': np.mean(latencies_b),
    }


def mann_whitney_trend(ea_over_time: list) -> dict:
    """
    Test whether EA shows a significant trend over time (Experiment 5).
    Compare first half vs second half of the time series.
    """
    from scipy.stats import mannwhitneyu

    mid = len(ea_over_time) // 2
    first_half = ea_over_time[:mid]
    second_half = ea_over_time[mid:]

    if len(first_half) < 2 or len(second_half) < 2:
        return {'significant': False, 'note': 'Too few data points'}

    stat, p = mannwhitneyu(second_half, first_half, alternative='greater')

    return {
        'statistic': stat,
        'p_value': p,
        'significant': p < 0.05,
        'trend_direction': 'positive' if np.mean(second_half) > np.mean(first_half) else 'negative',
        'first_half_mean': np.mean(first_half),
        'second_half_mean': np.mean(second_half),
    }


def run_all_significance_tests(
    all_results: Dict[str, list],
    reference_system: str = 'C2C-Full'
) -> Dict[str, dict]:
    """Run McNemar's test comparing every system against the reference."""
    tests = {}
    ref_results = all_results.get(reference_system)
    if not ref_results:
        return tests

    for sys_name, sys_results in all_results.items():
        if sys_name == reference_system:
            continue
        if len(sys_results) != len(ref_results):
            continue

        tests[f'{reference_system}_vs_{sys_name}_EA'] = mcnemar_test(
            ref_results, sys_results, metric='execution_success'
        )
        tests[f'{reference_system}_vs_{sys_name}_RC'] = mcnemar_test(
            ref_results, sys_results, metric='result_correct'
        )
        tests[f'{reference_system}_vs_{sys_name}_latency'] = mann_whitney_latency(
            ref_results, sys_results
        )

    return tests
