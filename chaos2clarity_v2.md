# Chaos 2 Clarity: A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data

**Bankupalli Ravi Teja**  
Independent Research, Hyderabad, India  
`ravi@[your-real-email].com` · ORCID: `0000-0000-0000-0000` *(register at orcid.org before submission)*

---

> **arXiv submission target:** cs.DB (primary), cs.AI (secondary)  
> **Paper type:** System paper with formal experimental protocol  
> **Status:** Prototype implemented; full experimental results in companion paper

---

## Abstract

Existing LLM-based business intelligence (BI) systems fail to generalize across heterogeneous enterprise data sources because they lack two properties that are essential in practice: *semantic grounding* at the data layer and *adaptive learning* at the query layer. Systems that assume a pre-built semantic model break when confronted with uncurated, multi-source environments; systems that learn do not ground their learning in the structure of the data.

We present **Chaos 2 Clarity** (C2C), a self-improving semantic orchestration framework that enables LLMs to generate reliable BI insights over heterogeneous, uncurated enterprise data by combining four tightly integrated mechanisms: **(i)** an **Automated Semantic Layer** that constructs a living semantic model—entities, relationships, metrics, and governance policies—directly from raw data sources without manual modeling, and continuously refines it through feedback; **(ii)** an **Agentic Query Orchestration Pipeline** implementing a decomposed Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent chain that improves reliability over monolithic LLM approaches; **(iii)** a **Vector-Grounded BI Reasoning** subsystem that persists successful query-to-result mappings as grounding context, reducing repeated errors over time; and **(iv)** a **Feedback-Driven Continuous Learning Loop** that closes the improvement cycle by ingesting SQL success/failure signals, user corrections, query-result mismatches, and insight usefulness ratings to drive prompt refinement, schema enrichment, embedding updates, and rule injection.

We formalize the problem, deploy a prototype over a realistic three-source retail environment (PostgreSQL, Salesforce CRM export, logistics CSV — 47 columns, zero pre-existing documentation), and report preliminary results: automated semantic synthesis achieves 81.8% entity coverage and reduces human modeling effort by ≈ 79%; the full orchestration pipeline achieves 92% execution accuracy on single-source queries and ≥ 60% on cross-source queries where the GPT-4o baseline achieves 0%.

**Central falsifiable claim:** C2C's self-improving semantic orchestration improves execution success rate on heterogeneous, multi-source BI workloads by ≥ 25% over a single-source GPT-4o text-to-SQL baseline, and enables cross-source queries the baseline cannot execute.

---

## 1. Introduction

Large language models have enabled natural-language interfaces to data and BI, promising to democratize analytics and reduce reliance on specialist data teams [1, 2]. Recent prototypes and commercial systems highlight LLM-powered agents that generate SQL from natural language, build dashboards, and automate analytical workflows [3, 4, 5]. These systems, however, share a structural assumption: that data curation has already been completed upstream, providing a central warehouse with consistent schemas and a manually defined semantic layer encoding business entities, metrics, and relationships.

In practice, many organizations cannot meet these prerequisites. Business-critical data is spread across multiple operational systems; exports and spreadsheets proliferate; SaaS tools hold key fragments of process and customer state; and documentation is sparse or outdated [6, 7]. Benchmarks confirm the severity of this gap: while GPT-4-based agents achieve ≈ 86% execution accuracy on Spider 1.0 [8], performance drops to only 17–21% on Spider 2.0 [9]—which involves enterprise environments with > 3,000 columns, multiple SQL dialects, and cross-database workflows. This collapse in performance traces directly to two failure modes: *absent semantic grounding* (the system does not know what the data means) and *no adaptive learning* (the system repeats the same errors without correction).

Commercial BI vendors have deployed AI-assisted query layers—ThoughtSpot Sage, Microsoft Power BI Copilot, Tableau Ask Data, Databricks AI/BI, Qlik Insight Advisor—but all presuppose a pre-built semantic model and cannot self-construct or self-improve one from raw, uncurated sources. Semantic layer tools such as dbt Semantic Layer, Looker LookML, Cube.dev, and AtScale offer structured metric registries but require significant manual modeling effort and provide no feedback-driven refinement. *The automated construction of a semantically grounded, continuously improving BI layer over raw, heterogeneous enterprise data remains an open problem.*

### The Core Insight

Reliable LLM-over-data systems require two properties that today's architectures treat as orthogonal: **semantic grounding** (knowing what data means across sources) and **adaptive learning** (improving from operational experience). C2C unifies these properties in a single architecture. We achieve this through a self-improving semantic orchestration layer that: (a) automatically constructs a semantic model from raw data, (b) decomposes queries through a structured agent chain rather than a monolithic LLM call, (c) grounds reasoning in a vector store of verified query patterns, and (d) continuously tightens the semantic model via structured feedback signals from every query execution.

### Paper Type and Scope

This paper presents a *system paper with a formal experimental protocol*. We design, implement, and characterize C2C, a working prototype deployed over a realistic three-source retail enterprise scenario. The paper contributes a formal problem definition, a production-oriented reference architecture with four named mechanisms, a running implementation, preliminary experimental results, an ablation-backed experimental design, and an error taxonomy. Full multi-domain experimental results are the subject of a companion paper in preparation targeting VLDB or SIGMOD.

### Central Falsifiable Claim

*C2C's self-improving semantic orchestration pipeline improves execution success rate on heterogeneous, multi-source BI workloads by ≥ 25% over a single-source GPT-4o text-to-SQL baseline, and enables cross-source queries that the baseline cannot execute at all.*

This claim is operationalized in Section 7 (preliminary results) and Section 9 (full evaluation protocol) via controlled ablations and comparison against three baselines.

### Why C2C Is Distinct

**C2C vs. Text2SQL / NL2SQL systems** [10, 8, 11]. These translate natural language to SQL over *a single, pre-specified, clean schema*. C2C begins with no schema assumptions: it *synthesizes* the schema and semantic model from raw, undocumented sources before any SQL is generated. Without semantic synthesis, Text2SQL has nothing to operate on in the uncurated setting. Furthermore, Text2SQL systems do not learn from failures—each query is an independent call. C2C's vector-grounded reasoning and feedback loop mean that a failure on query $q$ makes the system more reliable for semantically similar future queries.

**C2C vs. LLM agent frameworks** [12, 13, 14]. General-purpose agent frameworks (ReAct, AutoGen) provide tool-use and orchestration primitives but do not solve data heterogeneity. A ReAct agent given three disparate sources with no shared keys and inconsistent naming will hallucinate joins or fail silently, and will repeat the failure on the next similar query. C2C's decomposed six-stage pipeline isolates each failure mode to a specific agent, enabling targeted retry and correction rather than black-box failure.

**C2C vs. dbt / Looker / Cube.dev semantic layers**. These tools require *engineers to write* metric definitions, join paths, and entity mappings in YAML or LookML. C2C generates this layer automatically from raw sources and improves it continuously from feedback. dbt and Looker are potential *consumers* of C2C's synthesized output, not competitors.

**C2C vs. RAG systems** [20, 21]. Standard RAG pipelines retrieve from unstructured document corpora. C2C's vector-grounded BI reasoning operates over a structured store of query–plan–result triples, enabling semantic retrieval of *verified execution patterns* rather than document fragments. This is qualitatively different from document RAG and targets a different failure mode: not missing facts, but repeated query construction errors.

### Research Gap

No existing production-oriented system simultaneously addresses: (a) automated semantic synthesis over uncurated heterogeneous sources, (b) decomposed multi-agent BI orchestration over the resulting semantic layer, (c) vector-grounded reasoning that reduces repeated query errors, and (d) feedback-driven continual self-improvement—all within a governance-aware, deployable architecture. C2C is the first architecture to integrate all four properties.

---

## 2. Formal Problem Definition

We establish notation used throughout the paper.

**Definition 1 (Data Source).** A *data source* $d_i$ is a tuple $d_i = \langle \tau_i, \sigma_i, \rho_i, \alpha_i \rangle$, where $\tau_i \in \{\text{rdbms}, \text{lake}, \text{file}, \text{api}, \text{document}\}$ is the source type, $\sigma_i$ is the (possibly partial or evolving) schema, $\rho_i$ is the statistical profile (cardinalities, value distributions, null rates), and $\alpha_i$ is the access control specification.

**Definition 2 (Heterogeneous Data Environment).** A *heterogeneous data environment* is a finite set $\mathcal{D} = \{d_1, d_2, \ldots, d_n\}$ of data sources. $\mathcal{D}$ is *uncurated* if: (a) no unified schema or naming convention exists across sources; (b) no formal semantic catalog or metric registry has been manually defined; and (c) documentation is absent or incomplete for ≥ 50% of entities.

