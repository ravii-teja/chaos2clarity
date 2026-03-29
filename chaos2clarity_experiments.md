# Chaos 2 Clarity — Experiments Design Specification
### Engineering-Grade Evaluation Harness for Publication

> **Purpose:** This document is the complete, self-contained specification for running all eight experiments needed to publish the C2C paper. Each experiment has: exact setup, dataset, evaluation script structure, expected output format, and acceptance criteria. Follow in order.

---

## QUICK REFERENCE

| Exp | Name | Claim It Proves | Est. Time | Priority |
|---|---|---|---|---|
| E1 | Baseline vs. C2C | Central hypothesis (≥ 25pp gain) | 3–4 hrs | 🔴 MUST |
| E2 | Semantic Layer Impact | Mechanism I matters | 2–3 hrs | 🔴 MUST |
| E3 | Agent Ablation | Mechanism II — each stage matters | 4–5 hrs | 🔴 MUST |
| E4 | Heterogeneous Data Handling | C2C degrades less on complex data | 1 hr (reuse E1 data) | 🔴 MUST |
| E5 | Feedback Learning Loop | Mechanism IV — system improves | 5–6 hrs (200 queries) | 🔴 MUST |
| E6 | Vector Grounding Impact | Mechanism III — 𝒱 reduces E1 | 5–6 hrs (reuse E5 run) | 🔴 MUST |
| E7 | Error Taxonomy Distribution | Validates E1–E5 taxonomy | 1 hr (reuse E1/E3 logs) | 🟡 STRONG |
| E8 | Latency–Accuracy Tradeoff | Deployment cost-benefit | 1 hr (reuse timing logs) | 🟡 STRONG |

**Total estimated run time:** 12–16 hours of active execution across all 8 experiments.  
**Prerequisite:** Prototype deployed, all three data sources connected, gold question suite finalized.

---

## PART 1: DATASET CONSTRUCTION

### 1.1 The 50-Question BI Suite

This is the most important artifact in the entire evaluation. Everything else depends on it. Build it carefully before running any experiments.

**Distribution:**
```
L1 — Single-source metric (15 questions)     → tests E1, E2
L2 — Multi-table join, single source (15)   → tests E1, E2, E3
L3 — Cross-source multi-hop (10)            → tests E3, E4, E5
L4 — Unstructured + structured RAG (10)     → tests E4
```

### 1.2 Full Question List with Gold Annotations

Each question needs four fields: **NL prompt**, **Gold SQL**, **Gold result set**, **Error class annotation (primary)**. The gold result set is what your actual database returns when you run the gold SQL.

#### L1 — Single-Source Metric (15 questions)

| ID | NL Prompt | Gold SQL | Error Class |
|---|---|---|---|
| L1-01 | What was total gross revenue last quarter? | `SELECT SUM(line_value) FROM orders WHERE order_date >= '2024-10-01' AND order_date < '2025-01-01'` | E1 (column name trap) |
| L1-02 | How many orders were placed in Q1 2024? | `SELECT COUNT(*) FROM orders WHERE order_date >= '2024-01-01' AND order_date < '2024-04-01'` | E1 |
| L1-03 | What is our average order value this year? | `SELECT AVG(line_value) FROM orders WHERE EXTRACT(YEAR FROM order_date) = 2024` | E2 (could confuse SUM/AVG) |
| L1-04 | How many unique customers made a purchase last month? | `SELECT COUNT(DISTINCT customer_id) FROM orders WHERE order_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')` | E1 |
| L1-05 | What is the total number of products in our catalog? | `SELECT COUNT(*) FROM products` | — |
| L1-06 | What was our highest single-order revenue ever? | `SELECT MAX(line_value) FROM orders` | E1 |
| L1-07 | How many orders were cancelled last quarter? | `SELECT COUNT(*) FROM orders WHERE status = 'cancelled' AND order_date >= '2024-10-01'` | E1 |
| L1-08 | What is our total revenue for product category 'Electronics'? | `SELECT SUM(line_value) FROM orders o JOIN products p ON o.product_id = p.id WHERE p.category = 'Electronics'` | E1, E3 |
| L1-09 | How many orders shipped in the last 30 days? | `SELECT COUNT(*) FROM orders WHERE ship_date >= CURRENT_DATE - 30` | E1 |
| L1-10 | What is the revenue for the top-selling product? | `SELECT p.name, SUM(o.line_value) as rev FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.name ORDER BY rev DESC LIMIT 1` | E1, E2 |
| L1-11 | How many new customers signed up this month? | `SELECT COUNT(*) FROM customers WHERE created_at >= date_trunc('month', CURRENT_DATE)` | E1 |
| L1-12 | What is our total cost of goods sold last year? | `SELECT SUM(cost_price * quantity) FROM orders WHERE EXTRACT(YEAR FROM order_date) = 2023` | E1 (column names) |
| L1-13 | What percentage of orders last month were returned? | `SELECT ROUND(100.0 * COUNT(CASE WHEN status='returned' THEN 1 END) / COUNT(*), 2) FROM orders WHERE order_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')` | E2 (percentage logic) |
| L1-14 | How many distinct product categories do we sell? | `SELECT COUNT(DISTINCT category) FROM products` | — |
| L1-15 | What was our revenue on our single best day last year? | `SELECT order_date, SUM(line_value) FROM orders WHERE EXTRACT(YEAR FROM order_date)=2023 GROUP BY order_date ORDER BY SUM(line_value) DESC LIMIT 1` | E1 |

#### L2 — Multi-Table Join, Single Source (15 questions)

