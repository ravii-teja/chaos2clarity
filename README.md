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

All experiments run on **Google Colab** for reproducibility:

| Notebook | Purpose | Est. Time |
|---|---|---|
| `00_data_generation.ipynb` | Generate 3-source retail data + 50-question suite | 30 min |
| `04_experiment_runner.ipynb` | Run all 8 experiments | 12-16 hrs |

### Quick Start

1. **Open in Colab:** Upload notebooks to Google Colab
2. **Set API Keys:** Add `GOOGLE_API_KEY` (Gemini 1.5 Pro) and `OPENAI_API_KEY` (GPT-4o) to Colab Secrets
3. **Run Notebook 00** first to generate the data environment
4. **Run Notebook 04** to execute all experiments

## 📁 Project Structure

```
chaos2clarity/
├── notebooks/
│   ├── 00_data_generation.ipynb      # Data + gold annotations
│   └── 04_experiment_runner.ipynb    # All 8 experiments
├── src/
│   ├── data_generator.py             # Synthetic 3-source retail data
│   ├── semantic_layer.py             # Mechanism I
│   ├── orchestration.py              # Mechanism II (pipeline + ablations)
│   ├── vector_store.py               # Mechanism III
│   ├── feedback_loop.py              # Mechanism IV
│   ├── baselines.py                  # B1, B2, B3 baselines
│   ├── eval_harness.py               # Evaluation infrastructure
│   ├── stats.py                      # Statistical tests
│   └── prompts.py                    # All prompt templates
├── eval/
│   ├── questions/                     # 50-question BI suite (JSON)
│   ├── gold_semantic_model.json
│   └── results/                       # Experiment outputs
├── data/                              # Generated data files
├── figures/                           # Publication figures
├── requirements.txt
└── README.md
```

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