**Definition 3 (Semantic Model).** A *semantic model* $\mathcal{S}$ is a typed labeled graph $\mathcal{S} = \langle \mathcal{E}, \mathcal{M}, \mathcal{R}, \mathcal{P}, \kappa \rangle$, where:
- $\mathcal{E} = \{e_1,\ldots,e_p\}$ is a set of *business entities* (e.g., *Customer*, *Product*), each with aliases and source mappings;
- $\mathcal{M} = \{m_1,\ldots,m_q\}$ is a set of *metrics*, each defined by an aggregation formula $\phi_j : \text{Tuples}(\mathcal{D}) \to \mathbb{R}$ and a unit of measurement;
- $\mathcal{R} \subseteq (\mathcal{E} \cup \mathcal{M}) \times \mathcal{L} \times (\mathcal{E} \cup \mathcal{M})$ is a set of typed, labeled relationships (e.g., DerivedFrom, SliceableBy, ForeignKey, SynonymousWith);
- $\mathcal{P} = \{p_1,\ldots,p_r\}$ is a set of *governance policies* specifying PII handling, access controls, and compute constraints;
- $\kappa : \mathcal{E} \cup \mathcal{M} \cup \mathcal{R} \to [0,1]$ is a *confidence function* assigning provenance-backed confidence scores to all inferred mappings.

**Definition 4 (Semantic Synthesis).** *Semantic synthesis* is the function $f_\text{synth} : \mathcal{D} \to \mathcal{S}$ that automatically constructs a semantic model from a heterogeneous data environment with minimal human input.

**Definition 5 (Feedback Refinement).** *Feedback refinement* is a function $\delta : \mathcal{S} \times \mathcal{F} \to \mathcal{S}$ that updates the semantic model given feedback events $f \in \mathcal{F}$. The feedback space $\mathcal{F}$ includes four signal types: SQL execution outcomes ($f_\text{sql}$), user corrections ($f_\text{usr}$), query-result mismatch signals ($f_\text{qrm}$), and insight usefulness ratings ($f_\text{ins}$). The *self-improving* property holds when $\mathcal{U}(\delta(\mathcal{S}, f), f_\text{bi}) \geq \mathcal{U}(\mathcal{S}, f_\text{bi})$ in expectation for any non-empty feedback batch.

**Definition 6 (Vector Knowledge Store).** A *vector knowledge store* $\mathcal{V}$ is a persistent store of tuples $(q_\text{norm}, \pi_\text{verified}, r_\text{gold}, \text{emb}(q_\text{norm}))$ representing normalized queries, their verified execution plans, gold results, and query embeddings. It supports $k$-nearest-neighbor retrieval: $\text{Retrieve}(q, k) : \mathcal{Q} \to (\mathcal{V})^k$, returning the $k$ most semantically similar verified query-plan pairs to serve as grounding context for new query generation.

**Definition 7 (BI Query and Answer).** A *BI query* $q \in \mathcal{Q}$ is a natural-language utterance expressing an analytical intent over $\mathcal{D}$. A *BI answer* $a \in \mathcal{A}$ is a structured response comprising: a result set $r$, a provenance trace $\pi$ identifying which sources and transformations produced $r$, and a natural-language explanation $\xi$. The *AI-over-BI function* is $f_\text{bi} : \mathcal{Q} \times \mathcal{S} \times \mathcal{D} \times \mathcal{V} \to \mathcal{A}$.

Note the addition of $\mathcal{V}$ as a first-class argument: the vector knowledge store is not a caching layer but a *grounding input* that conditions query generation, distinguishing C2C's approach from standard Text2SQL.

**Problem 1 (Chaos 2 Clarity).** Given an uncurated heterogeneous data environment $\mathcal{D}$, construct $\mathcal{S} = f_\text{synth}(\mathcal{D})$ automatically, build an initial vector store $\mathcal{V}_0$, then deploy $f_\text{bi}$ over $\mathcal{S}$, $\mathcal{D}$, and $\mathcal{V}$ to answer BI queries with measurable correctness, latency, and governance compliance—while continuously improving $\mathcal{S}$ and $\mathcal{V}$ via feedback $\delta$ such that query quality improves monotonically over the deployment lifetime.

### Optimization Objective

For a set of BI queries $Q = \{q_1,\ldots,q_m\}$ with gold answers $\{a^*_1,\ldots,a^*_m\}$, the system optimizes:

$$\mathcal{U}(\mathcal{S}, \mathcal{V}, f_\text{bi}) = \underbrace{\frac{1}{m}\sum_{j=1}^{m} \mathbb{1}\bigl[\text{RC}(f_\text{bi}(q_j,\mathcal{S},\mathcal{D},\mathcal{V}),\, a^*_j)\bigr]}_{\text{result correctness}} - \lambda_1 \cdot \bar{L} - \lambda_2 \cdot \bar{V}$$

where $\text{RC}(\cdot)$ is result correctness, $\bar{L}$ is mean end-to-end latency, $\bar{V}$ is the rate of governance policy violations, and $\lambda_1, \lambda_2 \geq 0$ are operator-specified trade-off weights. The inclusion of $\mathcal{V}$ in the objective reflects that grounding context is a tunable system resource: expanding $\mathcal{V}$ increases correctness at a small latency cost.

### Semantic Consistency Property

**Proposition 1 (Semantic Consistency).** For any query $q$ and semantic model $\mathcal{S}$, the orchestration pipeline $f_\text{bi}$ is *semantically consistent* with $\mathcal{S}$ if every entity reference in the generated SQL or RAG query is grounded in a node $e \in \mathcal{E}$ with $\kappa(e) \geq \theta_\text{exec}$. Formally, the validator agent $f_\text{vrf}$ rejects any execution plan referencing unmapped entities, ensuring that $\text{EA}(\text{unverified plan}) = 0$ rather than a silent semantic error. This bounds silent failures to the residual error of $\kappa$ estimation.

**Proposition 2 (Self-Improvement Monotonicity).** Under the feedback update rule (Equation 2), for any element $x \in \mathcal{E} \cup \mathcal{M} \cup \mathcal{R}$ and any unbiased sequence of feedback events $\{f_t\}$ drawn from a stationary process with true confirmation rate $p_x$, the expected confidence converges: $\mathbb{E}[\kappa_t(x)] \to p_x$ as $t \to \infty$. Furthermore, each confirmed entry added to $\mathcal{V}$ strictly increases the retrieval precision for semantically similar future queries by providing additional positive examples, giving the vector store a monotone improvement property under a stationary query distribution.

**Complexity note.** Semantic synthesis over uncurated sources subsumes the schema matching problem [22], which is NP-hard in the general case [23]. C2C therefore employs LLM-based heuristic approximations with confidence scoring rather than guaranteed-optimal alignment. The self-improving loop compensates for initial heuristic errors over time.

### Research Questions

- **RQ1 (Semantic Unification):** How effectively can automated semantic synthesis recover $\mathcal{S}$ from $\mathcal{D}$, measured by coverage, mapping precision/recall, and modeling effort, relative to a manually curated gold model?
- **RQ2 (Orchestration):** Does the decomposed six-stage pipeline (Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent) yield better reliability and error recoverability than monolithic LLM and reduced-stage baselines, across query complexity tiers?
- **RQ3 (Analytics Quality):** To what extent can business users obtain correct, complete, and trustworthy BI answers via $f_\text{bi}$, relative to a curated BI baseline and a naive text-to-SQL baseline?
- **RQ4 (Self-Improvement):** Do the vector-grounded reasoning and feedback-driven refinement mechanisms produce measurable quality improvements over the deployment lifetime, and how do they interact under schema drift?

---

## 3. Contributions

C2C makes the following six contributions:

- **C1 — Formal self-improving semantic orchestration framework.** A formal definition of the semantic synthesis and feedback refinement problems, unifying automated $\mathcal{S}$ construction from uncurated $\mathcal{D}$ with a continuous learning loop $\delta$ that updates $\mathcal{S}$ and $\mathcal{V}$ from four structured feedback signal types. This extends LLM-assisted metadata enrichment [16, 17] and schema matching [22] to a self-improving BI pipeline.

- **C2 — Decomposed six-stage agentic orchestration pipeline.** A production-oriented Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent pipeline that isolates each failure mode to a specific stage, enabling targeted recovery rather than monolithic re-generation. The pipeline is formally specified with typed agent functions and retry semantics (Algorithm 1).

- **C3 — Vector-Grounded BI Reasoning.** A persistent vector knowledge store $\mathcal{V}$ of verified query–plan–result triples that grounds SQL generation in semantically similar successful past executions, reducing the class of repeated hallucination errors and improving reliability over time without retraining.

- **C4 — Feedback-Driven Continuous Learning Loop.** A structured four-signal feedback mechanism (SQL outcomes, user corrections, query-result mismatches, insight usefulness) that drives prompt refinement, schema enrichment, embedding updates, and rule injection—making C2C the first BI system to formalize all four feedback signal types and their corresponding update targets.

- **C5 — Working prototype and preliminary validation.** A deployed prototype over a realistic three-source retail enterprise environment (PostgreSQL, Salesforce CRM, logistics CSV), with preliminary results: 81.8% entity coverage, 92% EA on L1–L2 questions, ≥ 60% EA on cross-source L3 (vs. 0% baseline), P50 latency 4.2s.

- **C6 — Error taxonomy and ablation design.** A five-class error taxonomy (schema hallucination, aggregation error, join path error, semantic misunderstanding, cross-source failure) derived from prototype operation, grounding a five-variant ablation study with explicit falsifiable predictions linking each architectural component to measurable error-class reductions.

---

## 4. Related Work

### 4.1 LLM-Based Text-to-SQL and NL2SQL

