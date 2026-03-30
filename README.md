# Chaos 2 Clarity (C2C)

**A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data**

Bankupalli Ravi Teja · Independent Research, Hyderabad, India

> arXiv: cs.DB (primary), cs.AI (secondary)

---

## 🏗️ Architecture

C2C integrates four mechanisms:

1. **Automated Semantic Layer** — constructs a living semantic model from raw data
2. **Agentic Query Orchestration** — 6-stage pipeline: Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent
3. **Vector-Grounded BI Reasoning** — persists verified query–plan–result triples for grounding
4. **Feedback-Driven Continuous Learning Loop** — 4 signal types drive self-improvement

## 📊 Experiments

All computational experiments run completely natively using the **local open-source Ollama framework**, ensuring zero API cost, full data privacy, and end-to-end reproducibility.

| Notebook | Purpose | Est. Time |
|---|---|---|
| `c2c_experiments.ipynb` | The single master pipeline. Generates 3-source retail data, builds the test suite, initializes models, and runs all 8 experiments + plots. | ~6-10 hrs (varies by Mac RAM) |

### Quick Start

1. **Setup Virtual Environment:** Prevent global package pollution by isolating your environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Install Ollama:** Download from [ollama.com](https://ollama.com) and run `ollama serve` in the terminal.
3. **Pull the Model:** Run `ollama pull qwen2.5-coder:3b` (the mathematically optimized local coder).
4. **Run the Notebook:** Open `notebooks/c2c_experiments.ipynb` in Jupyter/VSCode using your new `.venv` kernel. 
5. **Execute:** Select **"Run All"**. The notebook will automatically interact with Ollama, run all 8 experiments, and generate all publication-ready figures to `/figures/`.

## 📁 Project Module Breakdown

The framework is highly modular. The following scripts inside the `src/` directory handle the core scientific mechanisms:

### 1. Data & Environment Setup
*   **`data_generator.py`**: Generates simulated uncurated enterprise data (Salesforce, CSVs, customer logs) and builds `retail.duckdb`.
*   **`llm_client.py`**: The unified local LLM engine connecting perfectly to Ollama without rate limits.

### 2. The Core Architecture (C2C Framework)
*   **`semantic_layer.py`**: Defines the "Gold" mathematical graph $\mathcal{S}$ and the Automated Synthesis Engine (Mechanism I) that dynamically maps schemas.
*   **`vector_store.py`**: A ChromaDB wrapper (Mechanism II) that persists verified past SQL executions for Few-Shot prompting.
*   **`feedback_loop.py`**: The self-improvement "brain" (Mechanism IV). Processes successes ($f_{sql}$) and failures ($f_{qrm}$) to iteratively update graph weights ($\kappa$).
*   **`prompts.py`**: Highly engineered prompt templates simulating a Planner, SQL Generator, and Validator.

### 3. Multi-Agent Pipelines & Baselines
*   **`orchestration.py`**: Defines the master `C2CPipeline` and systematic architecture ablations (`C2CNoPlanner`, `C2CNoValidator`, etc.) to prove necessity.
*   **`baselines.py`**: Defines static zero-shot LLMs ($\mathfrak{B}_1$ Direct LLM, $\mathfrak{B}_2$ Schema-Aware) used as null-hypothesis comparisons.

### 4. Evaluation & Science
*   **`eval_harness.py`**: The strict test engine. Validates EA and RC metrics dynamically against DuckDB.
*   **`stats.py`**: Calculates formal *p-values* (McNemar’s Test) proving statistical significance.

## 🧪 Data Environment

The prototype uses **47 columns** across 3 uncurated sources:

- **PostgreSQL** (DuckDB): orders, customers, products, sales_reps, returns (revenue stored as `line_value`)
- **Salesforce CRM**: accounts, opportunities (different naming: `email_address` not `email`)
- **Logistics CSV**: delivery events (status codes as integers, dates in MM/DD/YYYY)

No shared primary keys. Cross-source links only via implicit email matching.

## 📈 8 Experiments

| # | Name | Claim | Priority |
|---|---|---|---|
| E1 | Baseline vs. C2C | ≥ 25pp EA improvement | 🔴 MUST |
| E2 | Semantic Layer Impact | Mechanism I matters | 🔴 MUST |
| E3 | Agent Ablation | Each pipeline stage contributes | 🔴 MUST |
| E4 | Heterogeneous Data | Less degradation on complex data | 🔴 MUST |
| E5 | Feedback Loop | Self-improvement over time | 🔴 MUST |
| E6 | Vector Grounding | V reduces hallucination | 🔴 MUST |
| E7 | Error Taxonomy | E1-E5 taxonomy validation | 🟡 STRONG |
| E8 | Latency-Accuracy | Deployment cost-benefit | 🟡 STRONG |

## 📝 Citation

```bibtex
@article{teja2026chaos2clarity,
  title={Chaos 2 Clarity: A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data},
  author={Bankupalli, Ravi Teja},
  journal={arXiv preprint},
  year={2026}
}
```

## License

MIT
