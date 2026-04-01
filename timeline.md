# Chaos2Clarity: Event Timeline

| Event | Action Taken | Outcome |
|---|---|---|
| **Moved to Local LLM** | Switched from cloud APIs to a unified `OllamaClient` using local Qwen 2.5 3B | Ensured a fair, cost-free, offline hardware benchmark |
| **Created Evaluation Harness** | Built `c2c_experiments.ipynb` to automatically track EA and RC across 50 queries | Enabled systematic scalability testing runs |
| **Notebook Execution Crash** | Replaced hardcoded paths with dynamic `PROJECT_ROOT` python script | Notebook now runs flawlessly from any root or sub-directory |
| **Pre-Run Syntax Validation** | Ran mock subprocess dry-runs over the entire 3,000 line notebook | Verified zero syntax errors before initiating the deployment loop |
| **JSON Hallucination Discovery** | Identified how the pipeline gracefully survives 3B JSON string-escape errors | Formalized "Zero-Knowledge Start Resilience" (Contribution C7) |
| **Missing Visualizations** | Wrote explicit Matplotlib blocks mapping Exp 1, 3, and 5 into Python charts | Automatically exported publication-ready Waterfall and Scatter figures |
| **Mapped Final Analytics** | Generated `exp_oup2.md` pulling true execution metrics mapped to document sections | Mapped metrics directly into Sections 8 and 9 of the paper |