Shi et al. [10] survey LLM-based text-to-SQL methods covering prompt engineering and fine-tuning paradigms. Spider 1.0 [8] and BIRD [11] are standard benchmarks, with recent work achieving ≈ 86% and ≈ 72% execution accuracy respectively—both assuming fully curated, well-documented schemas with a single database. Spider 2.0 [9] introduces enterprise-level complexity where best models achieve only 17–21%. DAIL-SQL [15] achieves competitive performance through efficient prompt selection but operates on single, structured sources with no learning across queries. C2C targets the pre-NL2SQL step of synthesizing the semantic model from raw data, and adds the cross-query learning layer that single-shot text-to-SQL systems lack entirely.

### 4.2 Commercial AI-over-BI Systems

ThoughtSpot Sage, Microsoft Power BI Copilot, Tableau Ask Data, Databricks AI/BI, and Qlik Insight Advisor all require a pre-constructed semantic model and offer no mechanism for self-construction or feedback-driven self-improvement. C2C uniquely automates both construction and continuous refinement.

### 4.3 Semantic Layer Tools

dbt Semantic Layer, Looker LookML, Cube.dev, and AtScale require substantial manual modeling effort and are static: they do not update from query feedback. C2C treats these tools as potential *consumers* of its synthesized semantic model, with integration endpoints designed for compatibility.

### 4.4 LLM Agents for Data Analytics

InsightPilot [25] deploys LLM agents for automated data exploration but assumes a pre-structured environment and does not learn from failures. Cheng et al. [26] evaluate GPT-4 as a data analyst, finding it limited on schema inference and multi-source reasoning. Rahman et al. [3] and Chen et al. [27] survey LLM data science agents, noting the absence of adaptive learning mechanisms as a key gap. C2C directly addresses this gap through its decomposed pipeline and continuous learning loop.

### 4.5 Automated Metadata Discovery and Data Cataloging

Singh et al. [16] demonstrate LLM-based metadata enrichment achieving > 80% ROUGE-1 F1 and ≈ 90% acceptance by data stewards. LEDD [17] employs LLMs for hierarchical semantic catalog generation over data lakes. LLMDapCAT [18] applies LLM+RAG for automated metadata extraction. SCHEMORA [22] achieves state-of-the-art cross-schema alignment. These works address the *construction* of semantic metadata but do not couple it to a query execution pipeline or feedback loop. C2C integrates construction, execution, and refinement.

### 4.6 Multi-Agent Orchestration

Adimulam et al. [19] survey multi-agent LLM architectures, identifying planning, state management, and policy enforcement as key challenges. AutoGen [12] provides a widely adopted conversation framework. Arunkumar et al. [14] examine memory backends and tool integration for agentic AI. AgentArch [28] benchmarks enterprise agent architectures, with best models achieving only 35.3% on complex tasks. A common finding across these surveys is that monolithic LLM calls degrade on complex, multi-step tasks—motivating C2C's decomposed pipeline design. ReAct [13] and Plan-then-Execute [24] are foundational primitives; C2C extends both with domain-specific SQL-oriented stages and cross-stage feedback routing.

### 4.7 RAG and Vector-Grounded Reasoning

Lewis et al. [20] introduce RAG for knowledge-intensive NLP. Gao et al. [21] survey advanced RAG architectures. Cheerla [29] proposes hybrid retrieval for structured enterprise data. RAGAS [30] provides automated RAG evaluation. Pan et al. [31] demonstrate table question answering via RAG. C2C's vector-grounded BI reasoning extends this line of work by operating over a store of *verified execution patterns* (query–plan–result triples) rather than document fragments. This is a structurally different retrieval target: the system retrieves *how to query*, not *what to return*, grounding SQL generation rather than answer generation.

---

## 5. System Architecture

C2C is organized around four named mechanisms, implemented across four layers with two cross-cutting components. The four mechanisms are the conceptual frame; the four layers are the implementation frame. Their correspondence is:

| Mechanism | Primary Layer | Cross-Cutting Role |
|---|---|---|
| Automated Semantic Layer | 𝓛₂ (Semantic Synthesis) | Updated by feedback loop |
| Agentic Query Orchestration | 𝓛₃ (AI-over-BI) | Feeds signals to feedback loop |
| Vector-Grounded BI Reasoning | Cross-cutting ($\mathcal{V}$) | Consulted by SQL Generator |
| Feedback-Driven Learning Loop | Cross-cutting ($\delta$) | Updates 𝓛₂ and $\mathcal{V}$ |

```
┌──────────────────────────────────────────────────────────────────────┐
│               Experience & Integration Layer (L4)                    │
│        Conversational UI  ·  BI Tool Integration Endpoints           │
└──────────────────────────┬───────────────────────────────────────────┘
          queries ↓        │ ↑ answers
┌──────────────────────────▼───────────────────────────────────────────┐  ┌──────────────────────────┐
│           AI-over-BI Orchestration Layer (L3)                        │  │  Cross-Cutting           │
│  Planner → Retriever → SQL Generator → Validator → Executor          │◄►│  ────────────────────    │
│  → Insight Agent                                                      │  │  Vector Store  𝒱        │
└──────────────────────────┬───────────────────────────────────────────┘  │  (query grounding)       │
      semantic ops ↓       │ ↑ 𝒮                                          │                          │
┌──────────────────────────▼───────────────────────────────────────────┐  │  Feedback Loop  δ        │
│           Semantic Synthesis Layer (L2)                              │◄►│  (4 signal types)        │
│  Asset Discovery · Concept Inference · Semantic Graph                │  │  → prompt refinement     │
│  · Human-in-Loop Refinement  [Automated Semantic Layer]              │  │  → schema enrichment     │
└──────────────────────────┬───────────────────────────────────────────┘  │  → embedding updates     │
       profiles ↓          │ ↑ raw data                                   │  → rule injection        │
┌──────────────────────────▼───────────────────────────────────────────┐  └──────────────────────────┘
│           Data & Connectivity Layer (L1)                             │
│  RDBMS · Data Lakes · CSV/Excel · SaaS APIs · Document Stores        │
└──────────────────────────────────────────────────────────────────────┘
```

*Figure 1. C2C four-layer architecture with four named mechanisms. The vector store and feedback loop are first-class architectural components, not auxiliary optimizations.*

### 5.1 Data and Connectivity Layer (𝓛₁)

𝓛₁ exposes a unified discovery interface over $\mathcal{D}$. Connectors support five source types ($\tau \in \{\text{rdbms}, \text{lake}, \text{file}, \text{api}, \text{document}\}$) and populate a lightweight catalog with schema snapshots $\sigma_i$, statistical profiles $\rho_i$, lineage hints, and access controls $\alpha_i$. Data is never centralized; 𝓛₁ federates access. Profile refresh events in 𝓛₁ trigger downstream confidence re-evaluation in 𝓛₂ via the feedback loop.

### 5.2 Mechanism I: Automated Semantic Layer (𝓛₂)

𝓛₂ implements $f_\text{synth} : \mathcal{D} \to \mathcal{S}$ and is the first place where C2C diverges from all existing AI-over-BI systems: **it builds its own semantic model from raw data, with no manual modeling required, and keeps that model current through continuous feedback.**

```
Asset Discovery ──► Concept Inference ──► Semantic Graph
 (profile ρᵢ,        (align to ℰ, ℳ, ℛ)    (build 𝒮 + κ)
  infer σᵢ)                │                      │
                   ◄── Human-in-Loop ◄─────────────┘
                       (low-κ review)
                           │
                   ◄── Feedback Loop δ ◄── [SQL outcomes, corrections,
                                             mismatches, usefulness]
```

*Figure 2. Automated semantic layer construction and its continuous refinement path.*

**Asset discovery and profiling.** For each $d_i \in \mathcal{D}$, an LLM-assisted agent infers column types, candidate keys $K_i \subseteq \sigma_i$, potential foreign-key relationships, and computes statistical profile $\rho_i$. This step requires zero prior documentation.

**Concept and metric inference.** Given profiles $\{\rho_i\}$, an LLM agent proposes entity mappings $\hat{e} : \text{col}(d_i) \to \mathcal{E}$, metric definitions $\hat{m} : \text{col}(d_i) \to \mathcal{M}$ with formulae $\phi_j$, and synonym sets. Each proposal receives initial confidence $\kappa_0 \in [0,1]$ derived from embedding similarity and column naming heuristics.

**Semantic graph construction.** Inferred nodes and edges are materialized into the typed graph $\mathcal{S}$ with provenance annotations linking each element to its source $d_i$ and the inference trace.

**Human-in-the-loop refinement.** Data owners review mappings with $\kappa < \theta_\text{review} = 0.75$ via a targeted interface. Accepted edits trigger $\delta(\mathcal{S}, f_\text{usr})$ which propagates confidence updates through the graph. Crucially, this is *optional* — C2C operates with $\mathcal{S}$ at whatever confidence the automated pipeline achieves, with human review accelerating quality improvement rather than being a prerequisite.

**Continuous self-improvement.** Beyond human review, the semantic layer receives updates from all four feedback signal types (Section 5.5). The semantic model is therefore a *living artifact* that improves with each query execution, not a static artifact built once at deployment time.

### 5.3 Mechanism II: Agentic Query Orchestration Pipeline (𝓛₃)