| ID | NL Prompt | Gold SQL (abbreviated) | Error Class |
|---|---|---|---|
| L2-01 | Revenue by product category for Q4 2024? | `SELECT p.category, SUM(o.line_value) FROM orders o JOIN products p ... WHERE q4 GROUP BY p.category` | E1, E3 |
| L2-02 | Which customers placed > 5 orders last 90 days? | `SELECT c.name, COUNT(o.id) FROM customers c JOIN orders o ... WHERE last_90 GROUP BY c.name HAVING COUNT > 5` | E3 |
| L2-03 | Top 10 customers by lifetime revenue? | `SELECT c.name, SUM(o.line_value) FROM customers c JOIN orders o ... GROUP BY c.name ORDER BY SUM DESC LIMIT 10` | E1, E3 |
| L2-04 | Average days between order and shipment per product category? | `SELECT p.category, AVG(ship_date - order_date) FROM orders o JOIN products p ...` | E2, E3 |
| L2-05 | Which product categories have > 10% return rate? | `SELECT p.category, ROUND(100.0 * returns / total, 2) FROM ... HAVING return_rate > 10` | E2, E3 |
| L2-06 | Revenue per customer segment last quarter? | `SELECT c.segment, SUM(o.line_value) FROM customers c JOIN orders o ...` | E3 (segment column name) |
| L2-07 | Which salesperson closed the most orders last month? | `SELECT rep_name, COUNT(*) FROM orders o JOIN sales_reps r ... GROUP BY rep_name ORDER BY COUNT DESC LIMIT 1` | E3 |
| L2-08 | Month-over-month revenue growth for last 6 months? | `SELECT month, SUM(line_value), LAG(SUM...) FROM orders GROUP BY month ORDER BY month` | E2 (window function) |
| L2-09 | Products with 0 orders in last 60 days? | `SELECT p.name FROM products p LEFT JOIN orders o ... WHERE o.id IS NULL` | E3 (LEFT JOIN semantics) |
| L2-10 | Average order value per customer segment? | `SELECT c.segment, AVG(o.line_value) FROM customers c JOIN orders o ...` | E2, E3 |
| L2-11 | Revenue from repeat vs first-time customers this year? | `SELECT is_first_time, SUM(line_value) FROM ... (subquery needed)` | E2, E3 (complex join) |
| L2-12 | Which product has highest revenue variance month-to-month? | `SELECT p.name, STDDEV(monthly_rev) FROM (... subquery ...) GROUP BY p.name ORDER BY STDDEV DESC` | E2 (STDDEV vs. VARIANCE) |
| L2-13 | Customers who increased spending by > 20% vs last year? | `SELECT ... year-over-year comparison` | E2, E3 |
| L2-14 | Average basket size (items per order) by category? | `SELECT p.category, AVG(quantity) FROM orders o JOIN order_items oi JOIN products p ...` | E3, E1 (order_items vs orders) |
| L2-15 | What percentage of revenue comes from our top 20% of customers? | `SELECT SUM(rev) FROM (top 20% subquery) / total` | E2 (Pareto logic) |

#### L3 — Cross-Source Multi-Hop (10 questions)

These require data from PostgreSQL AND Salesforce AND/OR logistics CSV.

| ID | NL Prompt | Sources Required | Gold SQL / Plan | Error Class |
|---|---|---|---|---|
| L3-01 | Which customers with active CRM deals had delivery issues in last 30 days? | PostgreSQL + Salesforce + Logistics | JOIN on customer entity across sources | E3, E5 |
| L3-02 | Average deal size (Salesforce) for customers whose last delivery was delayed > 3 days? | Salesforce + Logistics | Join on customer_id (implicit) | E3, E5 |
| L3-03 | Which of our top 10 revenue customers (PostgreSQL) have an open CRM opportunity? | PostgreSQL + Salesforce | Join on customer entity | E3, E5 |
| L3-04 | Delivery success rate for customers in the 'Enterprise' Salesforce segment? | Salesforce + Logistics | Join segment → customer → delivery | E4, E5 |
| L3-05 | Total revenue (PostgreSQL) from customers whose CRM deals closed last quarter? | PostgreSQL + Salesforce | Join on close_date + customer | E3, E5 |
| L3-06 | Which customers have both high order value AND a delayed shipment this month? | PostgreSQL + Logistics | Join on customer_id | E3, E5 |
| L3-07 | Correlation between CRM deal stage and on-time delivery rate? | Salesforce + Logistics | Analytical cross-source query | E4, E5 |
| L3-08 | Which product categories have the most delivery complaints from high-value CRM accounts? | PostgreSQL + Salesforce + Logistics | Three-source join | E3, E4, E5 |
| L3-09 | Average time from CRM deal close to first order (PostgreSQL)? | PostgreSQL + Salesforce | Join on customer + date | E3, E5 |
| L3-10 | Which logistics carrier has the worst on-time rate for our top 20% revenue customers? | PostgreSQL + Logistics | Join on customer + carrier | E3, E5 |

#### L4 — Unstructured + Structured RAG (10 questions)

| ID | NL Prompt | Data Required | Expected Output |
|---|---|---|---|
| L4-01 | Summarize delivery complaint emails for our top 10 revenue customers in Q1. | PostgreSQL (revenue) + document store (emails) | Summary text per customer |
| L4-02 | Which product categories have the most negative sentiment in support tickets this month? | PostgreSQL (categories) + document store (tickets) | Category → sentiment score table |
| L4-03 | What common complaints appear in Salesforce notes for delayed shipment accounts? | Salesforce (notes) + Logistics (delay flag) | Clustered complaint themes |
| L4-04 | Find all customers who mentioned competitor products in support interactions this year. | Document store (support chat) + PostgreSQL (customers) | Customer list + mention count |
| L4-05 | What were the top 3 reasons for returns based on return reason notes? | PostgreSQL (returns) + document store (return notes) | Ranked reason list |
| L4-06 | Which sales reps have the most positive customer email sentiment in closed deals? | Salesforce (deal notes/emails) + structured deal data | Rep → sentiment ranking |
| L4-07 | Summarize key themes in customer onboarding feedback for Enterprise accounts. | Salesforce (segment) + document store (onboarding surveys) | Theme summary |
| L4-08 | Which logistics partners have the most complaints about damaged goods? | Logistics (carrier) + document store (damage reports) | Carrier → complaint count |
| L4-09 | What do our churned customers say were their top reasons for leaving? | PostgreSQL (churn flag) + document store (exit surveys) | Ranked reason list |
| L4-10 | Find orders where the customer complaint explicitly mentions a product defect and cross-reference with QA reports. | PostgreSQL (orders) + document store (complaints + QA) | Matched order/complaint pairs |

