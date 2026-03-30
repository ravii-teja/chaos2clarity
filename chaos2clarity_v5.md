# Chaos 2 Clarity: A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data

**Bankupalli Ravi Teja**  
Independent Research, Hyderabad, India  
`ravi@[your-real-email].com` · ORCID: `0000-0000-0000-0000` *(register at [orcid.org](https://orcid.org) before submission)*

> **arXiv target:** cs.DB (primary), cs.AI (secondary) · **Paper type:** System paper with experimental protocol

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Formal Problem Definition](#2-formal-problem-definition)
3. [Contributions](#3-contributions)
4. [Related Work](#4-related-work)
5. [System Architecture](#5-system-architecture)
6. [Prototype Implementation](#6-prototype-implementation)
7. [Error Taxonomy](#7-error-taxonomy)
8. [Evaluation Design](#8-evaluation-design)
9. [Full Evaluation Protocol](#9-full-evaluation-protocol)
10. [Discussion](#10-discussion)
11. [Conclusion](#11-conclusion)
- [References](#references)
- [Appendix A — Semantic Model Schema](#appendix-a-semantic-model-schema)
- [Appendix B — Agent Prompt Templates](#appendix-b-agent-prompt-templates)
- [Appendix C — BI Question Suite](#appendix-c-bi-question-suite--sample-questions)
- [Appendix D — System Comparison](#appendix-d-comparison-with-existing-systems)
- [Appendix E — Feedback Signal Taxonomy](#appendix-e-feedback-signal-taxonomy)
- [Appendix F — Hyperparameter Sensitivity](#appendix-f-hyperparameter-sensitivity)

---

## Abstract

Existing LLM-based business intelligence (BI) systems fail to generalize across heterogeneous enterprise data sources because they lack two properties essential in practice: *semantic grounding* at the data layer and *adaptive learning* at the query layer. Systems that assume a pre-built semantic model break on uncurated, multi-source environments; systems that learn do not ground their learning in the structure of the data.

We present **Chaos 2 Clarity** (C2C), a self-improving semantic orchestration framework that enables LLMs to generate reliable BI insights over heterogeneous, uncurated enterprise data through four tightly integrated mechanisms: **(i)** an **Automated Semantic Layer** that constructs a living semantic model—entities, relationships, metrics, and governance policies—directly from raw data sources without manual modeling, continuously refined through feedback; **(ii)** an **Agentic Query Orchestration Pipeline** implementing a decomposed Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent chain; **(iii)** a **Vector-Grounded BI Reasoning** subsystem that persists verified query–plan–result triples as grounding context, reducing repeated errors over time; and **(iv)** a **Feedback-Driven Continuous Learning Loop** ingesting SQL success/failure signals, user corrections, query-result mismatches, and insight usefulness ratings to drive prompt refinement, schema enrichment, embedding updates, and rule injection.

We formalize the problem, deploy a prototype over a realistic three-source retail environment (PostgreSQL, Salesforce CRM export, logistics CSV — 47 columns, zero pre-existing documentation), derive a five-class error taxonomy from prototype operation, and specify an eight-experiment evaluation protocol with explicit falsifiable predictions. Based on structural analysis of failure modes in uncurated BI settings, we hypothesize that C2C will improve execution accuracy by ≥ 25 percentage points over a direct LLM-to-SQL baseline and will enable cross-source queries that the baseline cannot execute.

---

<a id="1-introduction"></a>
## 1. Introduction

Large language models have enabled natural-language interfaces to data and BI, promising to democratize analytics and reduce reliance on specialist data teams [[1]](#ref-1) [[2]](#ref-2). Recent prototypes and commercial systems highlight LLM-powered agents that generate SQL from natural language, build dashboards, and automate analytical workflows [[3]](#ref-3) [[4]](#ref-4). These systems share a structural assumption: data curation has already been completed upstream, providing a central warehouse with consistent schemas and a manually defined semantic layer encoding business entities, metrics, and relationships.

In practice, many organizations cannot meet these prerequisites. Business-critical data is spread across multiple operational systems; exports and spreadsheets proliferate; SaaS tools hold key fragments of process and customer state; and documentation is sparse or outdated [[5]](#ref-5) [[6]](#ref-6). Benchmarks confirm the severity of this gap: while GPT-4-based agents achieve ≈ 86% execution accuracy on Spider 1.0 [[7]](#ref-7), performance drops to only 17–21% on Spider 2.0 [[8]](#ref-8)—which involves enterprise environments with > 3,000 columns, multiple SQL dialects, and cross-database workflows. This collapse traces to two failure modes that existing systems do not simultaneously address: *absent semantic grounding* (the system does not know what the data means across sources) and *no adaptive learning* (the system repeats the same errors without correction) [[9]](#ref-9) [[10]](#ref-10).

Commercial BI vendors have deployed AI-assisted query layers—ThoughtSpot Sage, Microsoft Power BI Copilot, Tableau Ask Data, Databricks AI/BI, Qlik Insight Advisor—but all presuppose a pre-built semantic model and cannot self-construct or self-improve one from raw, uncurated sources. Semantic layer tools such as dbt Semantic Layer, Looker LookML, Cube.dev, and AtScale offer structured metric registries but require significant manual modeling effort [[5]](#ref-5) [[20]](#ref-20) and provide no feedback-driven refinement. *The automated construction of a semantically grounded, continuously improving BI layer over raw, heterogeneous enterprise data remains an open problem.*

### The Core Insight

Reliable LLM-over-data systems require two properties that today's architectures treat as orthogonal: **semantic grounding** (knowing what data means across sources) and **adaptive learning** (improving from operational experience). C2C unifies these in a single architecture through: (a) automated semantic model construction from raw data, (b) decomposed query processing through a six-stage agent chain rather than a monolithic LLM call, (c) SQL generation grounded in a vector store of verified query patterns, and (d) continuous semantic model refinement via structured feedback signals from every query execution.

### Paper Type and Scope

This paper presents a *system paper with a formal experimental protocol*. We design, implement, and characterize C2C, a working prototype deployed over a realistic three-source retail enterprise scenario. The paper contributes: a formal problem definition, a production-oriented reference architecture with four named mechanisms, a running implementation, a five-class error taxonomy derived from prototype operation, and an eight-experiment evaluation protocol with falsifiable predictions. Full experimental results will be reported in an extended version of this work.

### Central Hypothesis

*C2C's self-improving semantic orchestration pipeline will improve execution accuracy on heterogeneous, multi-source BI workloads by ≥ 25 percentage points over a direct LLM-to-SQL baseline, and will enable cross-source queries that the baseline cannot execute at all.*

This hypothesis is operationalized in [Section 8](#8-evaluation-design) via eight experiments, each targeting a specific architectural component with a falsifiable prediction and explicit failure condition.

### Why C2C Is Distinct

**C2C vs. Text2SQL / NL2SQL systems** [[9]](#ref-9) [[7]](#ref-7) [[11]](#ref-11). These translate natural language to SQL over *a single, pre-specified, clean schema* and do not learn from failures—each query is an independent call. C2C synthesizes the schema and semantic model from raw, undocumented sources before any SQL is generated, and uses vector-grounded reasoning and feedback so a failure on query $q$ improves reliability for semantically similar future queries [[12]](#ref-12).

**C2C vs. LLM agent frameworks** [[13]](#ref-13) [[14]](#ref-14) [[15]](#ref-15). General-purpose frameworks (ReAct, AutoGen) provide tool-use and orchestration but do not solve data heterogeneity. A ReAct agent given disparate sources with no shared keys will hallucinate joins and repeat the failure on the next similar query [[5]](#ref-5). C2C's decomposed six-stage pipeline isolates each failure mode to a specific agent, enabling targeted retry and correction.

**C2C vs. dbt / Looker / Cube.dev semantic layers** [[5]](#ref-5) [[20]](#ref-20). These require engineers to write metric definitions, join paths, and entity mappings in YAML or LookML. C2C generates this layer automatically and improves it from feedback. dbt and Looker are potential *consumers* of C2C's synthesized output, not competitors.

**C2C vs. RAG systems** [[16]](#ref-16) [[17]](#ref-17). Standard RAG retrieves from unstructured document corpora. C2C's vector-grounded BI reasoning operates over verified query–plan–result triples, enabling retrieval of *verified execution patterns* rather than document fragments—targeting repeated query construction errors, not missing facts [[12]](#ref-12).

### Research Gap

To our knowledge, no existing production-oriented system simultaneously addresses: (a) automated semantic synthesis over uncurated heterogeneous sources, (b) decomposed multi-agent BI orchestration over the resulting semantic layer, (c) vector-grounded reasoning that reduces repeated query errors over time, and (d) feedback-driven continual self-improvement—all within a governance-aware, deployable architecture [[5]](#ref-5) [[10]](#ref-10).

---

<a id="2-formal-problem-definition"></a>
## 2. Formal Problem Definition

**Definition 1 (Data Source).** A *data source* $d_i$ is a tuple $d_i = \langle \tau_i, \sigma_i, \rho_i, \alpha_i \rangle$, where $\tau_i \in \{\text{rdbms}, \text{lake}, \text{file}, \text{api}, \text{document}\}$ is the source type, $\sigma_i$ is the (possibly partial or evolving) schema, $\rho_i$ is the statistical profile (cardinalities, value distributions, null rates), and $\alpha_i$ is the access control specification.

**Definition 2 (Heterogeneous Data Environment).** A *heterogeneous data environment* is a finite set $\mathcal{D} = \{d_1, d_2, \ldots, d_n\}$ of data sources. $\mathcal{D}$ is *uncurated* if: (a) no unified schema or naming convention exists across sources; (b) no formal semantic catalog or metric registry has been manually defined; and (c) documentation is absent or incomplete for ≥ 50% of entities.

**Definition 3 (Semantic Model).** A *semantic model* $\mathcal{S}$ is a typed labeled graph $\mathcal{S} = \langle \mathcal{E}, \mathcal{M}, \mathcal{R}, \mathcal{P}, \kappa \rangle$, where:
- $\mathcal{E} = \{e_1,\ldots,e_p\}$ is a set of *business entities*, each with aliases and source mappings;
- $\mathcal{M} = \{m_1,\ldots,m_q\}$ is a set of *metrics*, each defined by an aggregation formula $\phi_j : \text{Tuples}(\mathcal{D}) \to \mathbb{R}$ and a unit of measurement;
- $\mathcal{R} \subseteq (\mathcal{E} \cup \mathcal{M}) \times \mathcal{L} \times (\mathcal{E} \cup \mathcal{M})$ is a set of typed, labeled relationships;
- $\mathcal{P} = \{p_1,\ldots,p_r\}$ is a set of *governance policies*;
- $\kappa : \mathcal{E} \cup \mathcal{M} \cup \mathcal{R} \to [0,1]$ is a *confidence function* over all inferred mappings.

**Definition 4 (Semantic Synthesis).** *Semantic synthesis* is the function $f_\text{synth} : \mathcal{D} \to \mathcal{S}$ that automatically constructs a semantic model from a heterogeneous data environment with minimal human input. This problem subsumes schema matching [[18]](#ref-18), which is NP-hard in the general case [[19]](#ref-19); C2C employs LLM-based heuristic approximations with confidence scoring.

**Definition 5 (Feedback Refinement).** *Feedback refinement* is a function $\delta : \mathcal{S} \times \mathcal{F} \to \mathcal{S}$ that updates the semantic model given feedback events $f \in \mathcal{F}$. The feedback space $\mathcal{F}$ includes four signal types: SQL execution outcomes ($f_\text{sql}$), user corrections ($f_\text{usr}$), query-result mismatch signals ($f_\text{qrm}$), and insight usefulness ratings ($f_\text{ins}$). The *self-improving* property holds when $\mathcal{U}(\delta(\mathcal{S}, f), f_\text{bi}) \geq \mathcal{U}(\mathcal{S}, f_\text{bi})$ in expectation for any non-empty feedback batch.

**Definition 6 (Vector Knowledge Store).** A *vector knowledge store* $\mathcal{V}$ is a persistent store of tuples $(q_\text{norm}, \pi_\text{verified}, r_\text{gold}, \text{emb}(q_\text{norm}))$ representing normalized queries, verified execution plans, gold results, and query embeddings. It supports $k$-nearest-neighbor retrieval: $\text{Retrieve}(q, k) : \mathcal{Q} \to (\mathcal{V})^k$, returning the $k$ most semantically similar verified query–plan pairs as grounding context for new query generation. $\mathcal{V}$ is a first-class argument to $f_\text{bi}$—not a result cache—because it conditions query *generation*, not query *lookup*.

**Definition 7 (BI Query and Answer).** The *AI-over-BI function* is $f_\text{bi} : \mathcal{Q} \times \mathcal{S} \times \mathcal{D} \times \mathcal{V} \to \mathcal{A}$, where a *BI answer* $a \in \mathcal{A}$ comprises a result set $r$, provenance trace $\pi$, and natural-language explanation $\xi$.

**Problem 1 (Chaos 2 Clarity).** Given an uncurated heterogeneous data environment $\mathcal{D}$, construct $\mathcal{S} = f_\text{synth}(\mathcal{D})$ automatically, build an initial vector store $\mathcal{V}_0$, then deploy $f_\text{bi}$ over $\mathcal{S}$, $\mathcal{D}$, and $\mathcal{V}$ to answer BI queries with measurable correctness, latency, and governance compliance—while continuously improving $\mathcal{S}$ and $\mathcal{V}$ via feedback $\delta$ such that query quality improves over the deployment lifetime.

### Optimization Objective

<a id="equation-1"></a>

$$\mathcal{U}(\mathcal{S}, \mathcal{V}, f_\text{bi}) = \underbrace{\frac{1}{m}\sum_{j=1}^{m} \mathbb{1}\bigl[\text{RC}(f_\text{bi}(q_j,\mathcal{S},\mathcal{D},\mathcal{V}),\, a^*_j)\bigr]}_{\text{result correctness}} - \lambda_1 \cdot \bar{L} - \lambda_2 \cdot \bar{V} \tag{Eq. 1}$$

where $\text{RC}(\cdot)$ is result correctness, $\bar{L}$ is mean end-to-end latency, $\bar{V}$ is the governance violation rate, and $\lambda_1, \lambda_2 \geq 0$ are operator-specified weights.

### Formal Properties

**Proposition 1 (Semantic Consistency).** The orchestration pipeline $f_\text{bi}$ is *semantically consistent* with $\mathcal{S}$ if every entity reference in the generated SQL is grounded in a node $e \in \mathcal{E}$ with $\kappa(e) \geq \theta_\text{exec}$. The validator $f_\text{vrf}$ enforces this by rejecting any plan referencing unmapped entities, bounding silent failures to the residual error of $\kappa$ estimation rather than allowing arbitrary hallucinated joins. *Proof:* by construction of $f_\text{vrf}$—any plan failing the entity grounding check is rejected before execution, so ungrounded plans cannot produce results. $\square$

**Proposition 2 (Confidence Convergence).** Under the feedback update rule ([Equation 2](#equation-2)), for any element $x \in \mathcal{E} \cup \mathcal{M} \cup \mathcal{R}$ and any unbiased sequence of feedback events drawn from a stationary process with true confirmation rate $p_x$, the expected confidence converges: $\mathbb{E}[\kappa_t(x)] \to p_x$ as $t \to \infty$. The empirical effect of $\mathcal{V}$ growth on retrieval precision for similar future queries is measured in [Experiment 6](#87-experiment-6-vector-grounding-impact).

### Research Questions

- **RQ1 (Semantic Synthesis Quality):** How effectively does automated semantic synthesis recover $\mathcal{S}$ from $\mathcal{D}$, measured by entity/metric coverage and mapping F1, relative to a manually curated gold model?
- **RQ2 (Semantic Layer Impact):** Does the automated semantic layer produce measurably fewer join errors, aggregation errors, and hallucinated column references compared to operating on raw schemas?
- **RQ3 (Orchestration):** Does the decomposed six-stage pipeline yield better execution accuracy and error recoverability than monolithic LLM baselines and reduced-stage variants?
- **RQ4 (Heterogeneous Data):** Does C2C degrade less than baselines as data complexity increases from single-source structured to multi-source and semi-structured?
- **RQ5 (Self-Improvement):** Do the vector-grounded reasoning and feedback mechanisms produce measurable quality improvements over successive query batches, and at what rate?
- **RQ6 (Latency–Accuracy):** What is the explicit latency cost of orchestration overhead, and does the accuracy gain justify it across deployment scenarios?

---

<a id="3-contributions"></a>
## 3. Contributions

To our knowledge, C2C is the first system to make the following six contributions in a single deployable architecture:

- **C1 — Formal self-improving semantic orchestration framework.** A formal definition of the semantic synthesis and feedback refinement problems, unifying automated $\mathcal{S}$ construction from uncurated $\mathcal{D}$ with a continuous learning loop $\delta$ updating $\mathcal{S}$ and $\mathcal{V}$ from four structured feedback signal types. This extends LLM-assisted metadata enrichment [[20]](#ref-20) [[21]](#ref-21) and schema matching [[18]](#ref-18) to a self-improving BI pipeline.

- **C2 — Decomposed six-stage agentic orchestration pipeline.** A production-oriented Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent pipeline isolating each failure mode to a specific stage, with typed agent functions and retry semantics ([Algorithm 1](#algorithm-1)).

- **C3 — Vector-Grounded BI Reasoning.** A persistent vector knowledge store $\mathcal{V}$ of verified query–plan–result triples that grounds SQL generation in semantically similar successful past executions, reducing repeated hallucination errors without model retraining.

- **C4 — Feedback-Driven Continuous Learning Loop.** A structured four-signal feedback mechanism driving prompt refinement, schema enrichment, embedding updates, and rule injection. C2C is, to our knowledge, the first BI system to formally specify all four feedback signal types and their corresponding update targets in a single integrated loop.

- **C5 — Working prototype and error taxonomy.** A deployed prototype over a realistic three-source retail enterprise environment and a five-class error taxonomy (E1–E5) derived from prototype operation, grounding the evaluation design ([Section 7](#7-error-taxonomy)).

- **C6 — Eight-experiment evaluation protocol.** A structured evaluation framework with eight experiments mapped directly to the four architectural claims, with explicit falsifiable predictions, ablation variants, and dataset specifications ([Section 8](#8-evaluation-design)).

---

<a id="4-related-work"></a>
## 4. Related Work

<a id="41-llm-based-text-to-sql-and-nl2sql"></a>
### 4.1 LLM-Based Text-to-SQL and NL2SQL

Shi et al. [[9]](#ref-9) survey LLM-based text-to-SQL methods. Spider 1.0 [[7]](#ref-7) and BIRD [[11]](#ref-11) are standard benchmarks, with recent work achieving ≈ 86% and ≈ 72% execution accuracy respectively—both assuming fully curated, well-documented single-database schemas. Spider 2.0 [[8]](#ref-8) introduces enterprise-level complexity where best models achieve only 17–21%, attributable to schema heterogeneity [[8]](#ref-8). DAIL-SQL [[12]](#ref-12) achieves competitive performance through efficient prompt selection but operates on single, structured sources with no cross-query learning. C2C targets the pre-NL2SQL step of synthesizing the semantic model from raw data, and adds the cross-query learning layer that single-shot text-to-SQL systems lack entirely.

<a id="42-commercial-ai-over-bi-systems"></a>
### 4.2 Commercial AI-over-BI Systems

ThoughtSpot Sage, Microsoft Power BI Copilot, Tableau Ask Data, Databricks AI/BI, and Qlik Insight Advisor all require a pre-constructed semantic model and provide no mechanism for self-construction or feedback-driven self-improvement. C2C uniquely automates both construction and continuous refinement.

<a id="43-semantic-layer-tools"></a>
### 4.3 Semantic Layer Tools

dbt Semantic Layer, Looker LookML, Cube.dev, and AtScale require substantial manual modeling effort [[5]](#ref-5) [[20]](#ref-20) and are static: they do not update from query feedback. Singh et al. [[20]](#ref-20) document that manual semantic model construction for a mid-sized enterprise data environment requires weeks to months of engineering effort. C2C treats these as potential *consumers* of its synthesized output.

<a id="44-llm-agents-for-data-analytics"></a>
### 4.4 LLM Agents for Data Analytics

InsightPilot [[22]](#ref-22) deploys LLM agents for automated data exploration but assumes a pre-structured environment and does not learn from failures. Cheng et al. [[23]](#ref-23) evaluate GPT-4 as a data analyst, finding it limited on schema inference and multi-source reasoning. Rahman et al. [[3]](#ref-3) and Chen et al. [[10]](#ref-10) survey LLM data science agents, identifying the absence of adaptive learning and cross-source reasoning as key gaps. Zhu et al. [[5]](#ref-5) formalize requirements for agents over heterogeneous systems, identifying semantic alignment and operational feedback as unsolved problems.

<a id="45-automated-metadata-discovery-and-data-cataloging"></a>
### 4.5 Automated Metadata Discovery and Data Cataloging

Singh et al. [[20]](#ref-20) demonstrate LLM-based metadata enrichment achieving > 80% ROUGE-1 F1 and ≈ 90% acceptance by data stewards. LEDD [[21]](#ref-21) employs LLMs for hierarchical semantic catalog generation over data lakes. LLMDapCAT [[24]](#ref-24) applies LLM+RAG for automated metadata extraction. SCHEMORA [[18]](#ref-18) achieves state-of-the-art cross-schema alignment. These works address *construction* of semantic metadata but do not couple it to a query execution pipeline or feedback loop.

<a id="46-multi-agent-orchestration"></a>
### 4.6 Multi-Agent Orchestration

Adimulam et al. [[25]](#ref-25) survey multi-agent LLM architectures. AutoGen [[13]](#ref-13) provides a widely adopted conversation framework. Arunkumar et al. [[15]](#ref-15) examine memory backends and tool integration for agentic AI. AgentArch [[26]](#ref-26) benchmarks enterprise agent architectures, with best models achieving only 35.3% on complex multi-step tasks—motivating C2C's decomposed pipeline design. ReAct [[14]](#ref-14) and Plan-then-Execute [[27]](#ref-27) are foundational primitives that C2C extends with SQL-oriented stages and cross-stage feedback routing.

<a id="47-rag-and-vector-grounded-reasoning"></a>
### 4.7 RAG and Vector-Grounded Reasoning

Lewis et al. [[16]](#ref-16) introduce RAG for knowledge-intensive NLP. Gao et al. [[17]](#ref-17) survey advanced RAG architectures. Cheerla [[28]](#ref-28) proposes hybrid retrieval for structured enterprise data. RAGAS [[29]](#ref-29) provides automated RAG evaluation. Pan et al. [[30]](#ref-30) demonstrate table question answering via RAG. C2C's vector-grounded BI reasoning extends this by operating over verified execution patterns (query–plan–result triples) rather than document fragments—retrieving *how to query* rather than *what to return*.

---

<a id="5-system-architecture"></a>
## 5. System Architecture

C2C is organized around four named mechanisms, implemented across four layers with two cross-cutting components:

| Mechanism | Primary Layer | Cross-Cutting Role |
|---|---|---|
| Automated Semantic Layer | 𝓛₂ (Semantic Synthesis) | Updated continuously by feedback loop |
| Agentic Query Orchestration | 𝓛₃ (AI-over-BI) | Emits signals to feedback loop |
| Vector-Grounded BI Reasoning | Cross-cutting ($\mathcal{V}$) | Consulted by SQL Generator stage |
| Feedback-Driven Learning Loop | Cross-cutting ($\delta$) | Updates 𝓛₂ and $\mathcal{V}$ |

```
┌──────────────────────────────────────────────────────────────────────┐
│               Experience & Integration Layer (L4)                    │
│        Conversational UI  ·  BI Tool Integration Endpoints           │
└──────────────────────────┬───────────────────────────────────────────┘
          queries ↓        │ ↑ answers
┌──────────────────────────▼───────────────────────────────────────────┐  ┌───────────────────────────┐
│           AI-over-BI Orchestration Layer (L3)                        │  │  Cross-Cutting            │
│  Planner → Retriever → SQL Generator → Validator → Executor          │◄►│  ─────────────────────    │
│  → Insight Agent                                                      │  │  Vector Store  𝒱         │
└──────────────────────────┬───────────────────────────────────────────┘  │  (query grounding)        │
      semantic ops ↓       │ ↑ 𝒮                                          │                           │
┌──────────────────────────▼───────────────────────────────────────────┐  │  Feedback Loop  δ         │
│           Semantic Synthesis Layer (L2)  [Mechanism I]               │◄►│  4 signal types →         │
│  Asset Discovery · Concept Inference · Semantic Graph                │  │  prompt refinement        │
│  · Human-in-Loop Refinement                                          │  │  schema enrichment        │
└──────────────────────────┬───────────────────────────────────────────┘  │  embedding updates        │
       profiles ↓          │ ↑ raw data                                   │  rule injection           │
┌──────────────────────────▼───────────────────────────────────────────┐  └───────────────────────────┘
│           Data & Connectivity Layer (L1)                             │
│  RDBMS · Data Lakes · CSV/Excel · SaaS APIs · Document Stores        │
└──────────────────────────────────────────────────────────────────────┘
```

<a id="figure-1"></a>*Figure 1. C2C four-layer architecture. $\mathcal{V}$ and $\delta$ are first-class architectural components, not auxiliary optimizations.*

<a id="51-data-and-connectivity-layer"></a>
### 5.1 Data and Connectivity Layer (𝓛₁)

𝓛₁ exposes a unified discovery interface over $\mathcal{D}$, populating a lightweight catalog with schema snapshots $\sigma_i$, statistical profiles $\rho_i$, lineage hints, and access controls $\alpha_i$. Data is never centralized; 𝓛₁ federates access. Schema refresh events trigger confidence re-evaluation in 𝓛₂ via $\delta$.

<a id="52-mechanism-i-automated-semantic-layer"></a>
### 5.2 Mechanism I: Automated Semantic Layer (𝓛₂)

𝓛₂ implements $f_\text{synth} : \mathcal{D} \to \mathcal{S}$—building its own semantic model from raw data with no manual modeling required, keeping it current through continuous feedback.

```
Asset Discovery ──► Concept Inference ──► Semantic Graph
 (profile ρᵢ,        (align to ℰ, ℳ, ℛ)    (build 𝒮 + κ)
  infer σᵢ)                │                      │
                   ◄── Human-in-Loop ◄─────────────┘
                       (low-κ review)
                           │
                   ◄── Feedback Loop δ ◄── [f_sql, f_usr, f_qrm, f_ins]
```

<a id="figure-2"></a>*Figure 2. Automated semantic layer construction and continuous refinement.*

**Asset discovery and profiling.** For each $d_i \in \mathcal{D}$, an LLM-assisted agent infers column types, candidate keys, potential foreign-key relationships, and computes statistical profile $\rho_i$, following the approach demonstrated by Singh et al. [[20]](#ref-20) and extended by SCHEMORA [[18]](#ref-18).

**Concept and metric inference.** An LLM agent proposes entity mappings, metric definitions with formulae $\phi_j$, and synonym sets, assigning initial confidence $\kappa_0 \in [0,1]$ via embedding similarity and column naming heuristics.

**Semantic graph construction.** Inferred nodes and edges are materialized into typed graph $\mathcal{S}$ with provenance annotations, stored in Neo4j 5.x.

**Human-in-the-loop refinement.** Data owners review mappings with $\kappa < \theta_\text{review} = 0.75$. Human review is *optional*; C2C operates at whatever confidence the automated pipeline achieves. The HITL pattern follows practices in Singh et al. [[20]](#ref-20).

**Continuous self-improvement.** The semantic layer receives updates from all four feedback signal types ([Section 5.6](#56-mechanism-iv-feedback-driven-learning-loop))—it is a *living artifact* that improves with operational use.

<a id="53-mechanism-ii-agentic-orchestration"></a>
### 5.3 Mechanism II: Agentic Query Orchestration Pipeline (𝓛₃)

𝓛₃ implements $f_\text{bi}$ via a **decomposed six-stage pipeline**. The motivation for decomposition over monolithic LLM calls is empirically grounded: AgentArch [[26]](#ref-26) demonstrates that single-LLM-call approaches achieve only 35.3% on complex enterprise tasks. The six stages are formalized by the following typed functions. The **Retriever** ($f_\text{ret}$, Stage 2) and **Insight Agent** ($f_\text{ins}$, Stage 6) are new relative to standard five-agent designs: the Retriever introduces vector-grounded reasoning as a first-class pipeline stage; the Insight Agent extends narration to emit structured feedback signals.

<a id="table-agents"></a>

| Stage | Agent | Function | Signature |
|---|---|---|---|
| 1 | Planner | $f_\text{pln}$ | $\mathcal{Q} \times \mathcal{S} \times \mathcal{P} \to \mathcal{T} \times \mathcal{I} \times \Pi$ |
| 2 | Retriever | $f_\text{ret}$ | $\mathcal{Q} \times \mathcal{V} \to (\mathcal{V})^k$ |
| 3 | SQL Generator | $f_\text{qry}$ | $\Pi \times \mathcal{D} \times (\mathcal{V})^k \to \text{SQL}^* \cup \text{RAG}^*$ |
| 4 | Validator | $f_\text{vrf}$ | $(\text{SQL}^* \cup \text{RAG}^*) \times \mathcal{S} \times \mathcal{P} \to \{0,1\} \times (\cdot)_\text{safe}$ |
| 5 | Executor | $f_\text{exe}$ | $(\cdot)_\text{safe} \times \mathcal{D} \to r \cup \text{Error}$ |
| 6 | Insight Agent | $f_\text{ins}$ | $r \times \pi \to \xi \times \mathcal{F}$ |

The Planner employs a Plan-then-Execute strategy [[27]](#ref-27): a full plan $\pi \in \Pi$ is committed before execution, enabling budget control and policy pre-checking. Chain-of-thought prompting [[31]](#ref-31) is applied at planning and query generation stages.

<a id="54-orchestration-algorithm"></a>
### 5.4 Orchestration Algorithm

<a id="algorithm-1"></a>
**Algorithm 1: C2C Orchestration Pipeline**

```
Input:  Query q ∈ 𝒬, semantic model 𝒮, sources 𝒟,
        vector store 𝒱, policies 𝒫, max retries K
Output: Answer a ∈ 𝒜 or governed failure report

1.  (t, ℐ, π) ← f_pln(q, 𝒮, 𝒫)              // Planner: classify intent + build plan
2.  G ← f_ret(q, 𝒱, k=5)                     // Retriever: fetch k verified grounding plans
3.  k_retry ← 0;  error_ctx ← ∅
4.  while k_retry ≤ K do
5.      SQL* ← f_qry(π, 𝒟, G, error_ctx)     // SQL Generator: conditioned on plan + G
6.      (v, SQL*_safe) ← f_vrf(SQL*, 𝒮, 𝒫)  // Validator: 𝒮 consistency + policy check
7.      if v = 0 then
8.          emit f_sql(failure, policy_violation) → δ
9.          return governed failure: policy violation
10.     end if
11.     r ← f_exe(SQL*_safe, 𝒟)              // Executor: run in-situ
12.     if r = Success then
13.         ξ, F ← f_ins(r, π)               // Insight Agent: narrate + emit feedback
14.         write (q_norm, π, r) → 𝒱         // persist verified execution
15.         emit F → δ                        // route feedback to learning loop
16.         return a = (r, π, ξ)
17.     else
18.         error_ctx ← ExtractError(r)
19.         emit f_sql(failure, error_ctx) → δ // failure also feeds learning loop
20.         k_retry ← k_retry + 1
21.     end if
22. end while
23. return governed failure: max retries exceeded
```

**Key differentiators from single-pass Text2SQL:** (1) Line 2 grounds SQL generation in $k=5$ verified plans before generation begins. (2) Lines 13–15 write every success to $\mathcal{V}$ and route feedback to $\delta$—the system improves with every query. (3) Lines 8 and 19 route failure signals to $\delta$—the system learns from failures as well as successes. No existing BI system surveyed implements this bidirectional failure routing [[5]](#ref-5) [[10]](#ref-10).

<a id="55-mechanism-iii-vector-grounded-reasoning"></a>
### 5.5 Mechanism III: Vector-Grounded BI Reasoning

$\mathcal{V}$ is architecturally distinct from the result cache ([Section 5.8](#58-query-result-cache)). The cache returns *results* for repeated identical queries; $\mathcal{V}$ returns *execution patterns* for semantically similar but structurally distinct queries—it improves *query construction*, not query latency.

**Store structure:** $v_i = (q_\text{norm},\; \pi_\text{verified},\; \text{SQL}^*_\text{verified},\; r_\text{gold},\; \kappa_\text{entry},\; \text{emb}(q_\text{norm}))$

where $\kappa_\text{entry} \in [0,1]$ decays if subsequent similar queries produce contradictory results. The consistent-hallucination suppression mechanism is consistent with findings in DAIL-SQL [[12]](#ref-12): once a correct execution establishes `line_value` as the mapping for "revenue," this pattern enters $\mathcal{V}$ and grounds all future similar queries without rule engineering.

**Store management.** $\mathcal{V}$ is bounded at $|\mathcal{V}| \leq N_\text{max}$; entries with $\kappa_\text{entry} < \theta_\text{prune}$ are evicted when capacity is reached. On schema change detection, affected entries have $\kappa_\text{entry}$ set to 0 and are flagged for re-validation.

<a id="56-mechanism-iv-feedback-driven-learning-loop"></a>
### 5.6 Mechanism IV: Feedback-Driven Continuous Learning Loop

The feedback loop $\delta : \mathcal{S} \times \mathcal{F} \to \mathcal{S}$ makes C2C *self-improving* (full specification in [Appendix E](#appendix-e-feedback-signal-taxonomy)):

```
Signal Source          Update Targets
──────────────         ───────────────────────────────────────
f_sql  (SQL outcome) → schema enrichment, 𝒱 entry κ, rule injection
f_usr  (correction)  → schema enrichment, prompt refinement, synonym embeddings
f_qrm  (mismatch)    → prompt refinement (aggregation), schema (metric formulas)
f_ins  (usefulness)  → prompt refinement (narrator), 𝒱 κ_entry decay
```

<a id="figure-4"></a>*Figure 4. Four-signal feedback routing to four update target classes.*

<a id="equation-2"></a>
**Confidence update rule.** For $x \in \mathcal{E} \cup \mathcal{M} \cup \mathcal{R}$:

$$\kappa_{t+1}(x) = (1-\alpha)\,\kappa_t(x) + \alpha\,\mathbb{1}[f \text{ confirms } x] \tag{Eq. 2}$$

with learning rate $\alpha \in (0,1)$. Under a stationary unbiased confirmation process, $\mathbb{E}[\kappa_t(x)] \to p_x$ as $t \to \infty$ (Proposition 2). The prototype uses $\alpha = 0.15$, selected via grid search over $\{0.05, 0.10, 0.15, 0.20, 0.30\}$ on a 20-query held-out validation set; sensitivity analysis is reported in [Appendix F](#appendix-f-hyperparameter-sensitivity).

**Prompt refinement.** Failure patterns accumulate in store $\Phi$. When $|\Phi_\text{type}| \geq \theta_\text{batch} = 10$ for a given error class, a refinement step generates new few-shot examples targeting that class and injects them into the relevant agent's system prompt—a deployment-safe alternative to fine-tuning [[27]](#ref-27).

**Schema enrichment.** Repeated E1 failures on a specific column trigger LLM-assisted re-profiling. Proposals with $\kappa_0 \geq 0.85$ are auto-applied; lower-confidence proposals are queued for review.

**Embedding updates.** User corrections establishing new synonyms trigger re-embedding of affected $\mathcal{V}$ entries and $\mathcal{S}$ nodes.

**Rule injection.** Repeated policy violations of the same type are promoted to persistent rules in $\mathcal{P}$, reducing LLM validator reliance for known patterns.

<a id="57-experience-layer"></a>
### 5.7 Experience and Integration Layer (𝓛₄)

𝓛₄ exposes C2C via: (i) a conversational interface with multi-turn analytical dialogue and visualization rendering; and (ii) REST and semantic-layer APIs compatible with dbt Semantic Layer, Looker LookML, and generic JDBC/ODBC. Each user turn generates $f_\text{usr}$ and $f_\text{ins}$ signals routed to $\delta$.

<a id="58-query-result-cache"></a>
### 5.8 Query Result Cache

The result cache is a latency optimization layer distinct from $\mathcal{V}$. Two queries are *cache-equivalent* if $\cos(\text{emb}(q), \text{emb}(q')) \geq \lambda_\text{cache}$ and their resolved source sets are identical. Cache hit rate $H$ and latency reduction $\Delta L$ are tracked as system performance metrics. **The cache returns results; $\mathcal{V}$ returns patterns. A cache hit bypasses the entire pipeline; a $\mathcal{V}$ hit conditions SQL generation for a similar-but-distinct query. They are architecturally independent.**

---

<a id="6-prototype-implementation"></a>
## 6. Prototype Implementation

| Component | Technology | C2C Mechanism |
|---|---|---|
| Backend | Python 3.11 / [FastAPI](https://fastapi.tiangolo.com/), SQLAlchemy 2.0 async, Alembic | Infrastructure |
| LLM orchestration | [LangChain](https://www.langchain.com/) (agents), [LlamaIndex](https://www.llamaindex.ai/) (RAG pipelines) | Mechanisms II + III |
| LLM backbone | Gemini 1.5 Pro (primary), GPT-4o (secondary / ablation) | All mechanisms |
| Semantic graph | [Neo4j 5.x](https://neo4j.com/) | Mechanism I |
| Vector store | [Vertex AI Matching Engine](https://cloud.google.com/vertex-ai/docs/matching-engine/overview) | Mechanism III |
| Feedback store | PostgreSQL (event log + $\Phi$ failure patterns) | Mechanism IV |
| Cache | [Redis 7](https://redis.io/) (intent-normalized keys, configurable TTL) | Cache layer |
| Infrastructure | GCP: Cloud Run, Cloud SQL, Artifact Registry | Infrastructure |
| Frontend | Next.js 14 with Backend-for-Frontend pattern | 𝓛₄ |
| Data connectors | PostgreSQL, BigQuery, CSV/Parquet ([DuckDB](https://duckdb.org/)), Salesforce REST, PDF/DOCX ([unstructured.io](https://unstructured.io/)) | 𝓛₁ |

**Prototype deployment.** Three uncurated retail enterprise sources:
- PostgreSQL OLTP database — sales and order records, 14 tables;
- Salesforce CRM API export — customer accounts and active deals;
- CSV flat files — third-party logistics delivery events and status codes.

47 columns total, inconsistent naming conventions, no shared primary keys, zero pre-existing documentation. The column naming `line_value` (for "revenue") and the absence of any join key between Salesforce and logistics exports represent the canonical failure modes that motivate C2C's design.

**Deployment model.** C2C deploys as a sidecar with zero ETL overhead. $\mathcal{S}$ is built once and continuously maintained via $\delta$. $\mathcal{V}$ starts empty and is populated through operational use. Queries execute in-situ.

---

<a id="7-error-taxonomy"></a>
## 7. Error Taxonomy

The five error classes below were derived from failure modes observed during prototype operation and align with failure categories independently identified in the Text2SQL evaluation literature [[8]](#ref-8) [[9]](#ref-9) [[11]](#ref-11).

<a id="table-1"></a>

| Error Class | Stage | Definition | Recovery Mechanism |
|---|---|---|---|
| **E1: Schema hallucination** | SQL Generator | LLM references a column/table not in 𝒟. Example: `SELECT order_total` when column is `line_value`. | Retry with error context + $\mathcal{V}$ grounding + Mechanism IV schema enrichment |
| **E2: Aggregation error** | SQL Generator | Syntactically valid query with semantically wrong aggregation. Example: `AVG` instead of `SUM` for revenue. | Mechanism IV prompt refinement via $f_\text{qrm}$; not recoverable by retry alone |
| **E3: Join path error** | Planner | Join between incompatible entities or incorrect key, no path in $\mathcal{R}$. | Validator detects via $\mathcal{S}$ consistency check; retry with corrected plan; Mechanism IV rule injection |
| **E4: Semantic misunderstanding** | Planner | Query intent misclassified; plan addresses a different BI task. Example: trend query classified as metric lookup. | Mechanism IV prompt refinement via $f_\text{usr}$; requires $\mathcal{S}$ quality improvement |
| **E5: Cross-source failure** | Planner | Single-source plan issued for a multi-source query because $\mathcal{S}$ has low-confidence cross-source relationships. | Prevented by Mechanism I; categorically unaddressable by any single-source system |

*Table 1. Error taxonomy with stage attribution and recovery mapping.*

E1 and E3 are recoverable at query time (retry + grounding); E2 and E4 require Mechanism IV; E5 is prevented by Mechanism I.

---

<a id="8-evaluation-design"></a>
## 8. Evaluation Design

We define eight experiments: six core experiments each mapping directly to an architectural claim, and two secondary experiments for system characterization. **All result tables below contain empty cells to be filled upon experimental runs.**

<a id="81-dataset-and-baselines"></a>
### 8.1 Dataset and Baselines

**BI Question Suite** — 50 questions across four complexity tiers:

<a id="table-2"></a>

| Tier | Description | # Questions | Primary Error Classes Targeted |
|---|---|---|---|
| L1 | Single-source metric lookup | 15 | E1, E2 |
| L2 | Multi-table join (single source) | 15 | E1, E2, E3 |
| L3 | Cross-source multi-hop | 10 | E3, E4, E5 |
| L4 | Unstructured + structured (RAG) | 10 | E4 |

Each question has: natural language prompt, gold SQL (manually written), gold result set, and error-class annotation. Gold SQL annotation was performed by the author and one independent domain expert (data engineer), with disagreements resolved by a third independent reviewer. The annotation protocol follows the Spider/BIRD methodology [[7]](#ref-7) [[11]](#ref-11) adapted to the multi-source uncurated setting.

**Baselines:**
- **𝔅₁ (Direct LLM-to-SQL):** GPT-4o single call with raw schema context. No semantic layer, no orchestration, no learning.
- **𝔅₂ (Schema-aware LLM):** GPT-4o with schema descriptions and column metadata injected as context. No semantic layer, no orchestration. Represents the strongest single-call baseline [[9]](#ref-9) [[12]](#ref-12).
- **𝔅₃ (Pipeline, no semantic layer):** Full six-stage pipeline on raw schemas. No $\mathcal{S}$, no $\delta$, no $\mathcal{V}$ updates.

**Ablation variants** (named descriptively to avoid collision):
- **ABL-NoSynth:** Six-stage pipeline, raw schemas, no $\mathcal{S}$, no $\mathcal{V}$ updates (same as 𝔅₃)
- **ABL-Mono:** Monolithic single LLM call with full $\mathcal{S}$ context, no decomposition
- **ABL-NoPlanner:** Five-stage pipeline, Planner removed
- **ABL-NoValidator:** Six-stage pipeline, Validator disabled
- **ABL-NoRetry:** Six-stage pipeline, $K=0$ (no retry loop)
- **ABL-NoVector:** Six-stage pipeline, $\mathcal{V}$ disabled
- **ABL-NoFeedback:** Six-stage full pipeline, $\alpha=0$ (no $\delta$ updates)
- **C2C-Full:** All components active

**Metrics:**
- *Execution Accuracy (EA):* % queries executing without runtime error. **Primary metric.**
- *Result Correctness (RC):* % queries whose result set matches gold answer. **Primary metric.**
- *SQL Exact Match (EM):* % generated SQL matching gold SQL after normalization [[7]](#ref-7). **Secondary metric.** For L3 multi-source queries, multiple valid SQL formulations may exist, making RC more appropriate as primary.
- *Error Class Rate:* % failures attributed to each of E1–E5.
- *Latency P50/P95:* End-to-end response time in milliseconds.
- *Statistical significance:* McNemar's test on EA/RC differences [[7]](#ref-7); Mann-Whitney U on latency distributions ($\alpha = 0.05$).

<a id="82-experiment-1-baseline-vs-c2c-primary-proof"></a>
### 8.2 Experiment 1: Baseline vs. C2C (Primary Proof)

**Maps to:** Central hypothesis; RQ3  
**Goal:** Demonstrate C2C outperforms direct and schema-aware LLM approaches across all query tiers.

<a id="table-3"></a>

| System | L1 EA | L2 EA | L3 EA | L4 EA | Overall EA | Overall RC |
|---|---|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — | — | — | — |
| 𝔅₂: Schema-aware LLM | — | — | — | — | — | — |
| C2C-Full | — | — | — | — | — | — |

**Prediction:** EA(C2C-Full) ≥ EA(𝔅₁) + 25pp overall. EA(C2C-Full) on L3 > 0% while EA(𝔅₁) on L3 = 0%.  
**Failure condition:** If overall improvement < 5pp, the central hypothesis does not hold.

<a id="83-experiment-2-semantic-layer-impact"></a>
### 8.3 Experiment 2: Semantic Layer Impact

**Maps to:** Mechanism I; RQ1, RQ2  
**Goal:** Isolate the contribution of the automated semantic layer on error class rates.

<a id="table-4"></a>

| System | E1 Rate | E2 Rate | E3 Rate | E5 Rate | L2 EA | L3 EA |
|---|---|---|---|---|---|---|
| 𝔅₂: Schema-aware LLM | — | — | — | — | — | — |
| 𝔅₃: Pipeline, no 𝒮 | — | — | — | — | — | — |
| C2C-Full | — | — | — | — | — | — |

**Semantic synthesis quality sub-results (RQ1):**

<a id="table-5"></a>

| Metric | Result |
|---|---|
| Entities inferred / gold total | — / — |
| Metrics inferred / gold total | — / — |
| Cross-source relationships inferred / gold total | — / — |
| Mapping F1 ($\kappa \geq 0.80$ subset) | — |
| Human review time to acceptable $\mathcal{S}$ | — hours |

**Predictions:** E1 rate significantly lower in C2C-Full than 𝔅₂; E3 rate significantly lower in C2C-Full than 𝔅₃; E5 rate = 0 in C2C-Full on L3.

<a id="84-experiment-3-agent-ablation-study"></a>
### 8.4 Experiment 3: Agent Ablation Study

**Maps to:** Mechanism II; RQ3  
**Goal:** Demonstrate that pipeline decomposition contributes beyond the semantic layer, and that each stage independently matters.

<a id="table-6"></a>

| Variant | EA | RC | E1 Rate | E3 Rate | P50 (ms) |
|---|---|---|---|---|---|
| 𝔅₂: Schema-aware LLM (no decomp, no 𝒮) | — | — | — | — | — |
| ABL-Mono: Single LLM + 𝒮 | — | — | — | — | — |
| ABL-NoPlanner | — | — | — | — | — |
| ABL-NoValidator | — | — | — | — | — |
| ABL-NoRetry | — | — | — | — | — |
| C2C-Full | — | — | — | — | — |

**Predictions:** EA(C2C-Full) > EA(ABL-Mono) on L2–L3; removing Validator increases policy violations > 0; EA(ABL-NoRetry) < EA(C2C-Full).

<a id="85-experiment-4-heterogeneous-data-handling"></a>
### 8.5 Experiment 4: Heterogeneous Data Handling

**Maps to:** Core claim on heterogeneous data; RQ4  
**Goal:** Demonstrate C2C degrades less than baselines as data heterogeneity increases.  
**Note:** Tier captures both query complexity and data source heterogeneity; disentangling these two dimensions is deferred to the extended version.

<a id="table-7"></a>

| System | L1+L2 EA (Structured) | L3+L4 EA (Heterogeneous) | Absolute Degradation |
|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — |
| 𝔅₂: Schema-aware LLM | — | — | — |
| C2C-Full | — | — | — |

**Prediction:** C2C-Full's degradation < 50% of 𝔅₁'s degradation.

<a id="86-experiment-5-feedback-learning-loop"></a>
### 8.6 Experiment 5: Feedback Learning Loop

**Maps to:** Mechanism IV; RQ5  
**Goal:** Demonstrate measurable improvement over successive query batches.

**Setup:** 50-question suite run in four sequential batches (200 queries total) with feedback enabled between batches for C2C-Full and disabled for ABL-NoFeedback.

<a id="table-8"></a>

| Checkpoint | C2C-Full EA | ABL-NoFeedback EA | C2C-Full E1 Rate | ABL-NoFeedback E1 Rate |
|---|---|---|---|---|
| T=50 (batch 1) | — | — | — | — |
| T=100 (batch 2) | — | — | — | — |
| T=150 (batch 3) | — | — | — | — |
| T=200 (batch 4) | — | — | — | — |

**Expected output:** Graph, X-axis = query batch T, Y-axis = EA (left) and E1 rate (right).  
**Prediction:** EA(C2C-Full, T=200) ≥ EA(C2C-Full, T=50) + 5pp; EA(ABL-NoFeedback) is statistically flat (Mann-Whitney U, $\alpha = 0.05$).  
**Failure condition:** If both curves are flat, Mechanism IV contributes nothing and requires redesign.

<a id="87-experiment-6-vector-grounding-impact"></a>
### 8.7 Experiment 6: Vector Grounding Impact

**Maps to:** Mechanism III; RQ5  
**Goal:** Demonstrate that vector-grounded reasoning reduces first-pass hallucination rate.

**Setup:** Both C2C-Full and ABL-NoVector start from an **empty $\mathcal{V}$**, evaluated across the same 200-query session as [Experiment 5](#86-experiment-5-feedback-learning-loop). The $\mathcal{V}$ grows naturally as queries are processed.

<a id="table-9"></a>

| Checkpoint | C2C-Full First-Pass EA | ABL-NoVector First-Pass EA | C2C-Full E1 Rate | ABL-NoVector E1 Rate |
|---|---|---|---|---|
| T=50 | — | — | — | — |
| T=100 | — | — | — | — |
| T=150 | — | — | — | — |
| T=200 | — | — | — | — |

**Prediction:** By T=100, first-pass EA(C2C-Full) > first-pass EA(ABL-NoVector) by ≥ 8pp on L1+L2; E1 rate in C2C-Full declines faster than ABL-NoVector.

<a id="88-experiment-7-error-taxonomy-distribution-analysis"></a>
### 8.8 Experiment 7: Error Taxonomy Distribution Analysis

**Maps to:** Secondary; validates E1–E5 taxonomy  
**Goal:** Characterize and compare failure distributions across systems. Expected output: stacked bar chart confirming that different architectural decisions suppress different error classes.

<a id="table-10"></a>

| System | E1 (%) | E2 (%) | E3 (%) | E4 (%) | E5 (%) | No Error (%) |
|---|---|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — | — | — | — |
| 𝔅₂: Schema-aware LLM | — | — | — | — | — | — |
| ABL-Mono | — | — | — | — | — | — |
| C2C-Full | — | — | — | — | — | — |

<a id="89-experiment-8-latencyaccuracy-tradeoff"></a>
### 8.9 Experiment 8: Latency–Accuracy Tradeoff

**Maps to:** Secondary; RQ6  
**Goal:** Provide practitioners with explicit cost-benefit data.

<a id="table-11"></a>

| Variant | P50 (ms) | P95 (ms) | Overall EA | Latency premium vs. 𝔅₁ |
|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — | baseline |
| 𝔅₂: Schema-aware LLM | — | — | — | — |
| ABL-NoRetry | — | — | — | — |
| ABL-NoVector | — | — | — | — |
| C2C-Full | — | — | — | — |
| C2C-Full (cache hit) | — | — | — | — |

---

<a id="9-full-evaluation-protocol"></a>
## 9. Full Evaluation Protocol

### Phase 1: Experiments 1–8 (Offline, Reproducible)

Fixed $\mathcal{S}$ snapshot and controlled $\mathcal{V}$ initialization as described per experiment. Statistical significance via McNemar's test on EA/RC differences and Mann-Whitney U on latency distributions ($\alpha = 0.05$).

### Phase 2: Robustness and Drift

Inject four controlled schema perturbations per the Dr. Spider taxonomy [[32]](#ref-32):
1. Column rename: `order_total` → `line_value`
2. Table restructure: Split `orders` into `orders_header` + `orders_lines`
3. New source addition: Second CRM export with partially overlapping entities
4. Policy change: Mark `email_id` as PII requiring masking

For each: measure immediate EA drop, $t^*$ (interactions to restore 90% of pre-drift EA via $\delta$), and $\mathcal{V}$ invalidation behavior. **Prediction:** $t^* \leq 50$ for column rename and policy change; $t^* \leq 100$ for table restructure and new source.

### Phase 3: Pilot User Study

Within-subjects pilot study (n = 10–20 business analyst participants), task-order counterbalanced. Post-task surveys: SUS, NASA-TLX, custom 5-item trust scale. Paired Wilcoxon signed-rank tests ($\alpha = 0.05$).
- **H1:** Task success rate non-inferior to existing tools (ΔTSR ≥ −5%)
- **H2:** Time-to-insight lower with C2C (p < 0.05)
- **H3:** Trust score ≥ 3.5/5 on first use

---

<a id="10-discussion"></a>
## 10. Discussion

### Design Rationale

Existing BI systems fail on uncurated heterogeneous data in two distinguishable ways: *at query time* (wrong SQL, wrong join, hallucinated column) and *across queries* (repeating the same mistake). Single-mechanism interventions are insufficient: a semantic layer without a learning loop degrades as schemas evolve; a learning loop without semantic grounding learns to navigate a schema it still doesn't understand [[5]](#ref-5) [[10]](#ref-10). The four mechanisms address four distinct failure modes, and their combination enables the self-improving property.

### Limitations

LLM-inferred semantic mappings may exhibit hallucination or inconsistency on ambiguous schemas [[20]](#ref-20) [[18]](#ref-18). Multi-source query planning incurs latency proportional to cross-system join complexity. The feedback loop requires reaching batch threshold $\theta_\text{batch}$ before updating, creating a cold-start period for rare error types. Vector store grounding provides no benefit before warm-up queries have been processed. The prototype and evaluation are confined to a single domain (retail); generalization is deferred to the extended version.

### Future Work

1. Extending 𝓛₂ with domain ontologies (FIBO for finance, HL7/FHIR for healthcare) to reduce bootstrap time.
2. Integrating differential privacy [[33]](#ref-33) into $f_\text{vrf}$ for PII-sensitive deployments where masking alone is insufficient.
3. Fine-tuning domain-specific SQL generator models on the $\mathcal{V}$ store to reduce latency while maintaining the grounding benefit [[12]](#ref-12).
4. Defining open benchmarks for AI-over-BI on heterogeneous, uncurated data, complementing Spider [[7]](#ref-7), BIRD [[11]](#ref-11), and Spider 2.0 [[8]](#ref-8).

---

<a id="11-conclusion"></a>
## 11. Conclusion

We introduced **Chaos 2 Clarity** (C2C), a self-improving semantic orchestration framework for LLM-driven business intelligence over heterogeneous, uncurated enterprise data. The paper's central insight—that reliable LLM-over-data systems require semantic grounding and adaptive learning together—motivates a four-mechanism design: an Automated Semantic Layer that builds and continuously updates a semantic model from raw data; a decomposed six-stage Agentic Query Orchestration Pipeline that isolates failure modes for targeted recovery; Vector-Grounded BI Reasoning that suppresses repeated hallucination errors; and a Feedback-Driven Continuous Learning Loop ingesting four structured signal types.

The paper presents a deployed three-source retail prototype, a five-class error taxonomy ([Table 1](#table-1)), and an eight-experiment evaluation protocol with explicit falsifiable predictions. C2C addresses the gap identified by recent data agent surveys [[3]](#ref-3) [[5]](#ref-5) between current AI-over-data systems and the heterogeneous realities of enterprise data environments.

---

## Acknowledgements

The author thanks the open-source communities behind LangChain, LlamaIndex, FastAPI, and Neo4j, whose tools informed the prototype design. Gold SQL annotation was conducted by the author and one independent domain expert, with disagreements resolved by a third independent reviewer. No external funding was received.

---

## Ethics Statement

No human subjects data was collected in the work reported here. The user study ([Section 9](#9-full-evaluation-protocol), Phase 3) will be conducted under appropriate IRB review. The system includes a governance layer ($\mathcal{P}$, $f_\text{vrf}$) enforcing PII protection and data access policies.

---

## Reproducibility Statement

Prototype implementation, prompt templates, BibTeX reference file, TikZ figure sources, the 50-question BI suite with gold SQL and result sets, and all evaluation scripts will be released at:

**[https://github.com/bankupalliravi/chaos2clarity](https://github.com/bankupalliravi/chaos2clarity)**

---

<a id="references"></a>
## References

> *All arXiv links point to the abstract page. DOI links point to the canonical publisher record.*

<a id="ref-1"></a>
**[1]** OpenAI. [GPT-4 Technical Report](https://arxiv.org/abs/2303.08774). 2023. `arXiv:2303.08774`

<a id="ref-2"></a>
**[2]** Minaee, S., Mikolov, T., Nikzad, N., Chenaghlu, M., Socher, R., Amatriain, X., & Gao, J. [Large Language Models: A Survey](https://arxiv.org/abs/2402.06196). 2024. `arXiv:2402.06196`

<a id="ref-3"></a>
**[3]** Rahman, M., Bhuiyan, A., Islam, M. S., Laskar, M. T. R., Masry, A., Joty, S., & Hoque, E. [LLM-Based Data Science Agents: A Survey of Capabilities, Challenges, and Future Directions](https://arxiv.org/abs/2510.04023). 2025. `arXiv:2510.04023`

<a id="ref-4"></a>
**[4]** Jiang, J., Xie, H., Shen, S., Shen, Y., et al. [SiriusBI: A Comprehensive LLM-Powered Solution for Data Analytics in Business Intelligence](https://arxiv.org/abs/2411.06102). Tencent SiriusAI, 2024. `arXiv:2411.06102`

<a id="ref-5"></a>
**[5]** Zhu, Y., Wang, L., Yang, C., et al. [A Survey of Data Agents: Emerging Paradigm or Overstated Hype?](https://arxiv.org/abs/2510.23587) 2025. `arXiv:2510.23587`

<a id="ref-6"></a>
**[6]** Various Authors. [A Survey of LLM × DATA](https://arxiv.org/abs/2505.18458). 2025. `arXiv:2505.18458`

<a id="ref-7"></a>
**[7]** Yu, T., Zhang, R., Yang, K., Yasunaga, M., Wang, D., Li, Z., Ma, J., Li, I., Yao, Q., Roman, S., Zhang, Z., & Radev, D. [Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL](https://arxiv.org/abs/1809.08887). *EMNLP 2018*. `arXiv:1809.08887`

<a id="ref-8"></a>
**[8]** Lei, F., Chen, J., Ye, Y., Cao, R., et al. [Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows](https://arxiv.org/abs/2411.07763). 2024. `arXiv:2411.07763`

<a id="ref-9"></a>
**[9]** Shi, L., Tang, Z., Zhang, N., Zhang, X., & Yang, Z. [A Survey on Employing Large Language Models for Text-to-SQL Tasks](https://arxiv.org/abs/2407.15186). Peking University, 2024. `arXiv:2407.15186`

<a id="ref-10"></a>
**[10]** Chen, W., et al. [LLM/Agent-as-Data-Analyst: A Survey](https://arxiv.org/abs/2509.23988). 2025. `arXiv:2509.23988`

<a id="ref-11"></a>
**[11]** Li, J., Hui, B., Qu, G., Yang, J., Li, B., Li, B., Wang, B., Qin, B., Cao, R., Geng, R., Huo, N., Ma, C., Chang, K. C.-C., Huang, F., Cheng, R., & Li, Y. [Can LLM Already Serve as a Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs (BIRD)](https://arxiv.org/abs/2305.03111). *NeurIPS 2023*. `arXiv:2305.03111`

<a id="ref-12"></a>
**[12]** Gao, D., Wang, H., Li, Y., Sun, X., Qian, Y., Ding, B., & Zhou, J. [Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation (DAIL-SQL)](https://arxiv.org/abs/2308.15363). 2023. `arXiv:2308.15363`

<a id="ref-13"></a>
**[13]** Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework](https://arxiv.org/abs/2308.08155). Microsoft Research. *ICLR 2024*. `arXiv:2308.08155`

<a id="ref-14"></a>
**[14]** Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629). *ICLR 2023*. `arXiv:2210.03629`

<a id="ref-15"></a>
**[15]** Arunkumar, V., Gangadharan, G. R., & Buyya, R. [Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents](https://arxiv.org/abs/2601.12560). 2026. `arXiv:2601.12560`

<a id="ref-16"></a>
**[16]** Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). *NeurIPS 2020*. `arXiv:2005.11401`

<a id="ref-17"></a>
**[17]** Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., Guo, Q., Wang, M., & Wang, H. [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997). 2024. `arXiv:2312.10997`

<a id="ref-18"></a>
**[18]** Gungor, O. E., Paulsen, D., & Kang, W. [SCHEMORA: Schema Matching via Multi-Stage Recommendation and Metadata Enrichment using Off-the-Shelf LLMs](https://arxiv.org/abs/2507.14376). 2025. `arXiv:2507.14376`

<a id="ref-19"></a>
**[19]** Rahm, E., & Bernstein, P. A. [A Survey of Approaches to Automatic Schema Matching](https://doi.org/10.1007/s007780100048). *The VLDB Journal*, 10(4):334–350, 2001.

<a id="ref-20"></a>
**[20]** Singh, M., Kumar, A., Donaparthi, S., & Karambelkar, G. [Leveraging Retrieval Augmented Generative LLMs for Automated Metadata Description Generation to Enhance Data Catalogs](https://arxiv.org/abs/2503.09003). Fidelity Investments, 2025. `arXiv:2503.09003`

<a id="ref-21"></a>
**[21]** An, Q., Ying, C., Zhu, Y., Xu, Y., Zhang, M., & Wang, J. [LEDD: Large Language Model-Empowered Data Discovery in Data Lakes](https://arxiv.org/abs/2502.15182). 2025. `arXiv:2502.15182`

<a id="ref-22"></a>
**[22]** Ma, P., Ding, R., Wang, S., Han, S., & Zhang, D. [InsightPilot: An LLM-Empowered Automated Data Exploration System](https://aclanthology.org/2023.emnlp-demo.31/). Microsoft Research. *EMNLP System Demonstrations 2023*.

<a id="ref-23"></a>
**[23]** Cheng, L., Li, X., & Bing, L. [Is GPT-4 a Good Data Analyst?](https://arxiv.org/abs/2305.15038) Alibaba DAMO Academy, 2023. `arXiv:2305.15038`

<a id="ref-24"></a>
**[24]** Karim, S. F., Kelifa, A., Kjær, A. M. H., Jiang, S., Sørbø, S., & Roman, D. [LLMDapCAT: An LLM-Based Data Catalogue System for Data Sharing and Exploration](https://ceur-ws.org/Vol-4085/paper80.pdf). SINTEF AS. *CEUR Workshop Proceedings*, Vol. 4085, 2024.

<a id="ref-25"></a>
**[25]** Adimulam, A., Gupta, R., & Kumar, S. [The Orchestration of Multi-Agent Systems: Architectures, Protocols, and Enterprise Adoption](https://arxiv.org/abs/2601.13671). 2026. `arXiv:2601.13671`

<a id="ref-26"></a>
**[26]** Bogavelli, T., Sharma, R., & Subramani, H. [AgentArch: A Comprehensive Benchmark to Evaluate Agent Architectures in Enterprise](https://arxiv.org/abs/2509.10769). ServiceNow, 2025. `arXiv:2509.10769`

<a id="ref-27"></a>
**[27]** Del Rosario, R. F., Krawiecka, K., & Schroeder de Witt, C. [Architecting Resilient LLM Agents: A Guide to Secure Plan-then-Execute Implementations](https://arxiv.org/abs/2509.08646). 2025. `arXiv:2509.08646`

<a id="ref-28"></a>
**[28]** Cheerla, C. [Advancing Retrieval-Augmented Generation for Structured Enterprise and Internal Data](https://arxiv.org/abs/2507.12425). 2025. `arXiv:2507.12425`

<a id="ref-29"></a>
**[29]** Es, S., James, J., Espinosa-Anke, L., & Schockaert, S. [RAGAS: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217). 2023. `arXiv:2309.15217`

<a id="ref-30"></a>
**[30]** Pan, F., Canim, M., Glass, M., Gliozzo, A., & Hendler, J. [End-to-End Table Question Answering via Retrieval-Augmented Generation](https://arxiv.org/abs/2203.16714). IBM Research / RPI, 2022. `arXiv:2203.16714`

<a id="ref-31"></a>
**[31]** Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q. V., & Zhou, D. [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903). Google Brain. *NeurIPS 2022*. `arXiv:2201.11903`

<a id="ref-32"></a>
**[32]** Chang, S., Wang, J., Dong, M., Pan, L., Zhu, H., Li, A. H., Lan, W., Zhang, S., Jiang, J., Lilien, J., Ash, P., Wang, W. Y., Wang, Z., Castelli, V., Ng, P., & Xiang, B. [Dr. Spider: A Diagnostic Evaluation Benchmark towards Text-to-SQL Robustness](https://arxiv.org/abs/2301.08881). AWS AI / OSU. *ICLR 2023*. `arXiv:2301.08881`

<a id="ref-33"></a>
**[33]** Dwork, C., McSherry, F., Nissim, K., & Smith, A. [Calibrating Noise to Sensitivity in Private Data Analysis](https://doi.org/10.1007/11681878_14). *Theory of Cryptography Conference (TCC)*, 2006. `DOI:10.1007/11681878_14`

---

<a id="appendix-a-semantic-model-schema"></a>
## Appendix A: Semantic Model Schema

**Node types:**

| Node Type | Attributes |
|---|---|
| `Entity` $e$ | `name`, `aliases[]`, `source_tables[]`, κ, `pii_flag` |
| `Metric` $m$ | `name`, φ (formula), `unit`, `source_cols[]`, κ |
| `Dimension` $d$ | `name`, `values_sample[]`, `source_col`, `time_flag` |
| `DataSource` | `source_type` τ, `conn_ref`, σ (schema version), $t_\text{profiled}$ |
| `Policy` $p$ | `type` ∈ {pii, access, compute}, `rule`, `scope`, `priority` |

**Edge types:**

| Edge | Connects | Attributes |
|---|---|---|
| `DerivedFrom` | $m \to e$ | κ, formula ref |
| `SliceableBy` | $m \to d$ | join path |
| `ForeignKey` | $d_i \to d_j$ | `inferred_flag` |
| `SynonymousWith` | $e \leftrightarrow e'$ | similarity score |
| `GovernedBy` | $e, m \to p$ | enforcement level |

---

<a id="appendix-b-agent-prompt-templates"></a>
## Appendix B: Agent Prompt Templates

### B.1 Planner
```
System: You are a BI query planner.
Classify the task type and generate a step-by-step execution plan.
Task types: [metric_lookup | trend_analysis | slice_and_dice |
cross_source_join | anomaly_investigation | forecast |
comparison | what_if | policy_check | other]
Each plan step: {data_source, operation, dependencies, estimated_cost}.
Apply governance policies before planning.
Output: {"task_type":"<>","entities":[...],"metrics":[...],
"time_range":"...","plan_steps":[...],"confidence":<0-1>}
User question: {user_question}
Semantic model summary: {sm_summary}
Grounding context (k verified similar plans): {grounding_plans}
Active policies: {active_policies}
```

### B.2 SQL Generator
```
System: You are a BI SQL generator.
Generate SQL conditioned on the execution plan and grounding context.
If a grounding example shows the correct column name for a concept,
prefer it over inference.
Plan: {execution_plan} | Semantic model: {sm_json}
Grounding context: {verified_sql_examples}
Error context from previous attempt (if any): {error_ctx}
```

### B.3 Validator
```
System: You are a BI safety and consistency agent. Check:
1. PII policy violations
2. Full table scan risks (> max_rows={max_rows})
3. Join plausibility against semantic model
4. Entity references: all must have κ ≥ {theta_exec}
Output: {"approved":true|false,"violations":[...],"warnings":[...],
"modified_query":"<safe SQL or null>"}
Query: {proposed_sql} | Semantic model: {sm_summary}
```

### B.4 Insight Agent
```
System: You are a BI insight narrator and feedback emitter.
1. Generate a clear natural-language insight.
2. Identify result anomalies or semantic mismatches.
3. Rate result usefulness 0-1.
Output: {"narrative":"<>","anomalies":[...],"usefulness_score":<0-1>,
"feedback_signals":{"f_qrm":<0|1>,"f_ins":<usefulness_score>}}
Result: {result_set} | Execution trace: {provenance}
```

---

<a id="appendix-c-bi-question-suite--sample-questions"></a>
## Appendix C: BI Question Suite — Sample Questions

- **L1.** "What was our total gross revenue last quarter?"
- **L1.** "How many orders were placed in March 2024?"
- **L2.** "What is the revenue breakdown by product category for Q4?"
- **L2.** "Which customers placed more than 5 orders in the last 90 days?"
- **L3.** "Which customers with active CRM deals have had delivery issues in the last 30 days?"
- **L3.** "What is the average deal size for customers whose last delivery was delayed by more than 3 days?"
- **L4.** "Summarize delivery complaint emails for our top 10 customers by revenue in Q1."
- **L4.** "Which product categories have the most negative sentiment in customer support tickets this month?"

*(Full 50-question suite with gold SQL, gold result sets, and error-class annotations released in the [repository](https://github.com/bankupalliravi/chaos2clarity).)*

---

<a id="appendix-d-comparison-with-existing-systems"></a>
## Appendix D: Comparison with Existing Systems

| Capability | C2C | NL2SQL [[9]](#ref-9) | InsightPilot [[22]](#ref-22) | SiriusBI [[4]](#ref-4) | Catalogs [[20]](#ref-20) | Commercial BI |
|---|---|---|---|---|---|---|
| Handles uncurated data | ✓ | ✗ | ✗ | ✗ | ◦ | ✗ |
| Auto semantic synthesis | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ |
| Decomposed pipeline | ✓ | ✗ | ◦ | ◦ | ✗ | ✗ |
| Cross-source planning | ✓ | ✗ | ◦ | ✗ | ✗ | ✗ |
| Vector-grounded reasoning | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Feedback-driven self-improvement | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| RAG (struct. + unstruct.) | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Governance layer | ✓ | ✗ | ✗ | ◦ | ◦ | ◦ |
| Conversational BI UI | ✓ | ◦ | ✓ | ✓ | ✗ | ✓ |

*✓ = supported · ◦ = partial · ✗ = not supported*

---

<a id="appendix-e-feedback-signal-taxonomy"></a>
## Appendix E: Feedback Signal Taxonomy

Full specification of the four signal types processed by the feedback loop $\delta$ ([Section 5.6](#56-mechanism-iv-feedback-driven-learning-loop)):

| Signal | Source | Trigger | Update Targets |
|---|---|---|---|
| $f_\text{sql}$ | Executor | Any SQL success or failure | Schema enrichment (E1/E3), $\mathcal{V}$ entry κ updates, rule injection |
| $f_\text{usr}$ | Conversational UI | User edits or explicit correction | Schema enrichment, prompt refinement, synonym embedding updates |
| $f_\text{qrm}$ | Insight Agent | Semantic anomaly between intent and result | Prompt refinement (aggregation), schema enrichment (metric formulas) |
| $f_\text{ins}$ | UI / Insight Agent | Usefulness rating | Prompt refinement (narrator), $\mathcal{V}$ κ_entry decay for low-rated entries |

---

<a id="appendix-f-hyperparameter-sensitivity"></a>
## Appendix F: Hyperparameter Sensitivity

Learning rate α sensitivity analysis over {0.05, 0.10, 0.15, 0.20, 0.30} on a 20-query held-out validation set. Selected value: **α = 0.15**. Results to be completed with experimental runs (see [Experiment 5](#86-experiment-5-feedback-learning-loop)).

| α | Validation EA | Validation E1 Rate | Convergence rate |
|---|---|---|---|
| 0.05 | — | — | — |
| 0.10 | — | — | — |
| **0.15 (selected)** | — | — | — |
| 0.20 | — | — | — |
| 0.30 | — | — | — |

---

## Pre-Submission Checklist

- [ ] Register at [orcid.org](https://orcid.org); replace `0000-0000-0000-0000`
- [ ] Replace `ravi@example.com` with real email
- [ ] Create and populate [github.com/bankupalliravi/chaos2clarity](https://github.com/bankupalliravi/chaos2clarity)
- [ ] Run all eight experiments; fill every `—` cell before arXiv upload
- [ ] Fill [Appendix F](#appendix-f-hyperparameter-sensitivity) from α validation run
- [ ] Verify all 33 references are unique — no duplicates remain
- [ ] Update LaTeX source to match v5: Definitions 5–7, Algorithm 1 with Retriever on line 2, ablation variant naming (ABL-*), Propositions 1–2 (no false k-NN monotonicity claim), "to our knowledge" qualifiers, [Eq. 1](#equation-1) and [Eq. 2](#equation-2) numbered, [Appendix F](#appendix-f-hyperparameter-sensitivity) added
- [ ] Renumber LaTeX bibliography to match this document's 33-reference list (old [11] removed; [12]–[34] renumbered [11]–[33])
- [ ] Test LaTeX compilation: `pdflatex → bibtex → pdflatex → pdflatex`
- [ ] Verify `acmart` compiles on arXiv; fallback to `\documentclass[preprint]{acmart}` if needed
- [ ] Domain expert review before submission