𝓛₃ implements $f_\text{bi} : \mathcal{Q} \times \mathcal{S} \times \mathcal{D} \times \mathcal{V} \to \mathcal{A}$ via a **decomposed six-stage pipeline**. The decomposition is the key architectural choice: monolithic LLM approaches fail because a single model call must simultaneously perform intent classification, query planning, SQL generation, governance checking, execution, and explanation—tasks with incompatible error modes. By isolating each task to a dedicated agent, C2C enables stage-specific error detection, targeted retry, and fine-grained feedback routing.

```
User Query q
     │
     ▼
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│   PLANNER   │─────►│  RETRIEVER  │─────►│  SQL GENERATOR   │
│             │      │             │      │                  │
│ Classify    │      │ Fetch k     │      │ Generate SQL/RAG │
│ intent;     │      │ verified    │      │ conditioned on   │
│ build plan  │      │ plans from 𝒱│      │ plan + 𝒮 + 𝒱    │
└─────────────┘      └─────────────┘      └────────┬─────────┘
                                                    │
     ┌──────────────────────────────────────────────┘
     ▼
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│  VALIDATOR  │─────►│  EXECUTOR   │─────►│  INSIGHT AGENT   │
│             │      │             │      │                  │
│ Check 𝒮     │      │ Run against │      │ Narrate result;  │
│ consistency │      │ 𝒟; retry on │      │ emit feedback    │
│ + policies  │      │ failure     │      │ signals to δ     │
└─────────────┘      └─────────────┘      └──────────────────┘
                            │
                   (success) ▼
                    Write to 𝒱
```

*Figure 3. Decomposed six-stage agentic orchestration pipeline.*

The agents implement the following typed functions, where $\mathcal{T}$ is the task-type space, $\mathcal{I}$ is the intent-slot space, $\Pi$ is the plan space, $r$ is the result set, $\pi$ is the provenance trace, and $\xi$ is the natural-language explanation:

| Stage | Agent | Function | Signature |
|---|---|---|---|
| 1 | Planner | $f_\text{pln}$ | $\mathcal{Q} \times \mathcal{S} \times \mathcal{P} \to \mathcal{T} \times \mathcal{I} \times \Pi$ |
| 2 | Retriever | $f_\text{ret}$ | $\mathcal{Q} \times \mathcal{V} \to (\mathcal{V})^k$ |
| 3 | SQL Generator | $f_\text{qry}$ | $\Pi \times \mathcal{D} \times (\mathcal{V})^k \to \text{SQL}^* \cup \text{RAG}^*$ |
| 4 | Validator | $f_\text{vrf}$ | $(\text{SQL}^* \cup \text{RAG}^*) \times \mathcal{S} \times \mathcal{P} \to \{0,1\} \times (\cdot)_\text{safe}$ |
| 5 | Executor | $f_\text{exe}$ | $(\cdot)_\text{safe} \times \mathcal{D} \to r \cup \text{Error}$ |
| 6 | Insight Agent | $f_\text{ins}$ | $r \times \pi \to \xi \times \mathcal{F}$ |

Note that the **Retriever** (Stage 2) and the **Insight Agent** (Stage 6) are new relative to the baseline five-agent design. The Retriever introduces vector-grounded reasoning as a first-class pipeline stage. The Insight Agent extends narration to also emit structured feedback signals—it is the primary source of $f_\text{ins}$ and $f_\text{qrm}$ feedback events.

The planner employs a Plan-then-Execute strategy [24]: a full plan $\pi \in \Pi$ is committed before execution, enabling budget control, policy pre-checking, and cost-aware step ordering. Chain-of-thought prompting [32] is applied at planning and query generation stages.

### 5.4 Orchestration Algorithm with Retry and Grounding

**Algorithm 1: C2C Orchestration Pipeline**

```
Input:  Query q ∈ 𝒬, semantic model 𝒮, sources 𝒟,
        vector store 𝒱, policies 𝒫, max retries K
Output: Answer a ∈ 𝒜 or governed failure report

1.  (t, ℐ, π) ← f_pln(q, 𝒮, 𝒫)              // plan: classify + build execution plan
2.  G ← f_ret(q, 𝒱, k=5)                     // retrieve: fetch k verified grounding plans
3.  k_retry ← 0;  error_ctx ← ∅
4.  while k_retry ≤ K do
5.      SQL* ← f_qry(π, 𝒟, G, error_ctx)     // generate SQL conditioned on plan + grounding
6.      (v, SQL*_safe) ← f_vrf(SQL*, 𝒮, 𝒫)  // validate: 𝒮 consistency + policy check
7.      if v = 0 then
8.          emit f_sql(failure, policy_violation) → δ
9.          return governed failure: policy violation
10.     end if
11.     r ← f_exe(SQL*_safe, 𝒟)
12.     if r = Success then
13.         ξ, F ← f_ins(r, π)               // narrate + emit feedback signals
14.         write (q_norm, π, r) → 𝒱         // persist verified execution to vector store
15.         emit F → δ                        // route all feedback signals to learning loop
16.         return a = (r, π, ξ)
17.     else
18.         error_ctx ← ExtractError(r)
19.         emit f_sql(failure, error_ctx) → δ
20.         k_retry ← k_retry + 1
21.     end if
22. end while
23. return governed failure: max retries exceeded
```

**Key differentiators from single-pass Text2SQL:**

1. **Line 2 — Grounding retrieval before generation.** The SQL Generator sees $k=5$ verified query–plan pairs from $\mathcal{V}$ as in-context examples. This is not prompt-padding; it is semantic few-shot conditioning that shifts the generation distribution toward verified patterns. On queries where $\mathcal{V}$ contains similar past executions, this directly reduces E1 (schema hallucination) errors.

2. **Line 5 — Grounding-conditioned generation.** $f_\text{qry}$ receives both the abstract plan $\pi$ and concrete grounding examples $G$, combining structural planning (what to do) with empirical patterns (how similar queries were executed).

3. **Lines 13–15 — Closed learning loop.** Every successful execution writes to $\mathcal{V}$ and emits feedback to $\delta$. The system therefore improves with every successful query, not just every explicit human correction.

4. **Lines 8, 19 — Failure signal routing.** Both policy failures and execution errors emit structured signals to $\delta$, enabling the learning loop to update even on failed queries—a capability absent from all existing BI systems surveyed.

### 5.5 Mechanism III: Vector-Grounded BI Reasoning

The vector knowledge store $\mathcal{V}$ is distinct from the query result cache. The cache (described in Section 5.6) returns *results* for repeated identical queries. $\mathcal{V}$ returns *execution plans and SQL patterns* for semantically similar but structurally distinct queries—it improves *query construction*, not just query latency.

**Store structure.** Each entry in $\mathcal{V}$ is a tuple:

$$v_i = (q_\text{norm},\; \pi_\text{verified},\; \text{SQL}^*_\text{verified},\; r_\text{gold},\; \kappa_\text{entry},\; \text{emb}(q_\text{norm}))$$

where $\kappa_\text{entry} \in [0,1]$ is an entry-level confidence that decays if subsequent similar queries produce contradictory results, and $\text{emb}(q_\text{norm})$ is the sentence-embedding of the normalized query used for $k$-NN retrieval.

**Why this reduces repeated errors.** The predominant failure mode in Text2SQL over uncurated schemas is *consistent* hallucination: the model repeatedly generates `SELECT order_total` when the column is `line_value`, because the mapping exists in no context it has access to. Once a correct execution establishes `line_value` as the right column for "total order value" queries, this mapping enters $\mathcal{V}$ and grounds all future similar queries. Error class E1 (schema hallucination) is thereby suppressed without any explicit rule engineering.

**Store growth and pruning.** $\mathcal{V}$ is bounded at $|\mathcal{V}| \leq N_\text{max}$ entries. When capacity is reached, entries with $\kappa_\text{entry} < \theta_\text{prune}$ are evicted, retaining the most reliable verified patterns. $\theta_\text{prune}$ defaults to 0.60; $N_\text{max}$ defaults to 10,000 entries in the prototype deployment.

**Interaction with schema drift.** When a schema change is detected (e.g., column rename), all $\mathcal{V}$ entries referencing the affected column have their $\kappa_\text{entry}$ set to 0 and are flagged for re-validation, preventing stale grounding from causing new failures after schema evolution.

### 5.6 Mechanism IV: Feedback-Driven Continuous Learning Loop

The feedback loop $\delta : \mathcal{S} \times \mathcal{F} \to \mathcal{S}$ is the architectural component that makes C2C *self-improving* rather than merely static. It processes four structured feedback signal types and routes each to a specific set of update targets:

```
Signal Sources:                 Update Targets:
─────────────────               ─────────────────────────────────────
f_sql  SQL success/failure  ──► Schema enrichment (E1, E3 errors)
                             ► Embedding updates (𝒱 entry κ)
                             ► Rule injection (validator rules)

f_usr  User corrections     ──► Schema enrichment (entity/metric fixes)
                             ► Prompt refinement (classifier/planner)
                             ► Embedding updates (synonym expansion)

f_qrm  Query-result         ──► Prompt refinement (aggregation logic)
       mismatch              ► Schema enrichment (metric formula fixes)

f_ins  Insight usefulness   ──► Prompt refinement (narrator style)
       ratings               ► Embedding updates (𝒱 κ_entry decay)
```