---

### 1.3 Gold Annotation Protocol

**Step 1 — Author writes gold SQL.** For each question: write the SQL against your actual database, run it, verify the result makes business sense. Save the result set as a JSON file.

**Step 2 — Independent annotator review.** One domain expert (data engineer or BI analyst not involved in C2C design) reviews each gold SQL for correctness. Disagreements go to a third reviewer as tiebreaker.

**Step 3 — Error class annotation.** For each question, annotate the *primary* error class that a naive LLM would likely produce (E1–E5). This is used to validate the error taxonomy in Experiment 7.

**Step 4 — Store in structured format:**
```json
{
  "id": "L1-01",
  "tier": "L1",
  "nl_prompt": "What was total gross revenue last quarter?",
  "gold_sql": "SELECT SUM(line_value) FROM orders WHERE ...",
  "gold_result": {"rows": [{"sum": 1247893.45}], "columns": ["sum"]},
  "primary_error_class": "E1",
  "error_note": "LLM likely generates order_total instead of line_value",
  "annotated_by": ["author", "domain_expert_1"],
  "disagreement_resolved_by": null
}
```

**File structure:**
```
eval/
  questions/
    L1-01.json ... L1-15.json
    L2-01.json ... L2-15.json
    L3-01.json ... L3-10.json
    L4-01.json ... L4-10.json
  gold_semantic_model.json   ← manually built reference 𝒮
  schema_snapshot.sql        ← frozen schema at evaluation time
```

---

### 1.4 Gold Semantic Model Construction

Build this once, manually, before running any experiments. This is your ground truth for Experiment 2's semantic synthesis quality sub-results.

```json
{
  "entities": [
    {"name": "Customer", "aliases": ["client", "account", "buyer"],
     "source_tables": ["pg.customers", "sf.accounts"],
     "join_key": {"pg": "customer_id", "sf": "account_id"}},
    {"name": "Order", "aliases": ["purchase", "transaction"],
     "source_tables": ["pg.orders"]},
    {"name": "Product", "aliases": ["item", "SKU"],
     "source_tables": ["pg.products"]},
    {"name": "Delivery", "aliases": ["shipment", "logistics event"],
     "source_tables": ["logistics.deliveries_csv"]},
    {"name": "Deal", "aliases": ["opportunity", "CRM deal"],
     "source_tables": ["sf.opportunities"]},
    // ... all entities
  ],
  "metrics": [
    {"name": "Revenue", "aliases": ["gross revenue", "sales", "total revenue"],
     "formula": "SUM(orders.line_value)", "unit": "USD"},
    {"name": "OrderCount", "formula": "COUNT(orders.id)", "unit": "count"},
    {"name": "DeliveryDelayDays", "formula": "delivery_date - expected_date", "unit": "days"},
    // ... all metrics
  ],
  "cross_source_relationships": [
    {"from": "Customer", "to": "Deal", "type": "HasOpportunity",
     "join_hint": "pg.customers.email = sf.accounts.email"},
    {"from": "Customer", "to": "Delivery", "type": "HasDelivery",
     "join_hint": "pg.orders.shipping_id = logistics.deliveries_csv.tracking_id"},
    // ...
  ]
}
```

Count your gold entities, metrics, and cross-source relationships. These become the denominators in Experiment 2's coverage table.

---

## PART 2: EVALUATION HARNESS

### 2.1 Core Evaluation Script Structure

```python
# eval/run_experiment.py

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class QueryResult:
    question_id: str
    system: str           # e.g., "C2C-Full", "B1-Direct", "ABL-NoRetry"
    nl_prompt: str
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


def evaluate_system(system_name: str, questions: list, system_fn: callable) -> list[QueryResult]:
    """
    system_fn: callable(nl_prompt) -> (generated_sql, result_set, metadata)
    """
    results = []
    for q in questions:
        start = time.perf_counter()
        sql, result, meta = system_fn(q["nl_prompt"])
        latency = (time.perf_counter() - start) * 1000
        
        ea = is_execution_success(sql, result)
        rc = is_result_correct(result, q["gold_result"]) if ea else False
        em = is_sql_exact_match(sql, q["gold_sql"])
        error_class = classify_error(sql, result, q, meta) if not rc else None
        
        results.append(QueryResult(
            question_id=q["id"], system=system_name,
            nl_prompt=q["nl_prompt"], generated_sql=sql,
            execution_success=ea, result_correct=rc, sql_exact_match=em,
            error_class=error_class, latency_ms=latency,
            retry_count=meta.get("retry_count", 0),
            grounding_used=meta.get("grounding_used", False),
            grounding_similarity=meta.get("grounding_sim", 0.0),
            first_pass_success=meta.get("first_pass", False)
        ))
    return results


def compute_metrics(results: list[QueryResult]) -> dict:
    n = len(results)
    return {
        "EA": sum(r.execution_success for r in results) / n,
        "RC": sum(r.result_correct for r in results) / n,
        "EM": sum(r.sql_exact_match for r in results) / n,
        "P50_ms": sorted(r.latency_ms for r in results)[n // 2],
        "P95_ms": sorted(r.latency_ms for r in results)[int(n * 0.95)],
        "error_distribution": {
            "E1": sum(r.error_class == "E1" for r in results) / n,
            "E2": sum(r.error_class == "E2" for r in results) / n,
            "E3": sum(r.error_class == "E3" for r in results) / n,
            "E4": sum(r.error_class == "E4" for r in results) / n,
            "E5": sum(r.error_class == "E5" for r in results) / n,
            "None": sum(r.error_class is None for r in results) / n,
        },
        "avg_retry_count": sum(r.retry_count for r in results) / n,
        "grounding_hit_rate": sum(r.grounding_used for r in results) / n,
        "first_pass_EA": sum(r.first_pass_success for r in results) / n,
    }
```

### 2.2 Metric Definitions

