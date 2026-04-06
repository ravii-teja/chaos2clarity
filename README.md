
![c2c-banner](https://github.com/user-attachments/assets/e8e6a2cd-8b10-4ce2-ab5c-d1f49304eeb3)


# Chaos 2 Clarity (C2C)

**A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data**

Bankupalli Ravi Teja · Independent Research, Hyderabad, India

> arXiv: cs.AI
> 
> [Research Paper on Zenodo](https://zenodo.org/records/19414309)

---

## 🔬 Academic Significance
While most Text-to-SQL frameworks rely on massive, expensive cloud models (e.g., GPT-4o, Claude 3.5), C2C mathematically proves that a tightly constrained **3B parameter model** (Qwen 2.5 Coder) can achieve an Execution Accuracy of **87.5% ± 3.0% (peaking at 92.0%)** by aggressively utilizing a self-correcting semantic graph. This proves that **adaptive local orchestration infrastructure** is vastly superior to single-pass brute-force scaling, allowing edge deployments to process highly uncurated data with absolute data privacy.

---

## 🏗️ The C2C Architecture
This codebase implements four core autonomous mechanisms, natively isolated in the `/src` directory:

1. **Automated Semantic Layer** (`semantic_layer.py`): Constructs a living semantic mathematical graph ($\mathcal{S}$) mapping out implicit business logic.
2. **Agentic Query Orchestration** (`orchestration.py`, `prompts.py`): A formal 6-stage fallback pipeline: Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent.
3. **Vector-Grounded BI Reasoning** (`vector_store.py`): A localized persistent execution graph ($\mathcal{V}$) that grounds semantic generation in successful past SQL triples.
4. **Continuous Learning Loop** (`feedback_loop.py`): The core intelligence engine ($\delta$). Processes query execution successes ($f_{sql}$) and failures ($f_{qrm}$) to dynamically reconstruct broken semantic graphs in real-time.

---

## 🧪 Data Environment & Error Taxonomy
The framework does not rely on sanitized, pre-built academic datasets like Spider. It dynamically spins up **47 columns** across 3 highly uncurated sources:
*   **PostgreSQL (DuckDB)**: structured sales logs.
*   **Salesforce CRM**: unstructured SaaS extractions.
*   **Logistics CSV**: raw delivery event drops.

The architecture was built to explicitly target and suppress five distinct error classes native to edge-deployed LLMs:
*   **E1**: Schema Hallucination
*   **E2**: Aggregation Logic Failure
*   **E3**: Inferential Join Path Error
*   **E4**: Unstructured (RAG) Mismatch
*   **E5**: Cross-Source Failure

---

## 📊 Experimental Overview
The framework executes a rigorous 50-query simulation across the uncurated environment. We structured the methodology into strict phases:
1. **Baselines (Exp 1 & 2):** Tests the raw local LLM (`B1-Direct`) against the C2C framework to prove that multi-agent consensus structurally doubles **Result Correctness (RC)**.
2. **Ablation Constraints (Exp 3):** Systematically amputates the Planner, Validator, and Retry agents to measure exactly which architectural dependencies save the pipeline from failure.
3. **The Feedback Loop (Exp 5 & 6):** Forces the system through 200 sequential interactions to physically track how effectively it rewrites its own broken JSON semantic graphs after initial hallucinations.

![Feedback Loop Proof](./figures/exp5_learning_curve.png)

---

## 📈 Key Findings: What We've Learned
1. **The Planner Paradox on Small Models:** Removing the "Planner" agent (`ABL-NoPlanner`) paradoxically *improves* execution accuracy to 74%. We learned that forcing small 3B models to map out heavy JSON logical trees proactively often introduces fatal logical misdirection. Letting agents react dynamically yields structurally tighter query success rates in constrained regimes.
2. **"Zero-Knowledge" Start Resilience (Contribution C7):** Small models suffer from minor non-deterministic string escapes (e.g., `\n "entities"` crashes). C2C natively catches deeply nested parse exceptions, initializes a blank graph ($\mathcal{S} = \emptyset$), and autonomously rebuilds the entire operational context from scratch via the Feedback Loop across 200 queries.
3. **Immortality via Feedback:** The 3B model baseline flatlines rapidly against complex multi-table joins (frozen at 58.0%). C2C continuously mathematically suppresses E1 Hallucination rates from 38.0% down to a pristine 7.0%, achieving an **87.5% ± 3.0% EA** (peaking at 92.0%) entirely through historical vector-grounding over a 4-run ensemble.

---

## 💻 Hardware Environment & Offline Strategy
**Target Hardware:** The empirical benchmarks published in this research were natively executed on an **Apple MacBook Air M2 (8GB RAM)** utilizing system unified memory. 
> ⚠️ *Cross-Platform Compatibility:* Because the C2C architecture natively leverages Python `duckdb`, `chromadb`, and the `ollama` engine, **this notebook is fully cross-platform and will dynamically run on any OS** (Windows, Linux, or Intel Macs). However, the ~6-hour empirical execution time is specific to the M2 chip. Reproducing this on an 8GB RAM machine natively proves the architecture's incredible memory stability without Out-Of-Memory (OOM) crashes. If you replicate these experiments on devices with differing limits or thermal constraints, your execution duration will naturally vary.

**Why 100% Offline via Low-Compute Local LLMs?**
* **Data Sovereignty:** No database queries or schemas ever traverse a cloud boundary.
* **Architectural Supremacy:** It is academically trivial to achieve high accuracy by blindly throwing massive remote models at a problem. Forcing a tiny 3B model to perform at this tier proves the architectural scaffolding itself is mathematically sound.

---

## ⏱️ Execution & Time Estimates
The mathematical threshold for an academically viable paper requires **4 mathematically independent multi-runs** to calculate strict standard deviation error bars.

*   **P50 Single Run Block:** ~6 Hours
*   **Total Academic Deployment (4 Runs):** ~24 Continuous Execution Hours

| Pipeline Component | Queries Processed | Estimated P50 Runtime |
|---|---|---|
| Null Baselines (`B1`, `B2`, `B3`) | 50 (x3) | ~10 Minutes Total |
| Heavy `C2C-Full` Orchestrator | 50 | ~45 Minutes |
| Agent Structural Ablations | 50 (x4) | ~3 Hours Total |
| 200-Query Feedback Learning | 200 | ~2.5 Hours |

---

## 🚀 Quick Start & Multi-Run Automation

1. **Setup Virtual Environment:** Prevent global package pollution:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Install Ollama:** Download from ollama.com and run `ollama serve` natively.
3. **Pull the Edge Model:** Run `ollama pull qwen2.5-coder:3b`.
4. **Run the Master Node:** Open `notebooks/c2c_experiments.ipynb` using your `.venv` kernel. 
5. **Execute Pipeline (Run 1):** Select **"Run All"**. The notebook will execute the entire 6-hour evaluation block sequentially, dumping empirical `.json` logs into `/eval/results/`.
6. **The Native Mega Loop:** You do not need to write external Bash or Python orchestration scripts. The master notebook cell natively utilizes an intrinsic mega-loop to sequence all 4 benchmarking runs autonomously, completely trapping internal LLM data arrays. Just click "Run All" once, step away for 20+ hours, and all your academic standard deviations will stack perfectly into the `/runs/` directory!

---

## 📝 Citation
```bibtex
@article{chaos2clarity,
  title={Chaos 2 Clarity: A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data},
  author={Bankupalli, Ravi Teja},
  journal={arXiv preprint},
  year={2026}
}
```