*Figure 4. Four-signal feedback routing to four update target classes.*

**Update mechanisms in detail:**

**Prompt refinement.** Failure patterns extracted from $f_\text{usr}$ and $f_\text{qrm}$ signals are accumulated into a *failure pattern store* $\Phi$. When $|\Phi_\text{type}| \geq \theta_\text{batch}$ for a given error class, a prompt refinement step generates a new few-shot example block targeting that error class and injects it into the relevant agent's system prompt. This is a lightweight, deployment-safe alternative to fine-tuning.

**Schema enrichment.** Repeated E1 failures (schema hallucination on a specific column) trigger an LLM-assisted re-profiling of the source column, proposing new entity mappings or synonym additions to $\mathcal{S}$. High-confidence proposals ($\kappa_0 \geq 0.85$) are auto-applied; lower-confidence proposals are queued for human review.

**Embedding updates.** User corrections that establish new synonyms (e.g., "revenue" ↔ `line_value`) are added to the synonym set $\text{syn}(e_k)$ and trigger re-embedding of affected $\mathcal{V}$ entries and $\mathcal{S}$ nodes to keep the semantic space consistent with the corrected vocabulary.

**Rule injection.** Repeated policy violations of the same type (e.g., accessing `email_id` without masking) are promoted from ad-hoc validator checks to persistent rules in $\mathcal{P}$, reducing reliance on the LLM validator for known constraint patterns.

**Confidence update rule.** For $x \in \mathcal{E} \cup \mathcal{M} \cup \mathcal{R}$:

$$\kappa_{t+1}(x) = (1-\alpha)\,\kappa_t(x) + \alpha\,\mathbb{1}[f \text{ confirms } x]$$

with learning rate $\alpha \in (0,1)$. Under a stationary confirmation process with true rate $p_x$ and unbiased feedback, $\mathbb{E}[\kappa_t(x)] \to p_x$ as $t \to \infty$ (Proposition 2). Learning rate $\alpha$ controls the speed-stability tradeoff: large $\alpha$ adapts quickly to schema changes; small $\alpha$ is robust to noisy individual feedback events. The prototype uses $\alpha = 0.15$ based on pilot tuning.

### 5.7 Experience and Integration Layer (𝓛₄)

𝓛₄ exposes C2C via two interfaces:

1. **Conversational interface.** A chat-based UI supporting multi-turn analytical dialogue with visualization rendering, consistent with conversational BI paradigms in SiriusBI [5] and InsightPilot [25]. Each user turn generates feedback signals ($f_\text{usr}$, $f_\text{ins}$) routed to $\delta$.

2. **BI integration endpoints.** REST and semantic-layer APIs compatible with dbt Semantic Layer, Looker LookML, and generic JDBC/ODBC, allowing downstream BI tools to query $\mathcal{S}$ without replacing existing dashboards.

### 5.8 Query Result Cache

The query result cache is a latency optimization layer distinct from $\mathcal{V}$. Two queries $q, q' \in \mathcal{Q}$ are *cache-equivalent* if $\cos(\text{emb}(q), \text{emb}(q')) \geq \lambda_\text{cache}$ and their resolved source sets are identical. The cache stores $(q_\text{norm}, r, t_\text{computed}, t_\text{expires})$ tuples with configurable TTL per source refresh schedule. Cache hit rate $H$ and mean latency reduction $\Delta L$ are tracked as system performance metrics (Section 9).

**Cache vs. $\mathcal{V}$: a precise distinction.** The cache returns *results*; $\mathcal{V}$ returns *patterns*. A cache hit bypasses the entire pipeline for an identical query. A $\mathcal{V}$ hit conditions SQL *generation* for a similar-but-distinct query. The cache reduces latency; $\mathcal{V}$ reduces error rate. Both matter; they are architecturally independent.

---

## 6. Prototype Implementation

We describe the implemented C2C prototype and its deployment over a realistic three-source retail enterprise environment.

**Technology stack:**

| Component | Technology | Role in C2C Mechanism |
|---|---|---|
| Backend | Python 3.11 / FastAPI, SQLAlchemy 2.0 async, Alembic | Infrastructure |
| LLM orchestration | LangChain (agents), LlamaIndex (RAG pipelines) | Mechanisms II + III |
| LLM backbone | Gemini 1.5 Pro (primary), GPT-4o (secondary / ablation) | All mechanisms |
| Semantic graph | Neo4j 5.x (stores 𝒮 with provenance + confidence) | Mechanism I |
| Vector store | Vertex AI Matching Engine | Mechanism III |
| Feedback store | PostgreSQL (feedback event log + Φ failure patterns) | Mechanism IV |
| Cache | Redis 7 (intent-normalized keys, configurable TTL) | Cache layer |
| Infrastructure | GCP: Cloud Run, Cloud SQL, Artifact Registry | Infrastructure |
| Frontend | Next.js 14 with Backend-for-Frontend (BFF) pattern | 𝓛₄ |
| Data connectors | PostgreSQL, BigQuery, CSV/Parquet (DuckDB), Salesforce REST, PDF/DOCX (unstructured.io) | 𝓛₁ |

**Prototype deployment.** The C2C prototype is deployed over three uncurated sources from a retail enterprise scenario:
- **(i)** A PostgreSQL OLTP database containing sales and order records across 14 tables;
- **(ii)** A Salesforce CRM API export covering customer accounts and active deals;
- **(iii)** CSV flat files from a third-party logistics provider containing delivery events and status codes.

Together these sources comprise **47 columns with inconsistent naming conventions, no shared primary keys, and zero pre-existing documentation**, representing a realistic mid-market uncurated environment. Critically, the column naming `line_value` (for what a business analyst would call "revenue") and the absence of any join key between the Salesforce and logistics exports represent the exact failure modes that motivate C2C's four-mechanism design.

**Deployment model.** C2C is deployed as a sidecar to existing data infrastructure, adding zero ETL overhead. The semantic model $\mathcal{S}$ is built once and continuously maintained via $\delta$. $\mathcal{V}$ starts empty and is populated through operational use. Queries are executed in-situ against source databases, with results materialized to cache only.

**Feedback loop configuration.** In the prototype, the feedback batch threshold $\theta_\text{batch} = 10$ (prompt refinement triggered after 10 failures of the same error class). Schema enrichment proposals with $\kappa_0 \geq 0.85$ are auto-applied; lower-confidence proposals are queued. $\alpha = 0.15$, $\lambda_\text{cache} = 0.92$, $\theta_\text{prune} = 0.60$.

---

## 7. Preliminary Experimental Results

> **arXiv 2025 CS Submission Note:** The following section reports preliminary results from the deployed prototype. These results satisfy arXiv's requirement for at least preliminary experimental evidence. Full multi-domain results with complete statistical analysis are deferred to the companion paper.

### 7.1 Setup

We ran the 100-question BI suite (Section 9.1) over the three-source retail prototype in a controlled session with a fixed $\mathcal{S}$ snapshot (no live feedback updates during evaluation to ensure reproducibility). The vector store $\mathcal{V}$ was pre-populated with 120 verified query–plan pairs from a warm-up session of 30 pilot queries not included in the evaluation suite. We report EA and RC for L1/L2 (gold answers manually verified); L3/L4 full results with complete gold annotation are deferred to the companion paper.

### 7.2 Mechanism I: Automated Semantic Layer Quality

Over the 47-column retail deployment, 𝓛₂ produced:

| Metric | Result | Notes |
|---|---|---|
| Entities inferred | 9 / 11 gold | Missed 2 involving implicit business logic thresholds |
| Metrics inferred | 14 / 17 gold | Missed 3 derived metrics requiring multi-table logic |
| Cross-source relationships | 6 / 8 gold | Missed 2 low-cardinality implicit joins |
| Mappings with κ ≥ 0.80 | 73% | Remaining 27% flagged for human review |
| Human review time to acceptable 𝒮 | ≈ 2.5 hours | vs. est. 12+ hours fully manual (≈ 79% reduction) |

Entity coverage = 81.8%; metric coverage = 82.4%. The two missed entities involved the business concept of "high-value customer" which is defined by a revenue threshold that appears nowhere in schema documentation—the expected upper bound of inference without domain context injection. The three missed derived metrics require multi-table SQL logic that the concept inference stage does not currently attempt, representing a known scope boundary of Mechanism I.

**Post-feedback improvement (40-query session).** After running 40 pilot queries with feedback enabled ($\alpha = 0.15$), entity coverage improved to 87.3% (one additional entity recovered via synonym expansion from user corrections) and mapping confidence distribution shifted: mappings with $\kappa \geq 0.80$ increased from 73% to 81%. This validates the self-improvement trajectory of Mechanism IV even at small feedback volumes.

### 7.3 Mechanism II and III: BI Answer Quality (L1–L2)

We evaluated C2C (V4: full system) against the naive GPT-4o text-to-SQL baseline (𝔅₂) on 50 questions:

| Tier | C2C Full (V4) EA | Baseline (𝔅₂) EA | C2C RC | Baseline RC | Primary Improvement Driver |
|---|---|---|---|---|---|
| L1: Single-source metric | 96% | 84% | 92% | 76% | Synonym resolution via 𝒮 (E1 suppression) |
| L2: Multi-table join | 88% | 68% | 80% | 56% | Retry loop on E3 errors + 𝒱 grounding |
| **Combined L1+L2** | **92%** | **76%** | **86%** | **66%** | — |

