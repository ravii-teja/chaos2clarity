"""
Chaos 2 Clarity — Full Experiment Runner
Runs all 8 experiments locally and saves results.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from datetime import datetime

# ── API Keys ──
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not GOOGLE_API_KEY or not OPENAI_API_KEY:
    print("❌ Set GOOGLE_API_KEY and OPENAI_API_KEY environment variables")
    sys.exit(1)

# ── Initialize LLM Clients ──
import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
gemini = genai.GenerativeModel('gemini-1.5-pro')

from openai import OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

print("✅ LLM clients initialized")

# ── Setup directories ──
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
EVAL_DIR = os.path.join(os.path.dirname(__file__), 'eval')
RESULTS_DIR = os.path.join(EVAL_DIR, 'results')
QUESTIONS_DIR = os.path.join(EVAL_DIR, 'questions')
FIGURES_DIR = os.path.join(os.path.dirname(__file__), 'figures')

for d in [DATA_DIR, RESULTS_DIR, QUESTIONS_DIR, FIGURES_DIR]:
    os.makedirs(d, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# PHASE 1: DATA GENERATION
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE 1: GENERATING DATA ENVIRONMENT")
print("="*70)

from src.data_generator import setup_full_environment, get_schema_ddl, get_column_descriptions_str
import duckdb

DB_PATH = os.path.join(DATA_DIR, 'retail.duckdb')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn, sf_accounts, sf_opportunities, logistics, emails_df, tickets_df, status_codes = \
    setup_full_environment(data_dir=DATA_DIR, db_path=DB_PATH)

schema_ddl = get_schema_ddl(conn)
col_descriptions = get_column_descriptions_str()

# Save schema snapshot
with open(os.path.join(EVAL_DIR, 'schema_snapshot.sql'), 'w') as f:
    f.write(schema_ddl)

# ═══════════════════════════════════════════════════════════════
# PHASE 2: BUILD 50-QUESTION SUITE
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("PHASE 2: BUILDING 50-QUESTION BI SUITE")
print("="*70)

def create_question(qid, tier, nl_prompt, gold_sql, error_class, error_note=''):
    try:
        result = conn.execute(gold_sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        rows = [dict(zip(columns, row)) for row in result]
        gold_result = {'rows': rows, 'columns': columns}
    except Exception as e:
        print(f'  ⚠️ Gold SQL failed for {qid}: {e}')
        gold_result = None
    return {
        'id': qid, 'tier': tier, 'nl_prompt': nl_prompt,
        'gold_sql': gold_sql, 'gold_result': gold_result,
        'primary_error_class': error_class, 'error_note': error_note,
    }

questions = []

# L1 — Single-Source Metric (15)
l1 = [
    ('L1-01', 'What was total gross revenue last quarter?',
     "SELECT SUM(line_value) as total_revenue FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL 90 DAY", 'E1'),
    ('L1-02', 'How many orders were placed this year?',
     "SELECT COUNT(*) as order_count FROM orders WHERE EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)", 'E1'),
    ('L1-03', 'What is our average order value?',
     "SELECT AVG(line_value) as avg_order_value FROM orders", 'E2'),
    ('L1-04', 'How many unique customers made a purchase in the last 6 months?',
     "SELECT COUNT(DISTINCT customer_id) as unique_customers FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL 180 DAY", 'E1'),
    ('L1-05', 'What is the total number of products in our catalog?',
     "SELECT COUNT(*) as product_count FROM products", ''),
    ('L1-06', 'What was our highest single-order revenue ever?',
     "SELECT MAX(line_value) as max_revenue FROM orders", 'E1'),
    ('L1-07', 'How many orders were cancelled this year?',
     "SELECT COUNT(*) as cancelled_count FROM orders WHERE status = 'cancelled' AND EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE)", 'E1'),
    ('L1-08', 'What is our total revenue for Electronics products?',
     "SELECT SUM(o.line_value) as electronics_revenue FROM orders o JOIN products p ON o.product_id = p.id WHERE p.category = 'Electronics'", 'E1'),
    ('L1-09', 'How many orders shipped in the last 30 days?',
     "SELECT COUNT(*) as shipped_count FROM orders WHERE ship_date >= CURRENT_DATE - INTERVAL 30 DAY AND ship_date IS NOT NULL", 'E1'),
    ('L1-10', 'What is the revenue for the top-selling product?',
     "SELECT p.name, SUM(o.line_value) as rev FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.name ORDER BY rev DESC LIMIT 1", 'E1'),
    ('L1-11', 'How many new customers signed up this year?',
     "SELECT COUNT(*) as new_customers FROM customers WHERE EXTRACT(YEAR FROM created_at) = EXTRACT(YEAR FROM CURRENT_DATE)", 'E1'),
    ('L1-12', 'What is our total cost of goods sold this year?',
     "SELECT SUM(p.cost_price * o.quantity) as cogs FROM orders o JOIN products p ON o.product_id = p.id WHERE EXTRACT(YEAR FROM o.order_date) = EXTRACT(YEAR FROM CURRENT_DATE)", 'E1'),
    ('L1-13', 'What percentage of orders were returned?',
     "SELECT ROUND(100.0 * COUNT(CASE WHEN status='returned' THEN 1 END) / COUNT(*), 2) as return_pct FROM orders", 'E2'),
    ('L1-14', 'How many distinct product categories do we sell?',
     "SELECT COUNT(DISTINCT category) as category_count FROM products", ''),
    ('L1-15', 'What was our total revenue last year?',
     "SELECT SUM(line_value) as total_revenue FROM orders WHERE EXTRACT(YEAR FROM order_date) = EXTRACT(YEAR FROM CURRENT_DATE) - 1", 'E1'),
]
for qid, prompt, sql, ec in l1:
    questions.append(create_question(qid, 'L1', prompt, sql, ec))

# L2 — Multi-Table Join (15)
l2 = [
    ('L2-01', 'What is the revenue breakdown by product category?',
     "SELECT p.category, SUM(o.line_value) as revenue FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.category ORDER BY revenue DESC", 'E1'),
    ('L2-02', 'Which customers placed more than 5 orders?',
     "SELECT c.name, COUNT(o.id) as order_count FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name HAVING COUNT(o.id) > 5 ORDER BY order_count DESC", 'E3'),
    ('L2-03', 'Who are our top 10 customers by lifetime revenue?',
     "SELECT c.name, SUM(o.line_value) as lifetime_rev FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY lifetime_rev DESC LIMIT 10", 'E1'),
    ('L2-04', 'What is the average days between order and shipment per product category?',
     "SELECT p.category, AVG(o.ship_date - o.order_date) as avg_ship_days FROM orders o JOIN products p ON o.product_id = p.id WHERE o.ship_date IS NOT NULL GROUP BY p.category", 'E2'),
    ('L2-05', 'Which product categories have more than 10 percent return rate?',
     "SELECT p.category, ROUND(100.0 * COUNT(CASE WHEN o.status='returned' THEN 1 END) / COUNT(*), 2) as return_rate FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.category HAVING ROUND(100.0 * COUNT(CASE WHEN o.status='returned' THEN 1 END) / COUNT(*), 2) > 10", 'E2'),
    ('L2-06', 'What is the revenue per customer segment?',
     "SELECT c.segment, SUM(o.line_value) as segment_revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.segment ORDER BY segment_revenue DESC", 'E3'),
    ('L2-07', 'Which sales rep closed the most orders?',
     "SELECT r.rep_name, COUNT(o.id) as order_count FROM orders o JOIN sales_reps r ON o.sales_rep_id = r.id GROUP BY r.rep_name ORDER BY order_count DESC LIMIT 1", 'E3'),
    ('L2-08', 'What is the monthly revenue trend for the last 12 months?',
     "SELECT DATE_TRUNC('month', order_date) as month, SUM(line_value) as monthly_revenue FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL 365 DAY GROUP BY month ORDER BY month", 'E2'),
    ('L2-09', 'Which products had zero orders in the last 60 days?',
     "SELECT p.name FROM products p WHERE p.id NOT IN (SELECT DISTINCT product_id FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL 60 DAY)", 'E3'),
    ('L2-10', 'What is the average order value per customer segment?',
     "SELECT c.segment, AVG(o.line_value) as avg_order_value FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.segment", 'E2'),
    ('L2-11', 'What is the revenue from completed orders versus pending orders?',
     "SELECT status, SUM(line_value) as revenue FROM orders WHERE status IN ('completed', 'pending') GROUP BY status", 'E2'),
    ('L2-12', 'Which product has the highest total quantity sold?',
     "SELECT p.name, SUM(o.quantity) as total_qty FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.name ORDER BY total_qty DESC LIMIT 1", 'E3'),
    ('L2-13', 'What is the total discount given across all orders?',
     "SELECT SUM(line_value * discount_pct / 100.0) as total_discount FROM orders WHERE discount_pct > 0", 'E2'),
    ('L2-14', 'What is the average number of items per order by category?',
     "SELECT p.category, AVG(o.quantity) as avg_items FROM orders o JOIN products p ON o.product_id = p.id GROUP BY p.category", 'E3'),
    ('L2-15', 'What percentage of revenue comes from our top 20 percent of customers?',
     "WITH customer_rev AS (SELECT customer_id, SUM(line_value) as rev FROM orders GROUP BY customer_id), ranked AS (SELECT rev, NTILE(5) OVER (ORDER BY rev DESC) as quintile FROM customer_rev) SELECT ROUND(100.0 * SUM(CASE WHEN quintile = 1 THEN rev END) / SUM(rev), 2) as top20_pct FROM ranked", 'E2'),
]
for qid, prompt, sql, ec in l2:
    questions.append(create_question(qid, 'L2', prompt, sql, ec))

# L3 — Cross-Source (10)
l3 = [
    ('L3-01', 'Which customers with active CRM deals had delivery issues?',
     "SELECT DISTINCT c.name FROM customers c JOIN sf_accounts sa ON c.email = sa.email_address JOIN sf_opportunities so ON sa.account_id = so.account_id JOIN orders o ON c.id = o.customer_id JOIN logistics_deliveries ld ON o.shipping_id = ld.shipping_ref WHERE so.stage NOT IN ('Closed Won', 'Closed Lost') AND ld.status_code IN (5, 6)", 'E5'),
    ('L3-02', 'What is the average deal size for customers whose deliveries were delayed?',
     "SELECT AVG(so.amount) as avg_deal_size FROM sf_opportunities so JOIN sf_accounts sa ON so.account_id = sa.account_id JOIN customers c ON c.email = sa.email_address JOIN orders o ON c.id = o.customer_id JOIN logistics_deliveries ld ON o.shipping_id = ld.shipping_ref WHERE ld.status_code = 5", 'E5'),
    ('L3-03', 'Which of our top 10 revenue customers have an open CRM opportunity?',
     "WITH top10 AS (SELECT c.id, c.name, c.email, SUM(o.line_value) as rev FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name, c.email ORDER BY rev DESC LIMIT 10) SELECT t.name, so.deal_name, so.stage FROM top10 t JOIN sf_accounts sa ON t.email = sa.email_address JOIN sf_opportunities so ON sa.account_id = so.account_id WHERE so.stage NOT IN ('Closed Won', 'Closed Lost')", 'E5'),
    ('L3-04', 'What is the delivery success rate for Enterprise segment customers from CRM?',
     "SELECT ROUND(100.0 * COUNT(CASE WHEN ld.status_code = 4 THEN 1 END) / COUNT(*), 2) as success_rate FROM sf_accounts sa JOIN customers c ON c.email = sa.email_address JOIN orders o ON c.id = o.customer_id JOIN logistics_deliveries ld ON o.shipping_id = ld.shipping_ref WHERE sa.sf_segment = 'Enterprise'", 'E5'),
    ('L3-05', 'Total revenue from customers whose CRM deals closed successfully?',
     "SELECT SUM(o.line_value) as total_revenue FROM orders o JOIN customers c ON o.customer_id = c.id JOIN sf_accounts sa ON c.email = sa.email_address JOIN sf_opportunities so ON sa.account_id = so.account_id WHERE so.stage = 'Closed Won'", 'E5'),
    ('L3-06', 'Which customers have both high order value and a delayed shipment?',
     "SELECT DISTINCT c.name, SUM(o.line_value) as total_rev FROM customers c JOIN orders o ON c.id = o.customer_id JOIN logistics_deliveries ld ON o.shipping_id = ld.shipping_ref WHERE ld.status_code IN (5, 6) GROUP BY c.name HAVING SUM(o.line_value) > (SELECT AVG(line_value) * 2 FROM orders)", 'E5'),
    ('L3-07', 'What is the on-time delivery rate by CRM deal stage?',
     "SELECT so.stage, ROUND(100.0 * COUNT(CASE WHEN ld.status_code = 4 THEN 1 END) / COUNT(*), 2) as ontime_rate FROM sf_opportunities so JOIN sf_accounts sa ON so.account_id = sa.account_id JOIN customers c ON c.email = sa.email_address JOIN orders o ON c.id = o.customer_id JOIN logistics_deliveries ld ON o.shipping_id = ld.shipping_ref GROUP BY so.stage", 'E5'),
    ('L3-08', 'Which product categories have delivery complaints from high-value CRM accounts?',
     "SELECT p.category, COUNT(*) as complaint_count FROM products p JOIN orders o ON p.id = o.product_id JOIN logistics_deliveries ld ON o.shipping_id = ld.shipping_ref JOIN customers c ON o.customer_id = c.id JOIN sf_accounts sa ON c.email = sa.email_address WHERE ld.status_code IN (5, 6) AND sa.annual_revenue > 1000000 GROUP BY p.category ORDER BY complaint_count DESC", 'E5'),
    ('L3-09', 'What is the average time from CRM deal close to first order?',
     "SELECT AVG(o.min_order_date - CAST(so.close_date AS DATE)) as avg_days FROM sf_opportunities so JOIN sf_accounts sa ON so.account_id = sa.account_id JOIN customers c ON c.email = sa.email_address JOIN (SELECT customer_id, MIN(order_date) as min_order_date FROM orders GROUP BY customer_id) o ON c.id = o.customer_id WHERE so.stage = 'Closed Won'", 'E5'),
    ('L3-10', 'Which logistics carrier has the worst on-time rate for our top revenue customers?',
     "WITH top_customers AS (SELECT c.id FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY SUM(o.line_value) DESC LIMIT 100) SELECT ld.carrier_name, ROUND(100.0 * COUNT(CASE WHEN ld.status_code = 4 THEN 1 END) / COUNT(*), 2) as ontime_rate FROM logistics_deliveries ld JOIN orders o ON ld.shipping_ref = o.shipping_id WHERE o.customer_id IN (SELECT id FROM top_customers) GROUP BY ld.carrier_name ORDER BY ontime_rate ASC LIMIT 1", 'E5'),
]
for qid, prompt, sql, ec in l3:
    questions.append(create_question(qid, 'L3', prompt, sql, ec))

# L4 — Unstructured + Structured RAG (10)
l4 = [
    ('L4-01', 'Summarize delivery complaint themes for our top 10 revenue customers.',
     "SELECT c.name, SUM(o.line_value) as rev FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY rev DESC LIMIT 10", 'E4'),
    ('L4-02', 'Which product categories have the most negative sentiment in support tickets?',
     "SELECT p.category, COUNT(*) as count FROM products p JOIN orders o ON p.id = o.product_id GROUP BY p.category ORDER BY count DESC", 'E4'),
    ('L4-03', 'What common complaints appear for accounts with delayed shipments?',
     "SELECT ld.carrier_name, COUNT(*) as delay_count FROM logistics_deliveries ld WHERE ld.status_code = 5 GROUP BY ld.carrier_name ORDER BY delay_count DESC", 'E4'),
    ('L4-04', 'Find customers who mentioned competitor products in support interactions.',
     "SELECT DISTINCT customer_id FROM orders LIMIT 20", 'E4'),
    ('L4-05', 'What were the top 3 reasons for returns based on return notes?',
     "SELECT reason, COUNT(*) as count FROM returns GROUP BY reason ORDER BY count DESC LIMIT 3", 'E4'),
    ('L4-06', 'Which sales reps have customers with the most positive feedback?',
     "SELECT r.rep_name, COUNT(o.id) as count FROM sales_reps r JOIN orders o ON r.id = o.sales_rep_id WHERE o.status = 'completed' GROUP BY r.rep_name ORDER BY count DESC LIMIT 5", 'E4'),
    ('L4-07', 'Summarize key themes in feedback for Enterprise segment accounts.',
     "SELECT c.segment, COUNT(*) as count FROM customers c JOIN orders o ON c.id = o.customer_id WHERE c.segment = 'Enterprise' GROUP BY c.segment", 'E4'),
    ('L4-08', 'Which logistics partners have the most damaged goods complaints?',
     "SELECT ld.carrier_name, COUNT(*) as count FROM logistics_deliveries ld WHERE ld.status_code IN (5, 6) GROUP BY ld.carrier_name ORDER BY count DESC", 'E4'),
    ('L4-09', 'What do churned customers say were their top reasons for leaving?',
     "SELECT reason, COUNT(*) as count FROM returns GROUP BY reason ORDER BY count DESC", 'E4'),
    ('L4-10', 'Find orders where customer complaints mention a product defect.',
     "SELECT o.id, p.name FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = 'returned' LIMIT 20", 'E4'),
]
for qid, prompt, sql, ec in l4:
    questions.append(create_question(qid, 'L4', prompt, sql, ec))

# Save questions
for q in questions:
    filepath = os.path.join(QUESTIONS_DIR, f"{q['id']}.json")
    with open(filepath, 'w') as f:
        json.dump(q, f, indent=2, default=str)

success = sum(1 for q in questions if q['gold_result'] is not None)
print(f"✅ {len(questions)} questions created ({success} gold SQL valid)")

# ── Build gold semantic model ──
from src.semantic_layer import build_gold_semantic_model
gold_model = build_gold_semantic_model()
with open(os.path.join(EVAL_DIR, 'gold_semantic_model.json'), 'w') as f:
    f.write(gold_model.to_json())
print(f"✅ Gold model: {len(gold_model.entities)} entities, {len(gold_model.metrics)} metrics")

# ═══════════════════════════════════════════════════════════════
# PHASE 3: RUN EXPERIMENTS
# ═══════════════════════════════════════════════════════════════
from src.vector_store import VectorStore
from src.feedback_loop import FeedbackLoop
from src.orchestration import (
    C2CPipeline, C2CMonolithic, C2CNoPlanner,
    C2CNoValidator, C2CNoRetry, C2CNoVector, C2CNoFeedback
)
from src.baselines import B1DirectLLM, B2SchemaAwareLLM, B3PipelineNoSem
from src.eval_harness import evaluate_system, compute_metrics, save_results, compute_degradation, compute_metrics_by_tier
from src.stats import mcnemar_test, mann_whitney_latency, run_all_significance_tests

RATE_LIMIT = 1.5  # seconds between API calls

def rate_limited(fn):
    def wrapper(nl_prompt):
        time.sleep(RATE_LIMIT)
        return fn(nl_prompt)
    return wrapper

# ──────────────────────────────────────────────────────────
# EXPERIMENT 1: Baseline vs. C2C
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENT 1: BASELINE vs C2C (Central Hypothesis)")
print("="*70)

b1 = B1DirectLLM(openai_client, conn, schema_ddl)
b2 = B2SchemaAwareLLM(openai_client, conn, schema_ddl, col_descriptions)

sm_e1 = build_gold_semantic_model()
vs_e1 = VectorStore(collection_name='c2c_exp1')
fl_e1 = FeedbackLoop(alpha=0.15)
c2c = C2CPipeline(gemini, conn, sm_e1, vs_e1, fl_e1, schema_ddl, max_retries=3)

exp1_results = {}
exp1_metrics = {}

for sys_name, sys_fn in [('B1-Direct', b1), ('B2-SchemaAware', b2), ('C2C-Full', c2c)]:
    print(f"\n▶ Running {sys_name} ({len(questions)} questions)...")
    t_start = time.time()
    results = evaluate_system(sys_name, questions, rate_limited(sys_fn))
    elapsed = time.time() - t_start
    exp1_results[sys_name] = results
    exp1_metrics[sys_name] = compute_metrics(results)
    save_results(results, os.path.join(RESULTS_DIR, f'exp1_{sys_name}.json'))
    m = exp1_metrics[sys_name]
    print(f"  EA: {m['EA']*100:.1f}%  RC: {m['RC']*100:.1f}%  P50: {m['P50_ms']:.0f}ms  ({elapsed:.0f}s)")

# Print Experiment 1 table
print(f"\n{'System':<25} {'L1 EA':>8} {'L2 EA':>8} {'L3 EA':>8} {'L4 EA':>8} {'EA':>8} {'RC':>8}")
print("-"*80)
for s in ['B1-Direct', 'B2-SchemaAware', 'C2C-Full']:
    m = exp1_metrics[s]
    print(f"{s:<25} {m.get('L1_EA',0)*100:>7.1f}% {m.get('L2_EA',0)*100:>7.1f}% {m.get('L3_EA',0)*100:>7.1f}% {m.get('L4_EA',0)*100:>7.1f}% {m['EA']*100:>7.1f}% {m['RC']*100:>7.1f}%")

delta = exp1_metrics['C2C-Full']['EA'] - exp1_metrics['B1-Direct']['EA']
print(f"\n📊 C2C vs B1 delta: {delta*100:+.1f}pp  {'✅ PASS' if delta >= 0.25 else '⚠️ < 25pp' if delta >= 0.05 else '❌ FAIL'}")

# Significance tests
sig = run_all_significance_tests(exp1_results, 'C2C-Full')
with open(os.path.join(RESULTS_DIR, 'exp1_significance.json'), 'w') as f:
    json.dump(sig, f, indent=2, default=str)
for t, r in sig.items():
    print(f"  {t}: p={r.get('p_value',1):.4f} {'✅' if r.get('significant') else '❌'}")

# ──────────────────────────────────────────────────────────
# EXPERIMENT 2: Semantic Layer Impact
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENT 2: SEMANTIC LAYER IMPACT")
print("="*70)

b3 = B3PipelineNoSem(gemini, conn, schema_ddl)
print(f"\n▶ Running B3-PipelineNoSem ({len(questions)} questions)...")
b3_results = evaluate_system('B3-PipelineNoSem', questions, rate_limited(b3))
b3_metrics = compute_metrics(b3_results)
save_results(b3_results, os.path.join(RESULTS_DIR, 'exp2_B3.json'))
print(f"  EA: {b3_metrics['EA']*100:.1f}%  RC: {b3_metrics['RC']*100:.1f}%")

# Semantic synthesis quality
from src.semantic_layer import synthesize_semantic_model, measure_synthesis_quality
print("\n▶ Running automated semantic synthesis...")
try:
    auto_model = synthesize_semantic_model(conn, gemini, schema_ddl)
    synth_quality = measure_synthesis_quality(auto_model, gold_model)
    print("TABLE 3: Semantic Synthesis Quality")
    for k, v in synth_quality.items():
        print(f"  {k}: {v}")
    with open(os.path.join(RESULTS_DIR, 'exp2_synthesis_quality.json'), 'w') as f:
        json.dump(synth_quality, f, indent=2)
except Exception as e:
    print(f"  ⚠️ Synthesis error: {e}")
    synth_quality = {}

# Error rates comparison
print(f"\n{'System':<25} {'E1':>6} {'E2':>6} {'E3':>6} {'E5':>6} {'EA':>8}")
print("-"*60)
for sys_name, res in [('B2-SchemaAware', exp1_results['B2-SchemaAware']),
                       ('B3-PipelineNoSem', b3_results),
                       ('C2C-Full', exp1_results['C2C-Full'])]:
    m = compute_metrics(res)
    ed = m.get('error_distribution', {})
    print(f"{sys_name:<25} {ed.get('E1',0)*100:>5.1f}% {ed.get('E2',0)*100:>5.1f}% {ed.get('E3',0)*100:>5.1f}% {ed.get('E5',0)*100:>5.1f}% {m['EA']*100:>7.1f}%")

# ──────────────────────────────────────────────────────────
# EXPERIMENT 3: Agent Ablation Study
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENT 3: AGENT ABLATION STUDY")
print("="*70)

exp3_results = {'B2-SchemaAware': exp1_results['B2-SchemaAware'], 'C2C-Full': exp1_results['C2C-Full']}
exp3_metrics = {'B2-SchemaAware': exp1_metrics['B2-SchemaAware'], 'C2C-Full': exp1_metrics['C2C-Full']}

sm_e3 = build_gold_semantic_model()
ablation_systems = {
    'ABL-Mono': C2CMonolithic(gemini, conn, sm_e3, schema_ddl),
    'ABL-NoPlanner': C2CNoPlanner(gemini, conn, sm_e3, VectorStore('abl_np'), FeedbackLoop(), schema_ddl),
    'ABL-NoValidator': C2CNoValidator(gemini, conn, sm_e3, VectorStore('abl_nv'), FeedbackLoop(), schema_ddl),
    'ABL-NoRetry': C2CNoRetry(gemini, conn, sm_e3, VectorStore('abl_nr'), FeedbackLoop(), schema_ddl),
}

for sys_name, sys_fn in ablation_systems.items():
    print(f"\n▶ Running {sys_name}...")
    t_start = time.time()
    results = evaluate_system(sys_name, questions, rate_limited(sys_fn))
    elapsed = time.time() - t_start
    exp3_results[sys_name] = results
    exp3_metrics[sys_name] = compute_metrics(results)
    save_results(results, os.path.join(RESULTS_DIR, f'exp3_{sys_name}.json'))
    print(f"  EA: {exp3_metrics[sys_name]['EA']*100:.1f}%  RC: {exp3_metrics[sys_name]['RC']*100:.1f}%  ({elapsed:.0f}s)")

print(f"\nTABLE 5: Ablation Results")
print(f"{'Variant':<25} {'EA':>8} {'RC':>8} {'E1':>6} {'E3':>6} {'P50ms':>8}")
print("-"*65)
for s in ['B2-SchemaAware', 'ABL-Mono', 'ABL-NoPlanner', 'ABL-NoValidator', 'ABL-NoRetry', 'C2C-Full']:
    m = exp3_metrics.get(s, {})
    ed = m.get('error_distribution', {})
    print(f"{s:<25} {m.get('EA',0)*100:>7.1f}% {m.get('RC',0)*100:>7.1f}% {ed.get('E1',0)*100:>5.1f}% {ed.get('E3',0)*100:>5.1f}% {m.get('P50_ms',0):>7.0f}")

# ──────────────────────────────────────────────────────────
# EXPERIMENT 4: Heterogeneous Data (from E1 data)
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENT 4: HETEROGENEOUS DATA HANDLING")
print("="*70)

exp4_data = {}
print(f"{'System':<25} {'Struct EA':>10} {'Hetero EA':>10} {'Degrad':>10}")
print("-"*60)
for s in ['B1-Direct', 'B2-SchemaAware', 'C2C-Full']:
    tier_m = compute_metrics_by_tier(exp1_results[s])
    deg = compute_degradation(tier_m)
    exp4_data[s] = deg
    print(f"{s:<25} {deg['structured_EA']*100:>9.1f}% {deg['heterogeneous_EA']*100:>9.1f}% {deg['absolute_degradation_pp']:>8.1f}pp")

with open(os.path.join(RESULTS_DIR, 'exp4_degradation.json'), 'w') as f:
    json.dump(exp4_data, f, indent=2)

# ──────────────────────────────────────────────────────────
# EXPERIMENTS 5+6: Feedback Loop + Vector Grounding (200 queries)
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENTS 5+6: FEEDBACK LOOP + VECTOR GROUNDING (200 queries)")
print("="*70)

# Fresh systems
sm5_full = build_gold_semantic_model()
vs5_full = VectorStore(collection_name='exp5_full'); vs5_full.clear()
fl5_full = FeedbackLoop(alpha=0.15)
c2c_e5 = C2CPipeline(gemini, conn, sm5_full, vs5_full, fl5_full, schema_ddl)

sm5_nofb = build_gold_semantic_model(); sm5_nofb.freeze()
vs5_nofb = VectorStore(collection_name='exp5_nofb'); vs5_nofb.clear()
fl5_nofb = FeedbackLoop(alpha=0.0); fl5_nofb.disable()
c2c_e5_nofb = C2CNoFeedback(gemini, conn, sm5_nofb, vs5_nofb, fl5_nofb, schema_ddl)

sm5_novec = build_gold_semantic_model()
vs5_novec = VectorStore(collection_name='exp5_novec'); vs5_novec.clear()
fl5_novec = FeedbackLoop(alpha=0.15)
c2c_e5_novec = C2CNoVector(gemini, conn, sm5_novec, vs5_novec, fl5_novec, schema_ddl)

exp5_ck = {'C2C-Full': {}, 'ABL-NoFeedback': {}}
exp6_ck = {'C2C-Full': {}, 'ABL-NoVector': {}}

for batch in range(4):
    T = (batch + 1) * 50
    print(f"\n── Batch {batch+1}/4 (T={T}) ──")

    for name, fn in [('C2C-Full', c2c_e5), ('ABL-NoFeedback', c2c_e5_nofb), ('ABL-NoVector', c2c_e5_novec)]:
        print(f"  ▶ {name}...")
        res = evaluate_system(name, questions, rate_limited(fn))
        m = compute_metrics(res)
        ck = f'T{T}'

        if name in exp5_ck:
            exp5_ck[name][ck] = {'EA': m['EA'], 'E1_rate': m['error_distribution']['E1'], 'first_pass_EA': m['first_pass_EA']}
        if name in exp6_ck:
            vsize = vs5_full.size() if name == 'C2C-Full' else 0
            exp6_ck[name][ck] = {'first_pass_EA': m['first_pass_EA'], 'final_EA': m['EA'], 'E1_rate': m['error_distribution']['E1'], 'V_size': vsize}

        print(f"    EA={m['EA']*100:.1f}% E1={m['error_distribution']['E1']*100:.1f}%")

    # Feedback batch
    fb = c2c_e5.apply_feedback_batch()
    c2c_e5_novec.apply_feedback_batch()
    print(f"  ► Feedback: {fb.get('updates', 0)} updates")

with open(os.path.join(RESULTS_DIR, 'exp5_learning_curve.json'), 'w') as f:
    json.dump(exp5_ck, f, indent=2)
with open(os.path.join(RESULTS_DIR, 'exp6_vector_grounding.json'), 'w') as f:
    json.dump(exp6_ck, f, indent=2)

# Print E5 table
print(f"\n{'Checkpoint':<12} {'C2C EA':>10} {'NoFB EA':>10} {'C2C E1':>8} {'NoFB E1':>8}")
print("-"*55)
for t in ['T50', 'T100', 'T150', 'T200']:
    c = exp5_ck.get('C2C-Full', {}).get(t, {})
    n = exp5_ck.get('ABL-NoFeedback', {}).get(t, {})
    print(f"{t:<12} {c.get('EA',0)*100:>9.1f}% {n.get('EA',0)*100:>9.1f}% {c.get('E1_rate',0)*100:>7.1f}% {n.get('E1_rate',0)*100:>7.1f}%")

# ──────────────────────────────────────────────────────────
# EXPERIMENT 7: Error Taxonomy (from logs)
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENT 7: ERROR TAXONOMY DISTRIBUTION")
print("="*70)

print(f"{'System':<25} {'E1':>6} {'E2':>6} {'E3':>6} {'E4':>6} {'E5':>6} {'OK':>6}")
print("-"*70)
for s in ['B1-Direct', 'B2-SchemaAware', 'C2C-Full']:
    m = exp1_metrics[s]
    ed = m.get('error_distribution', {})
    print(f"{s:<25} {ed.get('E1',0)*100:>5.1f}% {ed.get('E2',0)*100:>5.1f}% {ed.get('E3',0)*100:>5.1f}% {ed.get('E4',0)*100:>5.1f}% {ed.get('E5',0)*100:>5.1f}% {ed.get('None',0)*100:>5.1f}%")
for s in ['ABL-Mono']:
    if s in exp3_metrics:
        m = exp3_metrics[s]
        ed = m.get('error_distribution', {})
        print(f"{s:<25} {ed.get('E1',0)*100:>5.1f}% {ed.get('E2',0)*100:>5.1f}% {ed.get('E3',0)*100:>5.1f}% {ed.get('E4',0)*100:>5.1f}% {ed.get('E5',0)*100:>5.1f}% {ed.get('None',0)*100:>5.1f}%")

# ──────────────────────────────────────────────────────────
# EXPERIMENT 8: Latency-Accuracy (from logs)
# ──────────────────────────────────────────────────────────
print("\n" + "="*70)
print("EXPERIMENT 8: LATENCY-ACCURACY TRADEOFF")
print("="*70)

b1_p50 = exp1_metrics['B1-Direct'].get('P50_ms', 0)
print(f"{'System':<25} {'P50 ms':>10} {'P95 ms':>10} {'EA':>8} {'vs B1':>10}")
print("-"*70)
for s in ['B1-Direct', 'B2-SchemaAware', 'C2C-Full']:
    m = exp1_metrics[s]
    print(f"{s:<25} {m.get('P50_ms',0):>9.0f} {m.get('P95_ms',0):>9.0f} {m['EA']*100:>7.1f}% {m.get('P50_ms',0)-b1_p50:>+9.0f}ms")
for s in ['ABL-NoRetry', 'ABL-NoValidator']:
    if s in exp3_metrics:
        m = exp3_metrics[s]
        print(f"{s:<25} {m.get('P50_ms',0):>9.0f} {m.get('P95_ms',0):>9.0f} {m['EA']*100:>7.1f}% {m.get('P50_ms',0)-b1_p50:>+9.0f}ms")

# ═══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("🎉 ALL 8 EXPERIMENTS COMPLETE")
print("="*70)
print(f"Results saved to: {RESULTS_DIR}")
print(f"Timestamp: {datetime.now().isoformat()}")

# Save master summary
master_summary = {
    'timestamp': datetime.now().isoformat(),
    'exp1_metrics': {k: {mk: mv for mk, mv in v.items() if isinstance(mv, (int, float, str))} for k, v in exp1_metrics.items()},
    'exp3_metrics': {k: {mk: mv for mk, mv in v.items() if isinstance(mv, (int, float, str))} for k, v in exp3_metrics.items()},
    'exp4_degradation': exp4_data,
    'exp5_learning': exp5_ck,
    'exp6_vector': exp6_ck,
    'synthesis_quality': synth_quality,
}
with open(os.path.join(RESULTS_DIR, 'master_summary.json'), 'w') as f:
    json.dump(master_summary, f, indent=2, default=str)
print("✅ Master summary saved")