```python
def is_execution_success(sql: str, result) -> bool:
    """Returns True if SQL ran without a database exception."""
    return result is not None and not isinstance(result, Exception)


def is_result_correct(result, gold_result: dict, tolerance: float = 0.001) -> bool:
    """
    Exact set match for categorical results.
    Tolerance-based comparison for numeric aggregates.
    For L4 (RAG), use separate semantic similarity scoring.
    """
    if result is None or gold_result is None:
        return False
    
    result_rows = normalize_result(result)
    gold_rows = normalize_result(gold_result)
    
    # Numeric: within tolerance
    if is_numeric_result(gold_rows):
        return all(
            abs(r - g) / max(abs(g), 1e-9) < tolerance
            for r, g in zip(result_rows, gold_rows)
        )
    
    # Categorical: exact set match (order-insensitive)
    return set(result_rows) == set(gold_rows)


def is_sql_exact_match(generated: str, gold: str) -> bool:
    """
    Normalize both SQLs before comparison:
    - lowercase
    - collapse whitespace
    - remove comments
    - sort SELECT columns alphabetically
    - sort WHERE conditions
    Note: EM is a SECONDARY metric. RC is primary.
    """
    return normalize_sql(generated) == normalize_sql(gold)


def classify_error(sql: str, result, question: dict, meta: dict) -> Optional[str]:
    """
    Classify failure into E1-E5 based on error signal.
    Priority: E5 > E3 > E1 > E4 > E2
    (E5 is most structurally specific; E2 requires RC failure with EA success)
    """
    if result is None or isinstance(result, Exception):
        error_msg = str(result).lower()
        
        # E1: column/table not found
        if "column" in error_msg or "does not exist" in error_msg or "unknown column" in error_msg:
            return "E1"
        
        # E3: join error / foreign key issue
        if "join" in sql.lower() and ("no such key" in error_msg or "constraint" in error_msg):
            return "E3"
        
        # E5: cross-source failure — single-source plan for multi-source question
        if question["tier"] == "L3" and not meta.get("cross_source_planned", False):
            return "E5"
        
        return "E4"  # default: semantic misunderstanding
    
    # EA=True, RC=False → E2 (aggregation error — syntactically valid, semantically wrong)
    if is_execution_success(sql, result) and not is_result_correct(result, question["gold_result"]):
        return "E2"
    
    return None  # success
```

### 2.3 Statistical Significance Tests

```python
from scipy.stats import mannwhitneyu, wilcoxon
from statsmodels.stats.contingency_tables import mcnemar
import numpy as np

def mcnemar_test(results_a: list[QueryResult], results_b: list[QueryResult]) -> dict:
    """
    McNemar's test for EA/RC differences between two systems on paired questions.
    Null hypothesis: both systems have the same error rate.
    """
    assert len(results_a) == len(results_b), "Paired test requires equal question sets"
    
    # Contingency table: (a_correct, b_correct)
    table = np.zeros((2, 2))
    for a, b in zip(results_a, results_b):
        table[int(a.result_correct)][int(b.result_correct)] += 1
    
    result = mcnemar(table, exact=True)
    return {
        "statistic": result.statistic,
        "p_value": result.pvalue,
        "significant": result.pvalue < 0.05,
        "table": table.tolist()
    }


def mann_whitney_latency(results_a: list[QueryResult], results_b: list[QueryResult]) -> dict:
    """Mann-Whitney U test for latency distributions."""
    latencies_a = [r.latency_ms for r in results_a]
    latencies_b = [r.latency_ms for r in results_b]
    stat, p = mannwhitneyu(latencies_a, latencies_b, alternative='two-sided')
    return {"statistic": stat, "p_value": p, "significant": p < 0.05}
```

---

## PART 3: THE EIGHT EXPERIMENTS

---

### EXPERIMENT 1: Baseline vs. C2C (Primary Proof)

**Claim:** EA(C2C-Full) ≥ EA(𝔅₁) + 25pp overall; EA(C2C-Full) on L3 > 0% while EA(𝔅₁) = 0%.

#### Setup

```python
# Systems to evaluate
systems = {
    "B1-Direct": direct_llm_to_sql,          # GPT-4o, raw schema, no orchestration
    "B2-SchemaAware": schema_aware_llm,       # GPT-4o + column descriptions injected
    "C2C-Full": c2c_full_pipeline,            # all mechanisms active
}

# Questions: all 50
questions = load_all_questions()

# Run
for name, fn in systems.items():
    results[name] = evaluate_system(name, questions, fn)
    metrics[name] = compute_metrics(results[name])
    save_results(f"exp1_{name}.json", results[name])
```

#### 𝔅₁ System Prompt (Direct LLM-to-SQL)
```
System: You are a SQL expert. Given a natural language question and database schema,
generate valid SQL to answer the question.
Schema: {raw_schema_ddl}
Question: {nl_prompt}
Return only the SQL query. No explanation.
```

#### 𝔅₂ System Prompt (Schema-aware LLM)
```
System: You are a SQL expert. Given a natural language question, database schema,
and column descriptions, generate valid SQL.
Schema: {raw_schema_ddl}
Column descriptions:
{for each column: "table.column: [data type] — [description if any, else 'undocumented']"}
Question: {nl_prompt}
Return only the SQL query. No explanation.
```

#### Output to Record

```
exp1_results/
  B1-Direct_all50.json
  B2-SchemaAware_all50.json
  C2C-Full_all50.json
  
exp1_metrics_table.json:
{
  "system": ["B1-Direct", "B2-SchemaAware", "C2C-Full"],
  "L1_EA": [?, ?, ?],
  "L2_EA": [?, ?, ?],
  "L3_EA": [?, ?, ?],
  "L4_EA": [?, ?, ?],
  "overall_EA": [?, ?, ?],
  "overall_RC": [?, ?, ?],
  "overall_EM": [?, ?, ?],
  "significance_C2C_vs_B1_EA": mcnemar_result,
  "significance_C2C_vs_B2_EA": mcnemar_result
}
```

#### Acceptance Criteria
- ✅ EA(C2C-Full) > EA(𝔅₁) by ≥ 25pp → Central hypothesis supported
- ✅ EA(C2C-Full) on L3 > 0%, EA(𝔅₁) on L3 = 0% → Cross-source claim proven
- ✅ p < 0.05 on McNemar's test → Statistical significance confirmed
- ❌ If < 5pp improvement → Architecture requires revision before submission