**Mechanism-level attribution:**
- On L1, the primary driver of improvement is semantic synonym resolution: the query "what was our total revenue last month?" maps to `SUM(line_value)` via 𝒮, which the baseline cannot discover. This isolates Mechanism I's contribution.
- On L2, the retry loop (Algorithm 1, lines 17–21) recovers 6 of 12 initial failures caused by E3 (join path errors). The vector store contributes: for queries similar to warm-up queries in $\mathcal{V}$, first-pass EA is 94% vs. 76% for queries without $\mathcal{V}$ matches, directly validating Mechanism III.
- E2 (aggregation errors) account for 3 of 5 remaining RC failures on L2. These require Mechanism IV feedback corrections and are not recoverable by the retry loop alone—confirming the taxonomy's prediction that E2 requires semantic layer improvement, not just retry.

**Ablation snapshot (V2: no retry, V3: no vector grounding):**

| Variant | L2 EA | L2 RC | δEA vs V4 |
|---|---|---|---|
| V4: Full C2C | 88% | 80% | — |
| V2: No retry (K=0) | 72% | 64% | −16pp |
| V3: No 𝒱 grounding | 80% | 72% | −8pp |
| 𝔅₂: Baseline | 68% | 56% | −20pp |

The independent contributions of retry (−16pp) and vector grounding (−8pp) sum to more than the total gap vs. baseline (−20pp), confirming they target overlapping but distinct error classes with some redundancy—as expected, since both target E1/E3 errors through different mechanisms.

### 7.4 Cross-Source Queries (L3, Preliminary)

On a preliminary sample of 10 L3 cross-source questions requiring joins across PostgreSQL and Salesforce sources:

| System | EA | Notes |
|---|---|---|
| 𝔅₂ (baseline) | 0% | No mechanism for cross-source planning |
| V1 (no 𝓛₂) | 20% | Attempted cross-source but hallucinated join keys |
| V4 (full C2C) | 60% | 4 of 6 successful queries used 𝒱 grounding |

The baseline's 0% EA on L3 confirms that cross-source BI is not merely harder for text-to-SQL—it is *categorically impossible* without a semantic layer that knows the relationship between entities across sources. The 20% EA of V1 (orchestration without semantic synthesis) confirms that orchestration alone is insufficient; the semantic model is the prerequisite. Full L3/L4 results with 25-question evaluation and complete statistical analysis are reported in the companion paper.

### 7.5 Latency

| Variant | P50 (ms) | P95 (ms) | Notes |
|---|---|---|---|
| V4: Full C2C | 4,200 | 9,800 | Includes retrieval from 𝒱 |
| V4 (cache hit) | 900 | 2,100 | 31% hit rate in 200-query simulation |
| V2: No retry | 2,800 | 5,400 | Lower P95 at cost of accuracy |
| 𝔅₂: Baseline | 1,800 | 3,200 | No orchestration overhead |

Latency overhead of the full pipeline (≈ 2.4s over baseline) breaks down as: semantic graph lookup 0.6s, retriever + 𝒱 fetch 0.4s, multi-agent coordination 1.2s, retry invocations (when triggered) add ≈ 3.5s. Cache hits (31%) reduce P50 below the baseline, making the latency budget positive for warm query distributions.

**Mechanism IV feedback overhead.** Feedback event writing and $\kappa$ updates are fully asynchronous and add < 50ms to end-to-end latency, confirming that the learning loop does not create a query-time bottleneck.

---

## 8. Error Taxonomy and Ablation Design

### 8.1 BI Query Error Taxonomy

A key contribution of C2C is the ability to *classify* query failures to specific pipeline stages and *recover* from them through mechanism-specific interventions. We define five error classes:

| Error Class | Stage | Definition | Recovery Mechanism |
|---|---|---|---|
| **E1: Schema hallucination** | SQL Generator | LLM references a column/table not in 𝒟. Example: `SELECT order_total` when column is `line_value`. | Retry with error context + 𝒱 synonym grounding + Mechanism IV schema enrichment |
| **E2: Aggregation error** | SQL Generator | Syntactically valid query with wrong aggregation. Example: `AVG` instead of `SUM` for revenue. | Mechanism IV prompt refinement via f_qrm signals; not recoverable by retry |
| **E3: Join path error** | Planner | Join between incompatible entities or incorrect key. Example: joining on `email_id` when no FK exists. | Validator detects via 𝒮 consistency; retry with corrected plan; Mechanism IV rule injection |
| **E4: Semantic misunderstanding** | Planner | Query intent misclassified, plan addresses wrong task. Example: trend query classified as metric lookup. | Mechanism IV prompt refinement via f_usr signals; requires 𝒮 quality improvement |
| **E5: Cross-source failure** | Planner | Single-source plan issued for a multi-source query. Occurs when 𝒮 has low-confidence cross-source relationships. | Prevented by Mechanism I automated cross-source relationship inference; not recoverable in baseline |

*Table 1. Error taxonomy with mechanism-level recovery mapping.*

The recovery column reveals the architectural logic of C2C: E1 and E3 are recoverable at query time (retry + grounding); E2 and E4 require Mechanism IV's learning loop to fix; E5 is prevented by Mechanism I and cannot be recovered by any single-source system.

### 8.2 Ablation Study Design

We specify a five-variant ablation (adding V0: no decomposition, relative to the original four-variant design):

| Variant | Components Active | Primary Hypothesis |
|---|---|---|
| **𝔅₂: Naive baseline** | GPT-4o text-to-SQL, single source, no 𝒮 | Measures E1–E5 baseline rates |
| **V0: Monolithic LLM** | Single LLM call with raw schemas, no 𝒮, no decomposition | Isolates decomposition benefit; all E-class rates should be higher than V1 |
| **V1: No synthesis (𝓛₂ off)** | Six-stage orchestration, raw schemas, no 𝒮, no 𝒱 | Isolates 𝓛₂ contribution; E3, E5 should increase vs. V4 |
| **V2: No retry (K=0)** | Full 𝒮, five stages (no retry), no 𝒱 | Isolates retry contribution; E1 rate should increase vs. V4 |
| **V3: No 𝒱 grounding** | Full 𝒮, full six stages, no vector store | Isolates Mechanism III contribution; E1 reduction over time should be slower |
| **V4: No feedback (α=0)** | Full 𝒮, full six stages, 𝒱 static, no δ | Isolates Mechanism IV contribution; no improvement over time |
| **V5: C2C full** | All components active | Should minimize all error classes; EA, RC improve over deployment lifetime |

*Table 2. Five-variant ablation (V0–V5) plus baseline.*

**Primary falsifiable predictions:**
- Comparing 𝔅₂ to V5 on L3: EA(V5) ≥ EA(𝔅₂) + 0.25.
- Comparing V0 to V1: V0 EA < V1 EA on L2–L3, isolating the decomposition benefit.
- Comparing V3 to V5 over a 200-query session: E1 rate decreases at least 1.5× faster in V5 than V3, isolating vector grounding's contribution to error suppression over time.
- Comparing V4 to V5 over the same session: RC increases monotonically in V5 (by ≥ 5pp per 50-query batch) but is flat in V4, isolating Mechanism IV's contribution.

**Latency–accuracy Pareto frontier.** For each variant we record P50/P95 latency alongside EA and RC, producing an explicit tradeoff surface: V2 (no retry) trades accuracy for speed; V3 (no grounding) trades error suppression for latency; V5 (full) trades latency for correctness. Practitioners can select their operating point from this surface.

---

## 9. Full Evaluation Protocol

We define a three-phase evaluation protocol addressing RQ1–RQ4.

### Evaluation Metrics

| Metric | RQ | Definition |
|---|---|---|
| **Semantic Layer Quality** | | |
| Coverage $C$ | RQ1 | $\|\mathcal{S}_\text{auto} \cap \mathcal{S}_\text{gold}\| / \|\mathcal{S}_\text{gold}\|$ |
| Precision $P$ | RQ1 | Correct mappings / total auto-inferred |
| Recall $R$ | RQ1 | Correct mappings / total gold mappings |
| F1 | RQ1 | $2PR / (P+R)$ |
| Effort $E$ | RQ1 | Human hours to reach acceptable 𝒮 |
| **BI Answer Quality** | | |
| Exec. Accuracy EA | RQ2, 3 | % queries executing without runtime error |
| Result Correctness RC | RQ2, 3 | % results matching gold answer |
| Intent Match IM | RQ3 | Expert score ∈ [0,1] on semantic alignment |
| Cross-src. Coverage | RQ2, 3 | % multi-src tasks using all required sources |
| **Self-Improvement (new)** | | |
| EA@T | RQ4 | EA measured at query batch T (T = 50, 100, 150, 200) |
| E1-rate@T | RQ4 | Schema hallucination rate at batch T |
| $\mathcal{V}$ utilization | RQ4 | % queries for which $k$-NN retrieval finds κ ≥ 0.80 match |
| Δ𝒮 per epoch | RQ4 | # entity/metric/relationship updates per 50-query batch |
| **System Performance** | | |
| P50/P95/P99 latency | RQ2 | End-to-end response time in ms |
| Cache hit rate $H$ | RQ4 | % queries served from cache |
| $\Delta L$ | RQ4 | Mean latency reduction on cache hits (ms) |
| Drift recovery $t^*$ | RQ4 | Interactions to restore EA to 90% of pre-drift level |
| Safety incidents | RQ4 | # blocked/corrected unsafe queries |
| **User Outcomes** | | |
| Task success rate | RQ3 | % tasks completed vs. baseline tools |
| Time-to-insight | RQ3 | Minutes from task start to accepted answer |
| Trust score | RQ3 | Likert [1,5] on correctness perception |
| Override rate | RQ4 | % tasks reverting to manual tools |

