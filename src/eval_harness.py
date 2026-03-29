"""
Chaos 2 Clarity — Evaluation Harness
Core evaluation infrastructure: QueryResult, metric computation, error classification.
Directly implements the evaluation functions from the experiments specification.
"""

import json
import time
import re
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class QueryResult:
    """Stores the full result of evaluating one question against one system."""
    question_id: str
    system: str
    nl_prompt: str
    tier: str
    generated_sql: str
    execution_success: bool       # EA: did SQL execute without error?
    result_correct: bool          # RC: does result match gold?
    sql_exact_match: bool         # EM: does SQL match gold SQL?
    error_class: Optional[str]    # E1-E5 or None if success
    latency_ms: float             # end-to-end wall time
    retry_count: int              # how many retries were needed
    grounding_used: bool          # did 𝒱 return a match?
    grounding_similarity: float   # highest cosine sim in 𝒱
    first_pass_success: bool      # did it succeed on attempt 0?
    raw_result: Any = None        # actual query result
    error_message: str = ""       # error message if failed
    cross_source_planned: bool = False

    def to_dict(self):
        d = asdict(self)
        # Remove raw_result for serialization (can be large)
        d.pop('raw_result', None)
        return d


def normalize_sql(sql: str) -> str:
    """Normalize SQL for exact match comparison."""
    if not sql:
        return ""
    sql = sql.strip()
    # Remove markdown code blocks if present
    sql = re.sub(r'^```(?:sql)?\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    # Lowercase
    sql = sql.lower()
    # Collapse whitespace
    sql = re.sub(r'\s+', ' ', sql)
    # Remove trailing semicolons
    sql = sql.rstrip(';').strip()
    # Remove comments
    sql = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    return sql.strip()


def is_execution_success(sql: str, result) -> bool:
    """Returns True if SQL ran without a database exception."""
    if result is None:
        return False
    if isinstance(result, Exception):
        return False
    if isinstance(result, dict) and result.get('error'):
        return False
    return True


def is_result_correct(result, gold_result: dict, tolerance: float = 0.01) -> bool:
    """
    Compare query result against gold result.
    - Numeric aggregates: within tolerance (1%)
    - Categorical/set results: exact set match (order-insensitive)
    - Row count comparison for list queries
    """
    if result is None or gold_result is None:
        return False

    try:
        # Handle different result formats
        result_rows = _normalize_result(result)
        gold_rows = _normalize_result(gold_result)

        if not result_rows and not gold_rows:
            return True
        if not result_rows or not gold_rows:
            return False

        # Single numeric value comparison
        if len(gold_rows) == 1 and _is_numeric(gold_rows[0]):
            if len(result_rows) >= 1 and _is_numeric(result_rows[0]):
                g = float(gold_rows[0])
                r = float(result_rows[0])
                if g == 0:
                    return abs(r) < tolerance
                return abs(r - g) / max(abs(g), 1e-9) < tolerance

        # Multi-row: compare as sets of tuples (order-insensitive)
        result_set = set(str(r) for r in result_rows)
        gold_set = set(str(g) for g in gold_rows)

        # If exact match
        if result_set == gold_set:
            return True

        # If the gold has specific rows, check subset relationship
        # (sometimes valid SQL produces correct rows in different format)
        if gold_set.issubset(result_set) and len(result_set) <= len(gold_set) * 1.5:
            return True

        return False

    except Exception:
        return False


def _normalize_result(result) -> list:
    """Convert various result formats to a flat list of values."""
    if isinstance(result, dict):
        if 'rows' in result:
            rows = result['rows']
            if isinstance(rows, list):
                flat = []
                for row in rows:
                    if isinstance(row, dict):
                        flat.extend(row.values())
                    elif isinstance(row, (list, tuple)):
                        flat.extend(row)
                    else:
                        flat.append(row)
                return flat
        return list(result.values())
    elif isinstance(result, list):
        flat = []
        for item in result:
            if isinstance(item, (list, tuple)):
                flat.extend(item)
            elif isinstance(item, dict):
                flat.extend(item.values())
            else:
                flat.append(item)
        return flat
    elif isinstance(result, (int, float, str)):
        return [result]
    return []


def _is_numeric(val) -> bool:
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def is_sql_exact_match(generated: str, gold: str) -> bool:
    """Normalized SQL comparison (secondary metric)."""
    return normalize_sql(generated) == normalize_sql(gold)


def classify_error(sql: str, result, question: dict, meta: dict = None) -> Optional[str]:
    """
    Classify failure into E1-E5 based on error signal.
    Priority: E5 > E3 > E1 > E4 > E2
    """
    meta = meta or {}

    if result is None or isinstance(result, Exception) or (isinstance(result, dict) and result.get('error')):
        error_msg = str(result).lower() if result else ""

        # E5: Cross-source failure
        if question.get('tier') in ['L3'] and not meta.get('cross_source_planned', False):
            return "E5"

        # E1: Column/table not found
        if any(kw in error_msg for kw in ['column', 'does not exist', 'unknown column',
                                            'not found', 'no such column', 'no such table',
                                            'catalog error', 'binder error']):
            return "E1"

        # E3: Join error
        if 'join' in (sql or '').lower() and any(kw in error_msg for kw in [
            'no such key', 'constraint', 'ambiguous', 'cannot join',
            'mismatch', 'foreign key']):
            return "E3"

        # E4: Default for other execution errors
        return "E4"

    # EA=True, RC=False → E2 (aggregation/semantic error)
    gold_result = question.get('gold_result')
    if gold_result and not is_result_correct(result, gold_result):
        return "E2"

    return None  # Success


def evaluate_system(
    system_name: str,
    questions: List[dict],
    system_fn,
    record_first_pass: bool = False
) -> List[QueryResult]:
    """
    Run a batch of questions through a system and collect results.

    Args:
        system_name: Identifier for the system being evaluated
        questions: List of question dicts with id, nl_prompt, gold_sql, gold_result, tier
        system_fn: callable(nl_prompt) -> (sql, result, metadata)
        record_first_pass: If True, track first-pass success separately
    """
    results = []
    for q in questions:
        start = time.perf_counter()
        try:
            sql, result, meta = system_fn(q['nl_prompt'])
        except Exception as e:
            sql = ""
            result = e
            meta = {}
        latency = (time.perf_counter() - start) * 1000

        ea = is_execution_success(sql, result)
        rc = is_result_correct(result, q.get('gold_result')) if ea else False
        em = is_sql_exact_match(sql, q.get('gold_sql', ''))
        error_class = classify_error(sql, result, q, meta) if not rc else None

        results.append(QueryResult(
            question_id=q['id'],
            system=system_name,
            nl_prompt=q['nl_prompt'],
            tier=q.get('tier', ''),
            generated_sql=sql or "",
            execution_success=ea,
            result_correct=rc,
            sql_exact_match=em,
            error_class=error_class,
            latency_ms=latency,
            retry_count=meta.get('retry_count', 0),
            grounding_used=meta.get('grounding_used', False),
            grounding_similarity=meta.get('grounding_sim', 0.0),
            first_pass_success=meta.get('first_pass', ea and rc),
            raw_result=result if ea else None,
            error_message=str(result) if not ea else "",
            cross_source_planned=meta.get('cross_source_planned', False),
        ))
    return results


def compute_metrics(results: List[QueryResult]) -> dict:
    """Compute aggregate metrics from a batch of results."""
    n = len(results)
    if n == 0:
        return {}

    latencies = sorted(r.latency_ms for r in results)

    metrics = {
        'n': n,
        'EA': sum(r.execution_success for r in results) / n,
        'RC': sum(r.result_correct for r in results) / n,
        'EM': sum(r.sql_exact_match for r in results) / n,
        'P50_ms': latencies[n // 2],
        'P95_ms': latencies[int(n * 0.95)] if n >= 20 else latencies[-1],
        'error_distribution': {
            'E1': sum(r.error_class == 'E1' for r in results) / n,
            'E2': sum(r.error_class == 'E2' for r in results) / n,
            'E3': sum(r.error_class == 'E3' for r in results) / n,
            'E4': sum(r.error_class == 'E4' for r in results) / n,
            'E5': sum(r.error_class == 'E5' for r in results) / n,
            'None': sum(r.error_class is None for r in results) / n,
        },
        'avg_retry_count': sum(r.retry_count for r in results) / n,
        'grounding_hit_rate': sum(r.grounding_used for r in results) / n,
        'first_pass_EA': sum(r.first_pass_success for r in results) / n,
    }

    # Per-tier breakdown
    tiers = set(r.tier for r in results if r.tier)
    for tier in sorted(tiers):
        tier_results = [r for r in results if r.tier == tier]
        tn = len(tier_results)
        if tn > 0:
            metrics[f'{tier}_EA'] = sum(r.execution_success for r in tier_results) / tn
            metrics[f'{tier}_RC'] = sum(r.result_correct for r in tier_results) / tn

    return metrics


def compute_metrics_by_tier(results: List[QueryResult]) -> dict:
    """Compute EA/RC per tier for degradation analysis (Experiment 4)."""
    tiers = {}
    for r in results:
        if r.tier not in tiers:
            tiers[r.tier] = []
        tiers[r.tier].append(r)

    metrics = {}
    for tier, tier_results in tiers.items():
        n = len(tier_results)
        metrics[f'{tier}_EA'] = sum(r.execution_success for r in tier_results) / n
        metrics[f'{tier}_RC'] = sum(r.result_correct for r in tier_results) / n
    return metrics


def compute_degradation(metrics_by_tier: dict) -> dict:
    """Compute structured → heterogeneous degradation (Experiment 4)."""
    l1_ea = metrics_by_tier.get('L1_EA', 0)
    l2_ea = metrics_by_tier.get('L2_EA', 0)
    l3_ea = metrics_by_tier.get('L3_EA', 0)
    l4_ea = metrics_by_tier.get('L4_EA', 0)

    structured_ea = (l1_ea + l2_ea) / 2
    hetero_ea = (l3_ea + l4_ea) / 2
    degradation = structured_ea - hetero_ea

    return {
        'structured_EA': round(structured_ea, 4),
        'heterogeneous_EA': round(hetero_ea, 4),
        'absolute_degradation_pp': round(degradation * 100, 2),
        'relative_degradation_pct': round(degradation / max(structured_ea, 1e-9) * 100, 2),
    }


def save_results(results: List[QueryResult], filepath: str):
    """Save results to JSON file."""
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    data = [r.to_dict() for r in results]
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_results(filepath: str) -> List[dict]:
    """Load results from JSON file."""
    with open(filepath) as f:
        return json.load(f)


def load_questions(questions_dir: str) -> List[dict]:
    """Load all question JSON files from directory."""
    questions = []
    for fname in sorted(Path(questions_dir).glob('*.json')):
        with open(fname) as f:
            questions.append(json.load(f))
    return questions


def format_results_table(all_metrics: dict, systems: list, metric_keys: list = None) -> str:
    """Format results as a markdown table for the paper."""
    if metric_keys is None:
        metric_keys = ['L1_EA', 'L2_EA', 'L3_EA', 'L4_EA', 'EA', 'RC']

    header = '| System | ' + ' | '.join(metric_keys) + ' |'
    separator = '|---|' + '|'.join(['---'] * len(metric_keys)) + '|'
    rows = [header, separator]

    for sys_name in systems:
        m = all_metrics.get(sys_name, {})
        vals = []
        for key in metric_keys:
            v = m.get(key, '—')
            if isinstance(v, float):
                vals.append(f'{v*100:.1f}%')
            else:
                vals.append(str(v))
        rows.append(f'| {sys_name} | ' + ' | '.join(vals) + ' |')

    return '\n'.join(rows)