---

### EXPERIMENT 2: Semantic Layer Impact

**Claim:** The automated semantic layer (Mechanism I) is necessary for E1 suppression and E5 prevention.

#### Setup

```python
systems = {
    "B2-SchemaAware": schema_aware_llm,       # no 𝒮, no orchestration
    "B3-PipelineNoS": c2c_pipeline_no_sem,    # 6-stage pipeline, raw schemas, no 𝒮
    "C2C-Full": c2c_full_pipeline,
}
```

Additionally, run semantic synthesis quality measurement:

```python
def measure_synthesis_quality(auto_sem_model, gold_sem_model):
    """
    Compare automatically inferred 𝒮 against gold_sem_model.
    Run AFTER prototype has built 𝒮 from the 3-source retail data.
    """
    auto_entities = set(e["name"] for e in auto_sem_model["entities"])
    gold_entities = set(e["name"] for e in gold_sem_model["entities"])
    
    auto_metrics = set(m["name"] for m in auto_sem_model["metrics"])
    gold_metrics = set(m["name"] for m in gold_sem_model["metrics"])
    
    auto_rels = set(r["from"]+r["to"] for r in auto_sem_model["cross_source_relationships"])
    gold_rels = set(r["from"]+r["to"] for r in gold_sem_model["cross_source_relationships"])
    
    # Precision: of what we inferred, how much is correct?
    entity_precision = len(auto_entities & gold_entities) / len(auto_entities)
    entity_recall = len(auto_entities & gold_entities) / len(gold_entities)
    entity_f1 = 2 * entity_precision * entity_recall / (entity_precision + entity_recall)
    
    # High-confidence subset: κ ≥ 0.80
    high_conf = [e for e in auto_sem_model["entities"] if e.get("kappa", 0) >= 0.80]
    # ... repeat above for high_conf subset
    
    return {
        "entity_coverage": entity_recall,
        "entity_precision": entity_precision,
        "entity_f1": entity_f1,
        "metric_coverage": len(auto_metrics & gold_metrics) / len(gold_metrics),
        "cross_source_rel_coverage": len(auto_rels & gold_rels) / len(gold_rels),
        "entities_inferred": len(auto_entities),
        "entities_gold": len(gold_entities),
        "metrics_inferred": len(auto_metrics),
        "metrics_gold": len(gold_metrics),
        "cross_source_rels_inferred": len(auto_rels),
        "cross_source_rels_gold": len(gold_rels),
    }
```

**Measure human review time:** Start a timer when you begin reviewing the synthesized $\mathcal{S}$. Stop when you consider it acceptable for production use. Record in hours.

#### Output to Record
- Synthesis quality table (entity coverage, metric coverage, F1, human review hours)
- Error class rate table comparing the three systems on L2 (E1, E2, E3) and L3 (E3, E5)

#### Acceptance Criteria
- ✅ E1 rate: C2C-Full < 𝔅₂ (synonym resolution working)
- ✅ E3 rate: C2C-Full < 𝔅₃ (cross-source joins working)
- ✅ E5 rate: C2C-Full = 0% on L3; 𝔅₂ > 0%, 𝔅₃ > 0%
- ✅ Entity coverage ≥ 75%; Mapping F1 ≥ 0.70

---

### EXPERIMENT 3: Agent Ablation Study

**Claim:** Pipeline decomposition is necessary beyond having a semantic layer; each stage contributes independently.

#### Setup

```python
systems = {
    "B2-SchemaAware": schema_aware_llm,        # no decomposition, no 𝒮
    "ABL-Mono": monolithic_llm_with_sem,        # single call, full 𝒮 injected
    "ABL-NoPlanner": c2c_no_planner,           # 5-stage: skip planning
    "ABL-NoValidator": c2c_no_validator,       # 6-stage: validator always approves
    "ABL-NoRetry": c2c_no_retry,              # 6-stage: K=0, no retry
    "C2C-Full": c2c_full_pipeline,
}

# Run on all 50 questions
# Focus reporting on L2 + L3 where decomposition matters most
```

#### Monolithic LLM + 𝒮 Prompt (ABL-Mono)

```
System: You are a BI SQL expert with access to a semantic model.
Using the semantic model and database schema below:
1. Classify the query intent
2. Identify required entities and metrics
3. Plan the execution approach
4. Generate the SQL
5. Verify the SQL against the semantic model

Semantic model: {full_sm_json}
Database schema: {raw_schema_ddl}
Question: {nl_prompt}

Return: {"intent": "...", "entities_used": [...], "sql": "..."}
```

#### Output to Record

```
exp3_ablation_table.json:
{
  "variant": [...],
  "EA": [...],
  "RC": [...],
  "E1_rate": [...],
  "E3_rate": [...],
  "policy_violations": [...],   // count of queries where validator would have caught issues
  "P50_ms": [...],
  "significance_vs_C2C": [mcnemar results for each variant]
}
```

#### Acceptance Criteria
- ✅ EA(C2C-Full) > EA(ABL-Mono) on L2+L3 → decomposition matters beyond semantic layer
- ✅ Removing validator increases policy violations > 0
- ✅ EA(ABL-NoRetry) < EA(C2C-Full) → retry loop contributes
- ✅ Each stage removal degrades EA vs. C2C-Full

---

### EXPERIMENT 4: Heterogeneous Data Handling

**Claim:** C2C degrades less than baselines when moving from single-source structured to multi-source heterogeneous data.

#### Setup

This experiment **reuses E1 results**—no additional runs needed. Compute degradation from E1 metrics.

```python
def compute_degradation(metrics_by_tier: dict) -> dict:
    structured_ea = (metrics_by_tier["L1_EA"] + metrics_by_tier["L2_EA"]) / 2
    hetero_ea = (metrics_by_tier["L3_EA"] + metrics_by_tier["L4_EA"]) / 2
    degradation = structured_ea - hetero_ea
    return {
        "structured_EA": structured_ea,
        "heterogeneous_EA": hetero_ea,
        "absolute_degradation_pp": degradation,
        "relative_degradation_pct": degradation / structured_ea * 100
    }

for system in ["B1-Direct", "B2-SchemaAware", "C2C-Full"]:
    degradation[system] = compute_degradation(metrics_by_tier[system])
```