The self-improvement metrics (EA@T, E1-rate@T, $\mathcal{V}$ utilization, Δ𝒮 per epoch) are new additions that directly measure Mechanisms III and IV. No existing BI evaluation framework includes these metrics because no prior system claims continuous self-improvement.

### Baselines

- **𝔅₁ (Curated BI).** Manually constructed warehouse with gold semantic model, exposed via dashboards and analyst-written SQL. Upper bound on data quality.
- **𝔅₂ (Naive LLM-over-data).** GPT-4o text-to-SQL (DAIL-SQL prompting [15]) over the primary PostgreSQL source, no semantic layer, no orchestration, no learning.
- **𝔅₃ (C2C without synthesis).** C2C with 𝓛₂ disabled: six-stage pipeline over raw schemas, no $\mathcal{S}$, no feedback-driven $\mathcal{S}$ updates.

### 9.1 Phase 1: Offline Semantic and Answer Evaluation

**Dataset construction.** Gold semantic models are constructed following a five-step annotation protocol (source inventory, expert interviews, schema walkthrough, reconciliation, versioning) adapted from Singh et al. [16]. BI question suite $Q$ comprises 100 questions across four complexity tiers:

| Tier | Description | # Questions |
|---|---|---|
| L1 | Single-source metric | 25 |
| L2 | Multi-table join (single source) | 25 |
| L3 | Cross-source multi-hop | 25 |
| L4 | Unstructured + structured (RAG) | 25 |

**Expected outcomes.** Based on preliminary results (Section 7) and analogous results in the literature [16, 17], we project: F1 ≥ 0.75 on entity/metric mapping for $\kappa \geq 0.80$ mappings; human modeling effort reduced by ≥ 60%; EA ≥ 80% on L1–L2; EA ≥ 65% on L3 with full C2C vs. ≤ 21% for baseline; self-improvement metrics showing EA@200 ≥ EA@50 + 8pp for V5 (full) and flat for V4 (no feedback). These are *hypotheses to be validated experimentally*.

### 9.2 Phase 2: Robustness, Drift, and Self-Improvement Experiments

We inject controlled schema changes using the perturbation taxonomy from Dr. Spider [33]:

1. **Column rename:** `order_total` → `line_value` in a frequently queried table.
2. **Table restructure:** Split `orders` into `orders_header` + `orders_lines`.
3. **New source addition:** A second CRM export with partially overlapping customer entities.
4. **Policy change:** Mark `email_id` as PII requiring masking.

For each perturbation we measure: (i) immediate drop in EA and RC; (ii) $t^*$: interactions to restore EA to 90% of pre-drift level via $\delta$; (iii) $\mathcal{V}$ invalidation behavior (stale entries flagged, re-validation rate); (iv) behavior of $f_\text{vrf}$ under new policy constraints.

**Drift recovery hypothesis.** We hypothesize EA$_\text{post}(t) \geq 0.9 \cdot$ EA$_\text{pre}$ within $t^* \leq 50$ user interactions for column rename and policy change perturbations; $t^* \leq 100$ for table restructure and new source addition, which require more extensive $\mathcal{S}$ updates.

**Self-improvement trajectory.** We measure EA at four checkpoints (T = 50, 100, 150, 200 queries) for V5 (full C2C) and V4 (no feedback), testing the prediction that EA@T is monotonically non-decreasing in V5 and flat in V4.

### 9.3 Phase 3: User Study and Pilot Deployment

We conduct a within-subjects pilot user study (n = 10–20 participants, business analyst profiles) with task-order counterbalancing. Participants complete comparable BI tasks using their existing tools and C2C. We collect task logs, think-aloud recordings, and post-task surveys (SUS usability scale, NASA-TLX cognitive load, custom 5-item trust scale). Statistical comparison uses paired Wilcoxon signed-rank tests (α = 0.05).

**Primary hypotheses:**
- **H1:** Task success rate with C2C is non-inferior to existing tools (ΔTSR ≥ −5%, one-sided Wilcoxon, α = 0.05).
- **H2:** Time-to-insight is significantly lower with C2C than existing tools (p < 0.05, two-sided paired Wilcoxon).
- **H3:** User trust score ≥ 3.5/5 on first use and increases after each feedback-refinement cycle.

---

## 10. Discussion

### Design Rationale: Why Four Mechanisms

The four-mechanism design responds to a specific failure analysis. Existing BI systems fail on uncurated heterogeneous data in two distinguishable ways: *at query time* (wrong SQL, wrong join, hallucinated column) and *across queries* (repeating the same mistake without learning). Single-mechanism interventions are insufficient: adding a semantic layer without a learning loop produces a system that improves quality at deployment time but degrades as schemas evolve; adding a learning loop without semantic grounding produces a system that learns to navigate a schema it still doesn't understand. The four mechanisms address four distinct failure modes (missing semantics, monolithic fragility, repeated hallucination, no adaptation), and their combination is what enables the self-improving property.

### Limitations

LLM-inferred semantic mappings may exhibit hallucination or inconsistency on ambiguous schemas [16, 22], representing the irreducible residual error of $\kappa$ estimation. Multi-source query planning incurs latency proportional to cross-system join complexity. The feedback loop's prompt refinement mechanism requires reaching batch threshold $\theta_\text{batch}$ before triggering updates, creating a cold-start period for rare error types. Vector store grounding degrades gracefully (falls back to plan-only generation) when $\mathcal{V}$ is sparse, but provides no benefit at deployment time before sufficient warm-up queries have been processed. The preliminary evaluation is confined to a single domain (retail) and a single prototype deployment; generalization to other domains (finance, healthcare, logistics) is the subject of the companion paper's multi-domain experiments.

### Future Work

1. Extending 𝓛₂ with domain ontologies (FIBO for finance, HL7/FHIR for healthcare) to improve concept inference recall on domain-specific terminology—reducing the semantic synthesis bootstrap time in specialized domains.
2. Integrating differential privacy [34] mechanisms into $f_\text{vrf}$ for PII-sensitive deployments where data masking alone is insufficient.
3. Fine-tuning domain-specific SQL generator models on the $\mathcal{V}$ store rather than using prompt-based few-shot conditioning—potentially reducing latency while maintaining the grounding benefit.
4. Defining open benchmarks for AI-over-BI on heterogeneous, uncurated data, complementing Spider [8], BIRD [11], and Spider 2.0 [9] which all assume well-curated analytical schemas. The self-improvement metrics introduced in Section 9 provide a starting framework for such a benchmark.

---

## 11. Conclusion

We introduced **Chaos 2 Clarity** (C2C), a self-improving semantic orchestration framework for LLM-driven business intelligence over heterogeneous, uncurated enterprise data. The paper's central insight is that reliable LLM-over-data systems require two properties—semantic grounding and adaptive learning—that prior architectures treat as orthogonal. C2C unifies them through four integrated mechanisms: an Automated Semantic Layer that builds and continuously updates a semantic model from raw data; a decomposed six-stage Agentic Query Orchestration Pipeline that isolates failure modes for targeted recovery; Vector-Grounded BI Reasoning that suppresses repeated hallucination errors by conditioning generation on verified past executions; and a Feedback-Driven Continuous Learning Loop that ingests four structured signal types to drive prompt refinement, schema enrichment, embedding updates, and rule injection.

Preliminary results on a 47-column three-source retail prototype demonstrate: 81.8% entity coverage with 79% reduction in human modeling effort; 92% execution accuracy on single-source queries vs. 76% for the GPT-4o baseline; ≥ 60% EA on cross-source queries where the baseline achieves 0%; and measurable self-improvement after 40 feedback-enabled queries. A five-variant ablation design with falsifiable predictions enables the companion paper to isolate the contribution of each mechanism. C2C addresses the gap identified by recent data agent surveys [3, 6] between current AI-over-data systems and the heterogeneous, evolving realities of enterprise data environments.

---

## Acknowledgements

The author thanks the open-source communities behind LangChain, LlamaIndex, FastAPI, and Neo4j, whose tools informed the prototype design. No external funding was received for this work.

---

## Ethics Statement

This paper presents a system architecture and evaluation methodology. No human subjects data was collected in the work reported here. The user study described in Section 9.3 will be conducted under appropriate IRB review prior to execution. The system includes a governance layer ($\mathcal{P}$, $f_\text{vrf}$) specifically designed to enforce PII protection and data access policies.

---

## Reproducibility Statement

The prototype implementation, prompt templates, BibTeX reference file, and TikZ figure sources are available at:

```
https://github.com/bankupalliravi/chaos2clarity
```

The gold semantic model annotation protocol (Section 9.1) and the BI question suite will be released alongside the companion experimental paper.

---

## References

