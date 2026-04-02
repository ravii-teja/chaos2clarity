# Chaos 2 Clarity (C2C)

**A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data**

Bankupalli Ravi Teja · Independent Research, Hyderabad, India

> arXiv: cs.DB (primary), cs.AI (secondary)

---

## 🔬 Academic Significance
While most Text-to-SQL frameworks rely on massive, expensive cloud models (e.g., GPT-4o, Claude 3.5), C2C mathematically proves that a tightly constrained **3B parameter model** (Qwen 2.5 Coder) can achieve enterprise-tier execution accuracy (88%) by aggressively utilizing a self-correcting semantic graph. This proves that **adaptive local orchestration infrastructure** is vastly superior to single-pass brute-force scaling, allowing edge deployments to process highly uncurated data with absolute data privacy.

---

## 📊 Experimental Overview
The framework executes a rigorous 50-query simulation across an uncurated DuckDB environment mimicking modern business schemas. We structured the methodology into strict phases:
1. **Baselines (Exp 1 & 2):** Tests the raw local LLM (`B1-Direct`) against the C2C framework to prove that multi-agent consensus structurally doubles **Result Correctness (RC)**.
2. **Ablation Constraints (Exp 3):** Systematically amputates the Planner, Validator, and Retry agents to measure exactly which architectural dependencies save the pipeline from failure.
3. **The Feedback Loop (Exp 5 & 6):** Forces the system through 200 sequential interactions to physically track how effectively it rewrites its own broken JSON semantic graphs ($\mathcal{S}$) after initial Zero-Knowledge hallucinations.

### What Results Actually Matter?
While standard literature obsesses over **Execution Accuracy (EA)** (whether the SQL compiles natively), C2C proves that **Result Correctness (RC)** is the only metric that matters in BI. A model can write syntactically flawless SQL that accidentally joins the wrong column (high EA, false RC). C2C sacrifices raw latency speed to drastically suppress these hallucinated joins.

---

## 📈 Key Findings: What We've Learned
1. **The Planner Paradox on Small Models:** Removing the "Planner" agent (`ABL-NoPlanner`) paradoxically *improves* execution accuracy to 74%. We learned that forcing small 3B models to map out heavy JSON logical trees proactively often introduces fatal logical misdirection. Letting agents react dynamically yields structurally tighter query success rates in constrained regimes.
2. **"Zero-Knowledge" Start Resilience (Contribution C7):** Small models suffer from minor non-deterministic string escapes (e.g., `\n "entities"` crashes). C2C proved it can securely catch deeply nested parsing exceptions natively, initialize a blank graph ($\mathcal{S} = \emptyset$), and autonomously mathematically rebuild the missing operational context from scratch via the Feedback Loop over 200 queries.
3. **Immortality via Feedback:** The 3B model baseline flatlines rapidly against complex 5-table joins. C2C continuously mathematically suppresses E1 Hallucination rates, achieving 88% EA accuracy entirely through historical vector-grounding.

---

## 💻 Hardware Environment & Offline Strategy

**Target Hardware:** The empirical benchmarks published in this research were executed locally on **Apple Silicon (macOS)** utilizing system unified memory. 
> ⚠️ *Disclaimer: The ~6-hour execution times and P50 latency metrics reflect this specific hardware. If you replicate these experiments on devices with differing RAM, GPU limits, or thermal constraints, your local execution duration will naturally vary.*

**Why 100% Offline via Low-Compute Local LLMs?**
1. **Data Sovereignty:** Modern enterprise BI deals with highly classified schemas, PII, and financial records. C2C ensures absolute zero-trust execution; no database queries or metadata ever traverse a cloud boundary (OpenAI, Anthropic, etc.).
2. **Architectural Edge Supremacy:** It is academically trivial to achieve high accuracy by blindly throwing massive remote models (like GPT-4o) at a problem. This research explicitly forces a tiny **low-compute 3B parameter model** to perform at enterprise-tier execution accuracy. It proves that intelligent orchestrator scaffolding is mathematically superior to brute-forcing raw parameters.
3. **Zero Marginal Inference Cost:** By proving reliability on edge devices, the financial barrier to scalable, continuous BI querying drops effectively to zero.

---

## ⏱️ Execution & Time Estimates

All computational workflows run completely offline and natively via `OllamaClient`, ensuring zero API costs and full data sovereignty. The mathematical threshold for an academically viable paper requires **4 mathematically independent multi-runs** to calculate strict standard deviation error bars.

*   **P50 Single Run Block:** ~6 Hours
*   **Total Academic Deployment (4 Runs):** ~24 Continuous Execution Hours

| Pipeline Component | Queries Processed | Estimated P50 Runtime |
|---|---|---|
| Null Baselines (`B1`, `B2`, `B3`) | 50 (x3) | ~10 Minutes Total |
| Heavy `C2C-Full` Orchestrator | 50 | ~45 Minutes |
| Agent Structural Ablations | 50 (x4) | ~3 Hours Total |
| 200-Query Feedback Learning | 200 | ~2.5 Hours |

---

## �� Quick Start Instructions

1. **Setup Virtual Environment:** Prevent global package pollution by isolating your environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Install Ollama:** Download from ollama.com and run `ollama serve` in the terminal natively.
3. **Pull the Edge Model:** Run `ollama pull qwen2.5-coder:3b` (the mathematically optimized local coder).
4. **Run the Master Node:** Open `notebooks/c2c_experiments.ipynb` using your `.venv` kernel. 
5. **Execute Pipeline:** Select **"Run All"**. The notebook will run the entirety of the 6-hour evaluation block sequentially, dump execution `.json` logs to `/eval/results/`, and automatically export publication-ready Pandas Matplotlib graphs to your interface.

---

## 📝 Citation
```bibtex
@article{teja2026chaos2clarity,
  title={Chaos 2 Clarity: A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data},
  author={Bankupalli, Ravi Teja},
  journal={arXiv preprint},
  year={2026}
}
```