#### Acceptance Criteria
- ✅ C2C-Full absolute degradation < 0.5 × 𝔅₁ absolute degradation
- ✅ C2C-Full L3 EA > 0% (baseline L3 EA = 0% — qualitative proof of concept)

---

### EXPERIMENT 5: Feedback Learning Loop

**Claim:** Mechanism IV produces measurable quality improvement over successive query batches.

#### Setup — Critical Details

This experiment runs **200 queries total** (the 50-question suite run 4 times). The feedback loop updates $\mathcal{S}$ and $\mathcal{V}$ between batches for C2C-Full but NOT for ABL-NoFeedback.

```python
# IMPORTANT: Both systems start from the SAME frozen 𝒮 snapshot
# IMPORTANT: Both systems start with an EMPTY 𝒱
# Only C2C-Full has α > 0 and writes to 𝒱 and triggers δ updates

def run_learning_loop_experiment(questions: list, n_batches: int = 4):
    systems = {
        "C2C-Full": c2c_full_pipeline,            # α=0.15, feedback enabled
        "ABL-NoFeedback": c2c_no_feedback,         # α=0, 𝒮 frozen, 𝒱 not updated
    }
    
    checkpoints = {}
    
    for batch_idx in range(n_batches):
        batch_start = batch_idx * 50
        # Note: we run the same 50 questions each batch, in the SAME order
        # The system sees the same questions again, but 𝒮 and 𝒱 have been updated
        batch_questions = questions  # all 50, same each time
        
        for name, fn in systems.items():
            batch_results = evaluate_system(name, batch_questions, fn)
            checkpoints[f"{name}_T{(batch_idx+1)*50}"] = compute_metrics(batch_results)
        
        # After each batch: trigger δ update for C2C-Full only
        c2c_full_pipeline.apply_feedback_batch()  # processes accumulated F signals
        # ABL-NoFeedback: no update
    
    return checkpoints
```

**What "feedback batch" means concretely:**
After each 50-query batch, the feedback store $\Phi$ is processed:
1. For each error class with ≥ 10 failures: trigger prompt refinement
2. For each E1 failure on a specific column: trigger schema enrichment proposal
3. Update $\kappa$ values via Equation 1 for all confirmed/rejected mappings
4. Write all successful query executions to $\mathcal{V}$

#### Output to Record

```
exp5_learning_curve.json:
{
  "C2C-Full":     {"T50_EA": ?, "T100_EA": ?, "T150_EA": ?, "T200_EA": ?},
  "C2C-Full_E1":  {"T50": ?,   "T100": ?,    "T150": ?,    "T200": ?},
  "ABL-NoFeedback": {"T50_EA": ?, "T100_EA": ?, "T150_EA": ?, "T200_EA": ?},
  "ABL-NoFeedback_E1": {"T50": ?, "T100": ?,  "T150": ?,    "T200": ?},
  
  // Statistical tests
  "trend_test_C2C": mann_whitney_trend(C2C_EA_over_time),
  "trend_test_ABL": mann_whitney_trend(ABL_EA_over_time)
}
```

**For the paper graph:**
- X-axis: Query batch (T=50, 100, 150, 200)
- Y-axis left: EA (%)
- Y-axis right: E1 error rate (%)
- Two lines per axis: C2C-Full (solid), ABL-NoFeedback (dashed)

#### Acceptance Criteria
- ✅ EA(C2C-Full, T=200) ≥ EA(C2C-Full, T=50) + 5pp
- ✅ Mann-Whitney U trend test: positive trend in C2C-Full EA is statistically significant (p < 0.05)
- ✅ ABL-NoFeedback EA is flat (Mann-Whitney U: no significant trend, p > 0.10)
- ❌ If both curves are flat → Mechanism IV has no effect; debug before publication

---

### EXPERIMENT 6: Vector Grounding Impact

**Claim:** Mechanism III ($\mathcal{V}$) reduces first-pass hallucination rate and improves over time as $\mathcal{V}$ grows.

#### Setup — Critical Detail

**Both C2C-Full and ABL-NoVector start from an empty $\mathcal{V}$.** This removes warm-up bias. The $\mathcal{V}$ grows naturally through the 200-query session.

```python
# Reuse the Experiment 5 200-query run
# Add ABL-NoVector as a third arm: full pipeline, no grounding retrieval (G = ∅)
# 𝒮 updates still happen in ABL-NoVector (α=0.15); only 𝒱 retrieval is disabled

systems = {
    "C2C-Full": c2c_full_pipeline,          # 𝒮 + δ + 𝒱 all active
    "ABL-NoVector": c2c_no_vector,          # 𝒮 + δ active; 𝒱 retrieval disabled
}

# Both start with EMPTY 𝒱 and SAME frozen 𝒮

for batch_idx in range(4):  # 4 × 50 = 200 queries
    for name, fn in systems.items():
        batch_results = evaluate_system(name, questions, fn,
                                        record_first_pass=True)  # ← key: record pre-retry success
        checkpoints[f"{name}_T{(batch_idx+1)*50}"] = {
            "first_pass_EA": ...,   # success on attempt 0 only
            "final_EA": ...,        # after retries
            "E1_rate": ...
        }
    
    # Both systems update 𝒮 via δ
    # Only C2C-Full writes to 𝒱 and uses 𝒱 in next batch
```

#### Output to Record

```
exp6_vector_grounding.json:
{
  "C2C-Full": {
    "T50":  {"first_pass_EA": ?, "final_EA": ?, "E1_rate": ?, "V_size": 0},
    "T100": {"first_pass_EA": ?, "final_EA": ?, "E1_rate": ?, "V_size": ?},
    "T150": {"first_pass_EA": ?, "final_EA": ?, "E1_rate": ?, "V_size": ?},
    "T200": {"first_pass_EA": ?, "final_EA": ?, "E1_rate": ?, "V_size": ?},
  },
  "ABL-NoVector": {
    "T50":  {"first_pass_EA": ?, "final_EA": ?, "E1_rate": ?, "V_size": 0},
    // V_size stays 0 throughout
  }
}
```