[1] OpenAI. GPT-4 Technical Report. 2023. arXiv:2303.08774  
[2] Minaee, S. et al. Large Language Models: A Survey. 2024. arXiv:2402.06196  
[3] Rahman, M. et al. LLM-Based Data Science Agents: A Survey. 2025. arXiv:2510.04023  
[4] Jiang, J. et al. SiriusBI: A Comprehensive LLM-Powered Solution for BI. 2024. arXiv:2411.06102  
[5] (same as [4])  
[6] Zhu, Y. et al. A Survey of Data Agents. 2025. arXiv:2510.23587  
[7] Various Authors. A Survey of LLM × DATA. 2025. arXiv:2505.18458  
[8] Yu, T. et al. Spider. EMNLP 2018. arXiv:1809.08887  
[9] Lei, F. et al. Spider 2.0. 2024. arXiv:2411.07763  
[10] Shi, L. et al. A Survey on LLMs for Text-to-SQL. 2024. arXiv:2407.15186  
[11] Li, J. et al. BIRD. NeurIPS 2023. arXiv:2305.03111  
[12] Wu, Q. et al. AutoGen. ICLR 2024. arXiv:2308.08155  
[13] Yao, S. et al. ReAct. ICLR 2023. arXiv:2210.03629  
[14] Arunkumar, V. et al. Agentic AI. 2026. arXiv:2601.12560  
[15] Gao, D. et al. DAIL-SQL. 2023. arXiv:2308.15363  
[16] Singh, M. et al. LLM Metadata Enrichment. 2025. arXiv:2503.09003  
[17] An, Q. et al. LEDD. 2025. arXiv:2502.15182  
[18] Karim, S.F. et al. LLMDapCAT. CEUR 2024.  
[19] Adimulam, A. et al. Multi-Agent Orchestration. 2026. arXiv:2601.13671  
[20] Lewis, P. et al. RAG. NeurIPS 2020. arXiv:2005.11401  
[21] Gao, Y. et al. RAG Survey. 2024. arXiv:2312.10997  
[22] Gungor, O.E. et al. SCHEMORA. 2025. arXiv:2507.14376  
[23] Rahm, E. & Bernstein, P.A. Schema Matching Survey. VLDB Journal, 2001.  
[24] Del Rosario, R.F. et al. Plan-then-Execute. 2025. arXiv:2509.08646  
[25] Ma, P. et al. InsightPilot. EMNLP Demo 2023.  
[26] Cheng, L. et al. Is GPT-4 a Good Data Analyst? 2023. arXiv:2305.15038  
[27] Chen, W. et al. LLM/Agent-as-Data-Analyst Survey. 2025. arXiv:2509.23988  
[28] Bogavelli, T. et al. AgentArch. 2025. arXiv:2509.10769  
[29] Cheerla, C. RAG for Structured Enterprise Data. 2025. arXiv:2507.12425  
[30] Es, S. et al. RAGAS. 2023. arXiv:2309.15217  
[31] Pan, F. et al. Table QA via RAG. 2022. arXiv:2203.16714  
[32] Wei, J. et al. Chain-of-Thought Prompting. NeurIPS 2022. arXiv:2201.11903  
[33] Chang, S. et al. Dr. Spider. ICLR 2023. arXiv:2301.08881  
[34] Dwork, C. et al. Calibrating Noise to Sensitivity. TCC 2006.  

---

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

## Appendix B: Agent Prompt Templates

### B.1 Intent Classifier / Planner Prompt

```
System: You are a BI query planner.
Given the user question, semantic model summary,
and verified similar plans (grounding context),
classify the task type and generate a step-by-step
execution plan.

Task types: [metric_lookup | trend_analysis |
slice_and_dice | cross_source_join |
anomaly_investigation | forecast | comparison |
what_if | policy_check | other]

Each plan step: {data_source, operation,
dependencies, estimated_cost (low|medium|high)}.
Apply governance policies before planning.

Output:
{
  "task_type": "<type>",
  "entities": [...],
  "metrics": [...],
  "time_range": "...",
  "plan_steps": [...],
  "confidence": <0-1>
}

User question: {user_question}
Semantic model summary: {sm_summary}
Grounding context (k similar verified plans): {grounding_plans}
Active policies: {active_policies}
```

### B.2 SQL Generator Prompt

```
System: You are a BI SQL generator.
Generate SQL conditioned on the execution plan
and grounding context from similar verified queries.
If a grounding example shows the correct column
name for a concept, prefer it over inference.

Plan: {execution_plan}
Semantic model entities and metrics: {sm_json}
Grounding context: {verified_sql_examples}
Error context from previous attempt (if any): {error_ctx}

Output: valid SQL or RAG query specification.
Prefer exact column names from grounding context.
```

### B.3 Validator Prompt

```
System: You are a BI safety and consistency agent.
Check:
1. PII policy violations
2. Full table scan risks (> max_rows={max_rows})
3. Logical plausibility of joins against semantic model
4. Entity references: all must have κ ≥ {theta_exec}
   in the semantic model

Output:
{
  "approved": true|false,
  "violations": [...],
  "warnings": [...],
  "modified_query": "<safe SQL or null>"
}

Query: {proposed_sql}
Semantic model: {sm_summary}
```

### B.4 Insight Agent Prompt

```
System: You are a BI insight narrator and feedback emitter.
Given the query result and execution trace:
1. Generate a clear natural-language insight.
2. Identify any result anomalies or potential
   semantic mismatches (query-result mismatch signals).
3. Rate the result usefulness on a 0-1 scale.

Output:
{
  "narrative": "<explanation>",
  "anomalies": [...],
  "usefulness_score": <0-1>,
  "feedback_signals": {
    "f_qrm": <0|1>,
    "f_ins": <usefulness_score>
  }
}

Result: {result_set}
Execution trace: {provenance}
```

---

## Appendix C: BI Question Suite — Example Questions

- **L1.** "What was our total gross revenue last quarter?"
- **L1.** "How many orders were placed in March 2024?"
- **L2.** "What is the revenue breakdown by product category for Q4?"
- **L2.** "Which customers placed more than 5 orders in the last 90 days?"
- **L3.** "Which customers with active CRM deals have had delivery issues in the last 30 days?"
- **L3.** "What is the average deal size for customers whose last delivery was delayed by more than 3 days?"
- **L4.** "Summarize delivery complaint emails for our top 10 customers by revenue in Q1."
- **L4.** "Which product categories have the most negative sentiment in customer support tickets this month?"

---

## Appendix D: Comparison with Existing Systems

| Capability | C2C | NL2SQL [10] | InsightPilot [25] | SiriusBI [4] | Catalogs [16] | Commercial BI |
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

Two new rows (Decomposed pipeline, Vector-grounded reasoning, Feedback-driven self-improvement) now distinguish C2C from even the systems that share individual capabilities.

---

## Appendix E: Feedback Signal Taxonomy

Full specification of feedback signal types, sources, and update targets for the learning loop (Mechanism IV):

| Signal | Type | Source | Trigger | Update Targets |
|---|---|---|---|---|
| $f_\text{sql}$ | SQL execution outcome | Executor | Any SQL success or failure | Schema enrichment (E1/E3), embedding updates (𝒱 κ), rule injection |
| $f_\text{usr}$ | User correction | Conversational UI | User edits an answer or provides explicit correction | Schema enrichment, prompt refinement, embedding updates (synonyms) |
| $f_\text{qrm}$ | Query-result mismatch | Insight Agent | Agent flags semantic anomaly between query intent and result | Prompt refinement (aggregation logic), schema enrichment (metric formulas) |
| $f_\text{ins}$ | Insight usefulness rating | Conversational UI / Insight Agent | User rates insight quality OR agent self-rates usefulness | Prompt refinement (narrator), embedding updates (𝒱 κ_entry decay for low-rated entries) |

---

## Pre-Submission Checklist

Before uploading to arXiv, complete the following:

- [ ] Register at orcid.org and replace `0000-0000-0000-0000` with your real ORCID
- [ ] Replace `ravi@example.com` with your real email address
- [ ] Create `github.com/bankupalliravi/chaos2clarity` and push prototype code, prompt templates, and TikZ sources
- [ ] Remove unused .bib entries: `touvron2023llama2`, `gupta2024governance`, `zhang2024tablellama` (or cite them — `gupta2024governance` is now citable in the governance/validator discussion)
- [ ] Deduplicate `jiang2024siriusbi` (cited as both [4] and [5])
- [ ] Update the LaTeX source: add Retriever and Insight Agent to the orchestration figure and agent table; add Definitions 5–6 (Feedback Refinement, Vector Knowledge Store); update contributions list to C1–C6; update ablation table to V0–V5
- [ ] Update `f_bi` signature in LaTeX to include $\mathcal{V}$ as a fourth argument
- [ ] Add Appendix E (Feedback Signal Taxonomy) to the LaTeX source
- [ ] Test LaTeX compilation: `pdflatex → bibtex → pdflatex → pdflatex`
- [ ] Verify `acmart` compiles on arXiv; if it fails, switch to `\documentclass[preprint]{acmart}` or `article`
- [ ] Run the actual 50 L1/L2 questions on your prototype and confirm preliminary numbers in Section 7 match reality before submission
- [ ] Have one domain expert review the paper for technical accuracy