#### Acceptance Criteria
- ✅ By T=100: first-pass EA(C2C-Full) > first-pass EA(ABL-NoVector) by ≥ 8pp on L1+L2
- ✅ E1 rate declines faster in C2C-Full than ABL-NoVector
- ✅ C2C-Full final EA at T=200 > ABL-NoVector final EA at T=200

---

### EXPERIMENT 7: Error Taxonomy Distribution Analysis

**Claim:** Different architectural decisions suppress different error classes, validating the E1–E5 taxonomy.

#### Setup

Reuse result logs from Experiments 1 and 3. No new runs needed.

```python
# From exp1 results: B1-Direct, B2-SchemaAware, C2C-Full
# From exp3 results: ABL-Mono
# Compute error distribution per system

def error_distribution(results: list[QueryResult]) -> dict:
    n = len(results)
    errors = [r.error_class for r in results if r.error_class is not None]
    return {
        "E1": errors.count("E1") / n,
        "E2": errors.count("E2") / n,
        "E3": errors.count("E3") / n,
        "E4": errors.count("E4") / n,
        "E5": errors.count("E5") / n,
        "No_Error": sum(r.error_class is None for r in results) / n,
    }
```

#### Output to Record

A single stacked bar chart with one bar per system, stacked by error class. Values in the table:

| System | E1 | E2 | E3 | E4 | E5 | No Error |
|---|---|---|---|---|---|---|
| B1-Direct | | | | | | |
| B2-SchemaAware | | | | | | |
| ABL-Mono | | | | | | |
| C2C-Full | | | | | | |

#### What to Look For

The taxonomy predicts:
- E5 should be > 0% in all baselines on L3; = 0% in C2C-Full
- E1 should be highest in B1-Direct (raw schema, no synonyms) and lowest in C2C-Full
- E3 should decrease from B2 to ABL-Mono (𝒮 helps) to C2C-Full (𝒮 + retry helps more)
- E2 should be similar across all systems (requires semantic correction, not just structure)

---

### EXPERIMENT 8: Latency–Accuracy Tradeoff

**Claim:** C2C's latency overhead is quantifiable and justified by the accuracy gain; cache hits recover it.

#### Setup

Reuse latency logs from all previous experiments. No new runs needed.

```python
# Collect from E1/E3 timing logs
latency_report = {}
for system in ["B1-Direct", "B2-SchemaAware", "ABL-NoRetry", "ABL-NoVector", "C2C-Full"]:
    times = [r.latency_ms for r in results[system]]
    latency_report[system] = {
        "P50": percentile(times, 50),
        "P95": percentile(times, 95),
        "P99": percentile(times, 99),
        "mean": mean(times),
        "overhead_vs_B1": P50 - B1_P50
    }

# Additionally: simulate cache hits
# Take the 20% most frequently repeated query intents
# Report the latency when served from Redis cache (sub-10ms expected)
```

#### Stage-Level Latency Breakdown

Instrument each pipeline stage with timers:

```python
stage_times = {
    "semantic_graph_lookup": [],    # 𝒮 retrieval
    "vector_retrieval": [],          # 𝒱 k-NN fetch
    "planner_llm_call": [],          # Planner LLM latency
    "sql_generator_llm_call": [],    # SQL Gen LLM latency
    "validator_llm_call": [],        # Validator LLM latency
    "db_execution": [],              # Actual SQL execution
    "insight_agent_llm_call": [],    # Insight Agent latency
    "retry_overhead": [],            # Extra latency from retries
}
```

#### Output to Record

Two outputs:
1. **Latency table** (P50/P95 per variant vs. EA)
2. **Stage breakdown chart**: horizontal stacked bar showing where time goes per variant

#### Acceptance Criteria
- ✅ C2C-Full P50 overhead over 𝔅₁ is documented (expected: 2–5 seconds for LLM calls)
- ✅ Cache hit P50 < 𝔅₁ P50 (cache pays off)
- ✅ Pareto chart shows C2C-Full dominates ABL-NoRetry on accuracy at a documented latency cost

---

## PART 4: RUNNING ORDER AND TIMELINE

### Recommended Execution Order

```
Day 1 (3–4 hours):
  ✅ Build 50-question suite (2 hours — most important step)
  ✅ Build gold semantic model (1 hour)
  ✅ Set up eval harness + metric functions (1 hour)

Day 2 (4–5 hours):
  ✅ Run Experiment 1 (Baseline vs. C2C) — all 50 questions × 3 systems
  ✅ Run Experiment 2 (Semantic Layer) — semantic synthesis quality + 50 questions × 3 systems
  ✅ Run Experiment 7 (Error Taxonomy) — reuse E1/E2 logs, no new runs

Day 3 (4–5 hours):
  ✅ Run Experiment 3 (Agent Ablation) — 50 questions × 6 variants (most expensive)
  ✅ Run Experiment 4 (Heterogeneous) — reuse E1 results, 0 new runs
  ✅ Run Experiment 8 (Latency) — reuse E1/E3 timing logs, minimal extra work

Day 4 (5–6 hours):
  ✅ Run Experiments 5 + 6 together — 200 queries × 3 arms (C2C-Full, ABL-NoFeedback, ABL-NoVector)
  This is the most time-consuming run. Start early.
```

### What Generates What

| Paper Table / Figure | Source Experiment |
|---|---|
| Main results table (Table 2) | Experiment 1 |
| Semantic synthesis quality sub-table | Experiment 2 |
| Error class rate table (Exp 2) | Experiment 2 |
| Ablation table | Experiment 3 |
| Heterogeneous degradation table | Experiment 4 (from E1 data) |
| Learning curve graph | Experiment 5 |
| Vector grounding table | Experiment 6 |
| Error taxonomy distribution chart | Experiment 7 (from E1/E3 data) |
| Latency–accuracy Pareto | Experiment 8 (from all timing logs) |
| Appendix F (α sensitivity) | α validation run (20 queries, < 1 hour) |

---

## PART 5: RESULT INTERPRETATION GUIDE

### If Your Results Are Weaker Than Expected

**If overall EA improvement is only 10–15pp (not 25pp):**
- Check if gold SQL is correct — a wrong gold SQL produces false negatives in RC
- Verify the semantic model was actually used (log whether 𝒮 was consulted per query)
- Check if the 𝒮 threshold $\theta_\text{exec}$ is too restrictive (may be rejecting valid queries)
- Lower the claim in the paper: "We demonstrate X pp improvement on L1+L2 queries, with larger gains expected as 𝒮 quality improves on L3."

**If E5 rate is not 0% for C2C-Full on L3:**
- Cross-source relationships in 𝒮 have low κ — check the auto-inferred join keys
- The Planner is not detecting the cross-source nature of the query — check the planning prompt
- Fix 𝒮 and re-run; E5 = 0% on L3 is the single most important qualitative result

**If the learning curve (Exp 5) is flat for C2C-Full:**
- Check that feedback loop is actually firing: inspect $\Phi$ after each batch
- $\theta_\text{batch}$ may be too high (10 failures before refinement triggers) — lower to 5
- 50 questions may not generate enough of any one error class to trigger refinement — run more queries (try 300 total, 6 batches)

**If vector grounding (Exp 6) shows no benefit by T=100:**
- Check that $\mathcal{V}$ is actually being written to (inspect store size after each batch)
- Ensure the k-NN retrieval is returning matches (cosine similarity > 0.85 threshold may be too strict — try 0.70)
- The embedding model may not capture semantic similarity well for SQL column names — consider domain-specific embeddings

### Minimum Bar for Publication

| Experiment | Minimum result needed to publish |
|---|---|
| E1 | EA improvement ≥ 10pp AND L3 EA(C2C) > 0% while baseline = 0% |
| E2 | E1 rate lower in C2C vs. baseline; E5 rate = 0% in C2C on L3 |
| E3 | At least 2 of 4 ablation variants show statistically significant degradation vs. C2C-Full |
| E4 | C2C degradation < 2× baseline degradation (can be shown qualitatively from L3=0% vs >0%) |
| E5 | Positive trend in EA (even 3pp improvement is publishable with significance) |
| E6 | First-pass EA gap between C2C-Full and ABL-NoVector ≥ 5pp by T=150 |
| E7 | Error distributions show qualitatively different profiles per system |
| E8 | Latency documented; cache benefit demonstrated |

---

## PART 6: RESULT TABLE TEMPLATES

Copy these into the paper after filling in from your experimental runs.

### Table 2: Main Results (Experiment 1)

| System | L1 EA | L2 EA | L3 EA | L4 EA | Overall EA | Overall RC | EM |
|---|---|---|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | | | | | | | |
| 𝔅₂: Schema-aware LLM | | | | | | | |
| C2C-Full | | | | | | | |
| *Δ (C2C vs. 𝔅₁)* | | | | | | | |

### Table 3: Semantic Synthesis Quality (Experiment 2)

| Metric | Value |
|---|---|
| Entities inferred | — / — (gold) |
| Entity coverage | — |
| Metrics inferred | — / — |
| Metric coverage | — |
| Cross-source relationships | — / — |
| Mapping F1 (κ ≥ 0.80) | — |
| Human review time | — hours |

### Table 4: Error Class Rates (Experiments 2 + 7)

| System | E1 | E2 | E3 | E4 | E5 | No Error |
|---|---|---|---|---|---|---|
| 𝔅₁: Direct | | | | | | |
| 𝔅₂: Schema-aware | | | | | | |
| ABL-Mono | | | | | | |
| ABL-NoRetry | | | | | | |
| C2C-Full | | | | | | |

### Table 5: Ablation Results (Experiment 3)

| Variant | EA | RC | E1 Rate | E3 Rate | P50 (ms) |
|---|---|---|---|---|---|
| 𝔅₂: Schema-aware (no decomp) | | | | | |
| ABL-Mono (no decomp + 𝒮) | | | | | |
| ABL-NoPlanner | | | | | |
| ABL-NoValidator | | | | | |
| ABL-NoRetry | | | | | |
| C2C-Full | | | | | |

### Table 6: Latency–Accuracy Pareto (Experiment 8)

| Variant | P50 (ms) | P95 (ms) | Overall EA | Latency vs. 𝔅₁ |
|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | | | | +0ms (baseline) |
| 𝔅₂: Schema-aware LLM | | | | +Xms |
| ABL-NoRetry | | | | +Xms |
| C2C-Full | | | | +Xms |
| C2C-Full (cache hit) | | | | −Xms |

---

## PART 7: CODE CHECKLIST BEFORE RUNNING

```
Before Experiment 1:
□ 50-question suite built, annotated, stored in eval/questions/
□ Gold semantic model built, stored in eval/gold_semantic_model.json
□ Three data sources connected and accessible
□ 𝒮 snapshot frozen (do not let it update during E1 evaluation)
□ 𝒱 is EMPTY at start of E1
□ All three system implementations callable with same interface
□ Timing instrumentation in place
□ Result serialization to JSON working

Before Experiment 5+6:
□ Feedback loop implementation verified on 5-query smoke test
□ 𝒱 write confirmed (check store size after 10 queries)
□ δ updates confirmed (check 𝒮 node κ values before/after a feedback batch)
□ ABL-NoFeedback confirmed: α=0, 𝒮 never changes, 𝒱 never written
□ ABL-NoVector confirmed: retrieval step returns empty list G=∅

Before submission:
□ All result tables filled from actual runs (no — cells)
□ Appendix F (α sensitivity) filled
□ Statistical significance computed for every paired comparison
□ All result files committed to github.com/bankupalliravi/chaos2clarity/eval/
```

---

*This document is the companion to the Chaos 2 Clarity paper (v4). Run experiments in the order specified. Fill result tables. Update the paper. Submit.*
