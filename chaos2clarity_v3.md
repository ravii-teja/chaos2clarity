# Chaos 2 Clarity: A Self-Improving Semantic Orchestration Framework for LLM-Driven Business Intelligence over Heterogeneous, Uncurated Enterprise Data

**Bankupalli Ravi Teja**  
Independent Research, Hyderabad, India  
`ravi@[your-real-email].com` · ORCID: `0000-0000-0000-0000` *(register at orcid.org before submission)*

---

> **arXiv submission target:** cs.DB (primary), cs.AI (secondary)  
> **Paper type:** System paper with formal experimental protocol  
> **Status:** Prototype implemented; experimental results to be added upon completion of evaluation runs

---

## Abstract

Existing LLM-based business intelligence (BI) systems fail to generalize across heterogeneous enterprise data sources because they lack two properties that are essential in practice: *semantic grounding* at the data layer and *adaptive learning* at the query layer. Systems that assume a pre-built semantic model break when confronted with uncurated, multi-source environments; systems that learn do not ground their learning in the structure of the data.

We present **Chaos 2 Clarity** (C2C), a self-improving semantic orchestration framework that enables LLMs to generate reliable BI insights over heterogeneous, uncurated enterprise data by combining four tightly integrated mechanisms: **(i)** an **Automated Semantic Layer** that constructs a living semantic model—entities, relationships, metrics, and governance policies—directly from raw data sources without manual modeling, and continuously refines it through feedback; **(ii)** an **Agentic Query Orchestration Pipeline** implementing a decomposed Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent chain that improves reliability over monolithic LLM approaches; **(iii)** a **Vector-Grounded BI Reasoning** subsystem that persists successful query-to-result mappings as grounding context, reducing repeated errors over time; and **(iv)** a **Feedback-Driven Continuous Learning Loop** that closes the improvement cycle by ingesting SQL success/failure signals, user corrections, query-result mismatches, and insight usefulness ratings to drive prompt refinement, schema enrichment, embedding updates, and rule injection.

We formalize the problem, deploy a prototype over a realistic three-source retail environment (PostgreSQL, Salesforce CRM export, logistics CSV — 47 columns, zero pre-existing documentation), define a six-experiment evaluation protocol mapping directly to each architectural claim, and present the evaluation framework awaiting experimental runs.

**Central falsifiable claim:** C2C's self-improving semantic orchestration improves execution accuracy on heterogeneous, multi-source BI workloads by ≥ 25 percentage points over a direct LLM-to-SQL baseline, and enables cross-source queries the baseline cannot execute.

---

## 1. Introduction

Large language models have enabled natural-language interfaces to data and BI, promising to democratize analytics and reduce reliance on specialist data teams [1, 2]. Recent prototypes and commercial systems highlight LLM-powered agents that generate SQL from natural language, build dashboards, and automate analytical workflows [3, 4]. These systems, however, share a structural assumption: that data curation has already been completed upstream, providing a central warehouse with consistent schemas and a manually defined semantic layer encoding business entities, metrics, and relationships.

In practice, many organizations cannot meet these prerequisites. Business-critical data is spread across multiple operational systems; exports and spreadsheets proliferate; SaaS tools hold key fragments of process and customer state; and documentation is sparse or outdated [5, 6]. Benchmarks confirm the severity of this gap: while GPT-4-based agents achieve ≈ 86% execution accuracy on Spider 1.0 [7], performance drops to only 17–21% on Spider 2.0 [8]—which involves enterprise environments with > 3,000 columns, multiple SQL dialects, and cross-database workflows. This collapse in performance traces to two failure modes that existing systems do not simultaneously address: *absent semantic grounding* (the system does not know what the data means across sources) and *no adaptive learning* (the system repeats the same errors without correction) [9, 10].

Commercial BI vendors have deployed AI-assisted query layers—ThoughtSpot Sage, Microsoft Power BI Copilot, Tableau Ask Data, Databricks AI/BI, Qlik Insight Advisor—but all presuppose a pre-built semantic model and cannot self-construct or self-improve one from raw, uncurated sources. Semantic layer tools such as dbt Semantic Layer, Looker LookML, Cube.dev, and AtScale offer structured metric registries but require significant manual modeling effort [11] and provide no feedback-driven refinement. *The automated construction of a semantically grounded, continuously improving BI layer over raw, heterogeneous enterprise data remains an open problem.*

### The Core Insight

Reliable LLM-over-data systems require two properties that today's architectures treat as orthogonal: **semantic grounding** (knowing what data means across sources) and **adaptive learning** (improving from operational experience). C2C unifies these properties in a single architecture through: (a) automated construction of a semantic model from raw data, (b) decomposed query processing through a structured six-stage agent chain rather than a monolithic LLM call, (c) grounding of SQL generation in a vector store of verified query patterns, and (d) continuous tightening of the semantic model via structured feedback signals from every query execution.

### Paper Type and Scope

This paper presents a *system paper with a formal experimental protocol*. We design, implement, and characterize C2C, a working prototype deployed over a realistic three-source retail enterprise scenario. The paper contributes: a formal problem definition, a production-oriented reference architecture with four named mechanisms, a running implementation, a five-class error taxonomy derived from prototype operation, and a six-experiment evaluation protocol with falsifiable predictions. Experimental results will be added upon completion of evaluation runs and reported in full in a companion paper targeting VLDB or SIGMOD.

### Central Falsifiable Claim

*C2C's self-improving semantic orchestration pipeline improves execution accuracy on heterogeneous, multi-source BI workloads by ≥ 25 percentage points over a direct LLM-to-SQL baseline, and enables cross-source queries that the baseline cannot execute at all.*

This claim is operationalized in Section 8 via six experiments, each targeting a specific architectural component.

### Why C2C Is Distinct

**C2C vs. Text2SQL / NL2SQL systems** [9, 7, 12]. These translate natural language to SQL over *a single, pre-specified, clean schema*. C2C begins with no schema assumptions: it *synthesizes* the schema and semantic model from raw, undocumented sources before any SQL is generated. Without semantic synthesis, Text2SQL has nothing to operate on in the uncurated setting. Furthermore, Text2SQL systems do not learn from failures—each query is an independent call. C2C's vector-grounded reasoning and feedback loop mean that a failure on query $q$ makes the system more reliable for semantically similar future queries [13].

**C2C vs. LLM agent frameworks** [14, 15, 16]. General-purpose agent frameworks (ReAct, AutoGen) provide tool-use and orchestration primitives but do not solve data heterogeneity. A ReAct agent given three disparate sources with no shared keys and inconsistent naming will hallucinate joins or fail silently [5], and will repeat the failure on the next similar query. C2C's decomposed six-stage pipeline isolates each failure mode to a specific agent, enabling targeted retry and correction.

**C2C vs. dbt / Looker / Cube.dev semantic layers**. These tools require *engineers to write* metric definitions, join paths, and entity mappings in YAML or LookML [11]. C2C generates this layer automatically from raw sources and improves it continuously from feedback. dbt and Looker are potential *consumers* of C2C's synthesized output, not competitors.

**C2C vs. RAG systems** [17, 18]. Standard RAG pipelines retrieve from unstructured document corpora. C2C's vector-grounded BI reasoning operates over a structured store of verified query–plan–result triples, enabling semantic retrieval of *verified execution patterns* rather than document fragments. This targets a different failure mode: not missing facts, but repeated query construction errors [13].

### Research Gap

No existing production-oriented system simultaneously addresses: (a) automated semantic synthesis over uncurated heterogeneous sources, (b) decomposed multi-agent BI orchestration over the resulting semantic layer, (c) vector-grounded reasoning that reduces repeated query errors over time, and (d) feedback-driven continual self-improvement—all within a governance-aware, deployable architecture [5, 10]. C2C is the first architecture to integrate all four properties.

---

## 2. Formal Problem Definition

**Definition 1 (Data Source).** A *data source* $d_i$ is a tuple $d_i = \langle \tau_i, \sigma_i, \rho_i, \alpha_i \rangle$, where $\tau_i \in \{\text{rdbms}, \text{lake}, \text{file}, \text{api}, \text{document}\}$ is the source type, $\sigma_i$ is the (possibly partial or evolving) schema, $\rho_i$ is the statistical profile (cardinalities, value distributions, null rates), and $\alpha_i$ is the access control specification.

**Definition 2 (Heterogeneous Data Environment).** A *heterogeneous data environment* is a finite set $\mathcal{D} = \{d_1, d_2, \ldots, d_n\}$ of data sources. $\mathcal{D}$ is *uncurated* if: (a) no unified schema or naming convention exists across sources; (b) no formal semantic catalog or metric registry has been manually defined; and (c) documentation is absent or incomplete for ≥ 50% of entities.

**Definition 3 (Semantic Model).** A *semantic model* $\mathcal{S}$ is a typed labeled graph $\mathcal{S} = \langle \mathcal{E}, \mathcal{M}, \mathcal{R}, \mathcal{P}, \kappa \rangle$, where:
- $\mathcal{E} = \{e_1,\ldots,e_p\}$ is a set of *business entities* (e.g., *Customer*, *Product*), each with aliases and source mappings;
- $\mathcal{M} = \{m_1,\ldots,m_q\}$ is a set of *metrics*, each defined by an aggregation formula $\phi_j : \text{Tuples}(\mathcal{D}) \to \mathbb{R}$ and a unit of measurement;
- $\mathcal{R} \subseteq (\mathcal{E} \cup \mathcal{M}) \times \mathcal{L} \times (\mathcal{E} \cup \mathcal{M})$ is a set of typed, labeled relationships (DerivedFrom, SliceableBy, ForeignKey, SynonymousWith);
- $\mathcal{P} = \{p_1,\ldots,p_r\}$ is a set of *governance policies* specifying PII handling, access controls, and compute constraints;
- $\kappa : \mathcal{E} \cup \mathcal{M} \cup \mathcal{R} \to [0,1]$ is a *confidence function* assigning provenance-backed confidence scores to all inferred mappings.

**Definition 4 (Semantic Synthesis).** *Semantic synthesis* is the function $f_\text{synth} : \mathcal{D} \to \mathcal{S}$ that automatically constructs a semantic model from a heterogeneous data environment with minimal human input. This problem subsumes schema matching [19], which is NP-hard in the general case [20]; C2C therefore employs LLM-based heuristic approximations with confidence scoring.

**Definition 5 (Feedback Refinement).** *Feedback refinement* is a function $\delta : \mathcal{S} \times \mathcal{F} \to \mathcal{S}$ that updates the semantic model given feedback events $f \in \mathcal{F}$. The feedback space $\mathcal{F}$ includes four signal types: SQL execution outcomes ($f_\text{sql}$), user corrections ($f_\text{usr}$), query-result mismatch signals ($f_\text{qrm}$), and insight usefulness ratings ($f_\text{ins}$). The *self-improving* property holds when $\mathcal{U}(\delta(\mathcal{S}, f), f_\text{bi}) \geq \mathcal{U}(\mathcal{S}, f_\text{bi})$ in expectation for any non-empty feedback batch.

**Definition 6 (Vector Knowledge Store).** A *vector knowledge store* $\mathcal{V}$ is a persistent store of tuples $(q_\text{norm}, \pi_\text{verified}, r_\text{gold}, \text{emb}(q_\text{norm}))$ representing normalized queries, their verified execution plans, gold results, and query embeddings. It supports $k$-nearest-neighbor retrieval: $\text{Retrieve}(q, k) : \mathcal{Q} \to (\mathcal{V})^k$, returning the $k$ most semantically similar verified query–plan pairs to serve as grounding context for new query generation.

**Definition 7 (BI Query and Answer).** A *BI query* $q \in \mathcal{Q}$ is a natural-language utterance expressing an analytical intent over $\mathcal{D}$. A *BI answer* $a \in \mathcal{A}$ comprises: a result set $r$, a provenance trace $\pi$, and a natural-language explanation $\xi$. The *AI-over-BI function* is $f_\text{bi} : \mathcal{Q} \times \mathcal{S} \times \mathcal{D} \times \mathcal{V} \to \mathcal{A}$.

$\mathcal{V}$ is a first-class argument—not a cache—because it conditions query *generation*, not query *lookup*. This is the formal distinction between vector-grounded BI reasoning and standard result caching.

**Problem 1 (Chaos 2 Clarity).** Given an uncurated heterogeneous data environment $\mathcal{D}$, construct $\mathcal{S} = f_\text{synth}(\mathcal{D})$ automatically, build an initial vector store $\mathcal{V}_0$, then deploy $f_\text{bi}$ over $\mathcal{S}$, $\mathcal{D}$, and $\mathcal{V}$ to answer BI queries with measurable correctness, latency, and governance compliance—while continuously improving $\mathcal{S}$ and $\mathcal{V}$ via feedback $\delta$ such that query quality improves over the deployment lifetime.

### Optimization Objective

$$\mathcal{U}(\mathcal{S}, \mathcal{V}, f_\text{bi}) = \underbrace{\frac{1}{m}\sum_{j=1}^{m} \mathbb{1}\bigl[\text{RC}(f_\text{bi}(q_j,\mathcal{S},\mathcal{D},\mathcal{V}),\, a^*_j)\bigr]}_{\text{result correctness}} - \lambda_1 \cdot \bar{L} - \lambda_2 \cdot \bar{V}$$

where $\text{RC}(\cdot)$ is result correctness, $\bar{L}$ is mean end-to-end latency, $\bar{V}$ is the governance violation rate, and $\lambda_1, \lambda_2 \geq 0$ are operator-specified weights.

### Semantic Consistency Property

**Proposition 1 (Semantic Consistency).** The orchestration pipeline $f_\text{bi}$ is *semantically consistent* with $\mathcal{S}$ if every entity reference in the generated SQL is grounded in a node $e \in \mathcal{E}$ with $\kappa(e) \geq \theta_\text{exec}$. The validator $f_\text{vrf}$ enforces this by rejecting any plan referencing unmapped entities, bounding silent failures to the residual error of $\kappa$ estimation rather than allowing arbitrary hallucinated joins.

**Proposition 2 (Self-Improvement Convergence).** Under the feedback update rule (Equation 1), for any element $x \in \mathcal{E} \cup \mathcal{M} \cup \mathcal{R}$ and any unbiased sequence of feedback events drawn from a stationary process with true confirmation rate $p_x$, the expected confidence converges: $\mathbb{E}[\kappa_t(x)] \to p_x$ as $t \to \infty$. Furthermore, each confirmed entry added to $\mathcal{V}$ strictly increases retrieval precision for semantically similar future queries under a stationary query distribution.

### Research Questions

- **RQ1 (Semantic Unification):** How effectively can automated semantic synthesis recover $\mathcal{S}$ from $\mathcal{D}$, measured by entity/metric coverage, mapping F1, and modeling effort reduction, relative to a manually curated gold model?
- **RQ2 (Semantic Layer Impact):** Does the automated semantic layer produce measurably fewer join errors, aggregation errors, and incorrect business metric results compared to operating on raw schemas?
- **RQ3 (Orchestration):** Does the decomposed six-stage pipeline yield better execution accuracy and error recoverability than monolithic LLM baselines and reduced-stage variants across query complexity tiers?
- **RQ4 (Heterogeneous Data):** Does C2C degrade less than baselines when query complexity moves from single-source structured to multi-source and semi-structured data?
- **RQ5 (Self-Improvement):** Do the vector-grounded reasoning and feedback-driven refinement mechanisms produce measurable quality improvements over the deployment lifetime, reducing repeated error rates over successive query batches?
- **RQ6 (Latency–Accuracy):** What is the explicit latency cost of orchestration overhead, and does the accuracy gain justify it across deployment scenarios?

---

## 3. Contributions

C2C makes the following six contributions:

- **C1 — Formal self-improving semantic orchestration framework.** A formal definition of the semantic synthesis and feedback refinement problems, unifying automated $\mathcal{S}$ construction from uncurated $\mathcal{D}$ with a continuous learning loop $\delta$ that updates $\mathcal{S}$ and $\mathcal{V}$ from four structured feedback signal types. This extends LLM-assisted metadata enrichment [21, 22] and schema matching [19] to a self-improving BI pipeline.

- **C2 — Decomposed six-stage agentic orchestration pipeline.** A production-oriented Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent pipeline that isolates each failure mode to a specific stage, enabling targeted recovery rather than monolithic re-generation (Algorithm 1).

- **C3 — Vector-Grounded BI Reasoning.** A persistent vector knowledge store $\mathcal{V}$ of verified query–plan–result triples that grounds SQL generation in semantically similar successful past executions, reducing repeated hallucination errors over time without model retraining.

- **C4 — Feedback-Driven Continuous Learning Loop.** A structured four-signal feedback mechanism (SQL outcomes, user corrections, query-result mismatches, insight usefulness) that drives prompt refinement, schema enrichment, embedding updates, and rule injection. C2C is the first BI system to formalize all four feedback signal types and their corresponding update targets.

- **C5 — Working prototype and error taxonomy.** A deployed prototype over a realistic three-source retail enterprise environment (PostgreSQL, Salesforce CRM, logistics CSV) and a five-class error taxonomy (E1–E5) derived from prototype operation, grounding the evaluation design.

- **C6 — Six-experiment evaluation protocol.** A structured evaluation framework with six experiments mapping directly to the four architectural claims, with explicit falsifiable predictions, baselines, metrics, and dataset specifications.

---

## 4. Related Work

### 4.1 LLM-Based Text-to-SQL and NL2SQL

Shi et al. [9] survey LLM-based text-to-SQL methods covering prompt engineering and fine-tuning paradigms. Spider 1.0 [7] and BIRD [12] are standard benchmarks, with recent work achieving ≈ 86% and ≈ 72% execution accuracy respectively—both assuming fully curated, well-documented single-database schemas. Spider 2.0 [8] introduces enterprise-level complexity where best models achieve only 17–21%, attributable to schema heterogeneity rather than query complexity per se [8]. DAIL-SQL [13] achieves competitive performance through efficient prompt selection but operates on single, structured sources with no cross-query learning. C2C targets the pre-NL2SQL step of synthesizing the semantic model from raw data, and adds the cross-query learning layer that single-shot text-to-SQL systems lack entirely.

### 4.2 Commercial AI-over-BI Systems

ThoughtSpot Sage, Microsoft Power BI Copilot, Tableau Ask Data, Databricks AI/BI, and Qlik Insight Advisor all require a pre-constructed semantic model and provide no mechanism for self-construction or feedback-driven self-improvement. The requirement for a pre-built semantic model is documented as the primary deployment barrier for mid-market organizations [5]. C2C uniquely automates both construction and continuous refinement.

### 4.3 Semantic Layer Tools

dbt Semantic Layer, Looker LookML, Cube.dev, and AtScale require substantial manual modeling effort [11] and are static: they do not update from query feedback. Singh et al. [21] estimate that manual semantic model construction for a mid-sized enterprise data environment requires weeks to months of engineering effort. C2C treats these tools as potential *consumers* of its synthesized output, with integration endpoints designed for compatibility.

### 4.4 LLM Agents for Data Analytics

InsightPilot [23] deploys LLM agents for automated data exploration but assumes a pre-structured environment and does not learn from failures. Cheng et al. [24] evaluate GPT-4 as a data analyst, finding it limited on schema inference and multi-source reasoning. Rahman et al. [3] and Chen et al. [25] survey LLM data science agents, identifying the absence of adaptive learning and cross-source reasoning as key gaps in current systems. Zhu et al. [5] formalize requirements for agents operating over heterogeneous systems, identifying semantic alignment and operational feedback as unsolved problems. C2C directly targets both.

### 4.5 Automated Metadata Discovery and Data Cataloging

Singh et al. [21] demonstrate LLM-based metadata enrichment for enterprise catalogs, achieving > 80% ROUGE-1 F1 and ≈ 90% acceptance by data stewards. LEDD [22] employs LLMs for hierarchical semantic catalog generation over data lakes. LLMDapCAT [26] applies LLM+RAG for automated metadata extraction. SCHEMORA [19] achieves state-of-the-art cross-schema alignment via multi-stage LLM recommendation. These works address the *construction* of semantic metadata but do not couple it to a query execution pipeline or feedback loop. C2C integrates construction, execution, and refinement.

### 4.6 Multi-Agent Orchestration

Adimulam et al. [27] survey multi-agent LLM architectures, identifying planning, state management, and policy enforcement as key challenges. AutoGen [14] provides a widely adopted conversation framework. Arunkumar et al. [16] examine memory backends and tool integration for agentic AI. AgentArch [28] benchmarks enterprise agent architectures, with best models achieving only 35.3% on complex multi-step tasks, motivating C2C's decomposed pipeline design. ReAct [15] and Plan-then-Execute [29] are foundational primitives that C2C extends with domain-specific SQL-oriented stages and cross-stage feedback routing.

### 4.7 RAG and Vector-Grounded Reasoning

Lewis et al. [17] introduce RAG for knowledge-intensive NLP. Gao et al. [18] survey advanced RAG architectures. Cheerla [30] proposes hybrid retrieval for structured enterprise data. RAGAS [31] provides automated RAG evaluation. Pan et al. [32] demonstrate table question answering via RAG. C2C's vector-grounded BI reasoning extends this line by operating over a store of *verified execution patterns* (query–plan–result triples) rather than document fragments—retrieving *how to query* rather than *what to return*, grounding SQL generation rather than answer generation.

---

## 5. System Architecture

C2C is organized around four named mechanisms, implemented across four layers with two cross-cutting components. Their correspondence:

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
│           Semantic Synthesis Layer (L2)  [Mechanism I]               │◄►│  (4 signal types)         │
│  Asset Discovery · Concept Inference · Semantic Graph                │  │  → prompt refinement      │
│  · Human-in-Loop Refinement                                          │  │  → schema enrichment      │
└──────────────────────────┬───────────────────────────────────────────┘  │  → embedding updates      │
       profiles ↓          │ ↑ raw data                                   │  → rule injection         │
┌──────────────────────────▼───────────────────────────────────────────┐  └───────────────────────────┘
│           Data & Connectivity Layer (L1)                             │
│  RDBMS · Data Lakes · CSV/Excel · SaaS APIs · Document Stores        │
└──────────────────────────────────────────────────────────────────────┘
```

*Figure 1. C2C four-layer architecture. The vector store $\mathcal{V}$ and feedback loop $\delta$ are first-class architectural components, not auxiliary optimizations.*

### 5.1 Data and Connectivity Layer (𝓛₁)

𝓛₁ exposes a unified discovery interface over $\mathcal{D}$. Connectors support five source types and populate a lightweight catalog with schema snapshots $\sigma_i$, statistical profiles $\rho_i$, lineage hints, and access controls $\alpha_i$. Data is never centralized; 𝓛₁ federates access. Schema refresh events in 𝓛₁ trigger confidence re-evaluation in 𝓛₂ via $\delta$.

### 5.2 Mechanism I: Automated Semantic Layer (𝓛₂)

𝓛₂ implements $f_\text{synth} : \mathcal{D} \to \mathcal{S}$ and is the primary differentiator from all existing AI-over-BI systems: it builds its own semantic model from raw data, with no manual modeling required, and keeps that model current through continuous feedback. The challenge of automated semantic synthesis from heterogeneous sources is well-documented in the schema matching literature [19, 20]; C2C's contribution is coupling the synthesis step to a live BI execution pipeline with feedback.

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

*Figure 2. Automated semantic layer construction and continuous refinement path.*

**Asset discovery and profiling.** For each $d_i \in \mathcal{D}$, an LLM-assisted agent infers column types, candidate keys, potential foreign-key relationships, and computes statistical profile $\rho_i$. LLM-based column type inference and candidate key detection follows the approach demonstrated by Singh et al. [21] and extended by SCHEMORA [19].

**Concept and metric inference.** An LLM agent proposes entity mappings $\hat{e} : \text{col}(d_i) \to \mathcal{E}$, metric definitions with formulae $\phi_j$, and synonym sets, using embedding similarity and column naming heuristics to assign initial confidence $\kappa_0 \in [0,1]$.

**Semantic graph construction.** Inferred nodes and edges are materialized into the typed graph $\mathcal{S}$ with provenance annotations linking each element to its source and inference trace, stored in Neo4j 5.x.

**Human-in-the-loop refinement.** Data owners review mappings with $\kappa < \theta_\text{review} = 0.75$ via a targeted interface. Human review is *optional*—C2C operates with whatever confidence the automated pipeline achieves; human review accelerates quality, not prerequisite. The HITL review pattern follows practices documented in Singh et al. [21].

**Continuous self-improvement.** The semantic model receives updates from all four feedback signal types (Section 5.6). It is a *living artifact* that improves with operational use, not a static artifact built once.

### 5.3 Mechanism II: Agentic Query Orchestration Pipeline (𝓛₃)

𝓛₃ implements $f_\text{bi}$ via a **decomposed six-stage pipeline**. The motivation for decomposition over monolithic LLM calls is empirically grounded: AgentArch [28] shows that single-LLM-call approaches achieve only 35.3% on complex enterprise tasks, while decomposed architectures recover significant accuracy. By isolating each task to a dedicated agent, C2C enables stage-specific error detection, targeted retry, and fine-grained feedback routing.

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

| Stage | Agent | Function | Signature |
|---|---|---|---|
| 1 | Planner | $f_\text{pln}$ | $\mathcal{Q} \times \mathcal{S} \times \mathcal{P} \to \mathcal{T} \times \mathcal{I} \times \Pi$ |
| 2 | Retriever | $f_\text{ret}$ | $\mathcal{Q} \times \mathcal{V} \to (\mathcal{V})^k$ |
| 3 | SQL Generator | $f_\text{qry}$ | $\Pi \times \mathcal{D} \times (\mathcal{V})^k \to \text{SQL}^* \cup \text{RAG}^*$ |
| 4 | Validator | $f_\text{vrf}$ | $(\text{SQL}^* \cup \text{RAG}^*) \times \mathcal{S} \times \mathcal{P} \to \{0,1\} \times (\cdot)_\text{safe}$ |
| 5 | Executor | $f_\text{exe}$ | $(\cdot)_\text{safe} \times \mathcal{D} \to r \cup \text{Error}$ |
| 6 | Insight Agent | $f_\text{ins}$ | $r \times \pi \to \xi \times \mathcal{F}$ |

The Planner employs a Plan-then-Execute strategy [29]: a full plan $\pi \in \Pi$ is committed before execution, enabling budget control, policy pre-checking, and cost-aware step ordering. Chain-of-thought prompting [33] is applied at planning and query generation stages.

### 5.4 Orchestration Algorithm

**Algorithm 1: C2C Orchestration Pipeline**

```
Input:  Query q ∈ 𝒬, semantic model 𝒮, sources 𝒟,
        vector store 𝒱, policies 𝒫, max retries K
Output: Answer a ∈ 𝒜 or governed failure report

1.  (t, ℐ, π) ← f_pln(q, 𝒮, 𝒫)              // classify intent + build execution plan
2.  G ← f_ret(q, 𝒱, k=5)                     // retrieve k verified grounding plans
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
15.         emit F → δ                        // route feedback signals to learning loop
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

1. **Line 2 — Grounding retrieval before generation.** The SQL Generator receives $k=5$ verified query–plan pairs from $\mathcal{V}$ as conditioning context, shifting generation toward verified patterns. This is semantic few-shot conditioning, not prompt-padding.

2. **Lines 13–15 — Closed learning loop.** Every successful execution writes to $\mathcal{V}$ and emits feedback to $\delta$. The system improves with every successful query, not only with explicit human corrections.

3. **Lines 8, 19 — Failure signal routing.** Both policy failures and execution errors emit structured signals to $\delta$, enabling the learning loop to update even on failed queries. No existing BI system surveyed implements this bidirectional failure routing [5, 10].

### 5.5 Mechanism III: Vector-Grounded BI Reasoning

The vector knowledge store $\mathcal{V}$ is architecturally distinct from the result cache. The cache returns *results* for repeated identical queries; $\mathcal{V}$ returns *execution patterns* for semantically similar but structurally distinct queries—it improves *query construction*, not query latency.

**Store structure.** Each entry in $\mathcal{V}$ is a tuple:
$$v_i = (q_\text{norm},\; \pi_\text{verified},\; \text{SQL}^*_\text{verified},\; r_\text{gold},\; \kappa_\text{entry},\; \text{emb}(q_\text{norm}))$$

where $\kappa_\text{entry} \in [0,1]$ decays if subsequent similar queries produce contradictory results.

**Error suppression mechanism.** The predominant failure mode in Text2SQL over uncurated schemas is *consistent* hallucination: the model repeatedly generates the same wrong column name because the correct mapping exists in no accessible context [9, 8]. Once a correct execution establishes the mapping, it enters $\mathcal{V}$ and grounds all future similar queries. Error class E1 (schema hallucination) is thereby suppressed without rule engineering. The use of verified examples as in-context conditioning is consistent with findings in DAIL-SQL [13] and analogous few-shot selection work [9].

**Store management.** $\mathcal{V}$ is bounded at $|\mathcal{V}| \leq N_\text{max}$ entries. When capacity is reached, entries with $\kappa_\text{entry} < \theta_\text{prune}$ are evicted. On schema change detection, all $\mathcal{V}$ entries referencing the affected column have $\kappa_\text{entry}$ set to 0 and are flagged for re-validation, preventing stale grounding after schema evolution.

### 5.6 Mechanism IV: Feedback-Driven Continuous Learning Loop

The feedback loop $\delta : \mathcal{S} \times \mathcal{F} \to \mathcal{S}$ makes C2C *self-improving*. It processes four structured signal types and routes each to specific update targets:

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

**Confidence update rule.** For $x \in \mathcal{E} \cup \mathcal{M} \cup \mathcal{R}$:

$$\kappa_{t+1}(x) = (1-\alpha)\,\kappa_t(x) + \alpha\,\mathbb{1}[f \text{ confirms } x] \tag{1}$$

with learning rate $\alpha \in (0,1)$. Under a stationary confirmation process with unbiased feedback, $\mathbb{E}[\kappa_t(x)] \to p_x$ as $t \to \infty$ (Proposition 2). The prototype uses $\alpha = 0.15$.

**Prompt refinement** accumulates failure patterns in store $\Phi$. When $|\Phi_\text{type}| \geq \theta_\text{batch} = 10$ for a given error class, a refinement step generates new few-shot examples targeting that class and injects them into the relevant agent's system prompt. This is a deployment-safe alternative to fine-tuning, consistent with the prompt-based adaptation approach in [29].

**Schema enrichment.** Repeated E1 failures on a specific column trigger LLM-assisted re-profiling, proposing new entity mappings or synonym additions. Proposals with $\kappa_0 \geq 0.85$ are auto-applied; lower-confidence proposals are queued for human review.

**Embedding updates.** User corrections establishing new synonyms trigger re-embedding of affected $\mathcal{V}$ entries and $\mathcal{S}$ nodes, keeping the semantic space consistent with corrected vocabulary.

**Rule injection.** Repeated policy violations of the same type are promoted from ad-hoc validator checks to persistent rules in $\mathcal{P}$, reducing LLM validator reliance for known constraint patterns.

### 5.7 Experience and Integration Layer (𝓛₄)

𝓛₄ exposes C2C via: (i) a conversational interface supporting multi-turn analytical dialogue with visualization rendering; and (ii) REST and semantic-layer APIs compatible with dbt Semantic Layer, Looker LookML, and generic JDBC/ODBC, allowing downstream BI tools to query $\mathcal{S}$ without replacing existing dashboards. Each conversational user turn generates $f_\text{usr}$ and $f_\text{ins}$ signals routed to $\delta$.

### 5.8 Query Result Cache

The result cache is a latency optimization layer distinct from $\mathcal{V}$. Two queries are *cache-equivalent* if $\cos(\text{emb}(q), \text{emb}(q')) \geq \lambda_\text{cache}$ and their resolved source sets are identical. Cache hit rate $H$ and latency reduction $\Delta L$ are tracked as system performance metrics.

---

## 6. Prototype Implementation

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
- **(i)** A PostgreSQL OLTP database — sales and order records across 14 tables;
- **(ii)** A Salesforce CRM API export — customer accounts and active deals;
- **(iii)** CSV flat files from a third-party logistics provider — delivery events and status codes.

These sources comprise 47 columns with inconsistent naming conventions, no shared primary keys, and zero pre-existing documentation. The column naming `line_value` (for what a business analyst calls "revenue") and the absence of any join key between the Salesforce and logistics exports represent the canonical failure modes that motivate C2C's design.

**Deployment model.** C2C deploys as a sidecar to existing data infrastructure with zero ETL overhead. $\mathcal{S}$ is built once and continuously maintained via $\delta$. $\mathcal{V}$ starts empty and is populated through operational use. Queries execute in-situ against source databases.

---

## 7. Error Taxonomy

A key contribution of C2C is the ability to *classify* query failures to specific pipeline stages and route recovery through mechanism-specific interventions. The five error classes below were derived from observation of failure modes during prototype operation and align with failure categories independently identified in the Text2SQL evaluation literature [8, 9, 12].

| Error Class | Stage | Definition | Recovery Mechanism |
|---|---|---|---|
| **E1: Schema hallucination** | SQL Generator | LLM references a column/table not in 𝒟. Example: `SELECT order_total` when column is `line_value`. | Retry with error context + 𝒱 grounding + Mechanism IV schema enrichment |
| **E2: Aggregation error** | SQL Generator | Syntactically valid query with semantically wrong aggregation. Example: `AVG` instead of `SUM` for revenue. | Mechanism IV prompt refinement via $f_\text{qrm}$; not recoverable by retry alone |
| **E3: Join path error** | Planner | Join between incompatible entities or incorrect key, with no path in $\mathcal{R}$. | Validator detects via $\mathcal{S}$ consistency check; retry with corrected plan; Mechanism IV rule injection |
| **E4: Semantic misunderstanding** | Planner | Query intent misclassified; plan addresses a different BI task. Example: trend query classified as metric lookup. | Mechanism IV prompt refinement via $f_\text{usr}$; requires $\mathcal{S}$ quality improvement |
| **E5: Cross-source failure** | Planner | Single-source plan issued for a multi-source query because $\mathcal{S}$ has low-confidence cross-source relationships. | Prevented by Mechanism I automated cross-source inference; not recoverable by any single-source system |

*Table 1. Error taxonomy with stage attribution and mechanism-level recovery mapping.*

E1 and E3 are recoverable at query time (retry + grounding); E2 and E4 require Mechanism IV's learning loop; E5 is prevented by Mechanism I and is categorically unaddressable by single-source Text2SQL systems.

---

## 8. Evaluation Design

We define six core experiments directly mapped to the four architectural claims, plus two secondary experiments for system characterization. This structure follows the principle that every experiment must provide direct evidence for a specific claim [see framework in attached document].

### 8.1 Dataset

**BI Question Suite.** 50 questions across four complexity tiers, derived from the three-source retail prototype:

| Tier | Description | # Questions | Target Error Classes |
|---|---|---|---|
| L1 | Single-source metric lookup | 15 | E1, E2 |
| L2 | Multi-table join (single source) | 15 | E1, E2, E3 |
| L3 | Cross-source multi-hop | 10 | E3, E4, E5 |
| L4 | Unstructured + structured (RAG) | 10 | E4 |

Each question has: a natural language prompt, gold SQL (manually written), gold result set, and error-class annotation. Gold SQL is verified by two independent annotators; disagreements are resolved by discussion. The question design follows the Spider/BIRD annotation methodology [7, 12] adapted to the multi-source uncurated setting.

**Baselines.**
- **𝔅₁ (Direct LLM-to-SQL):** GPT-4o single call with raw schema context, no semantic layer, no orchestration, no learning.
- **𝔅₂ (Schema-aware LLM):** GPT-4o with schema descriptions and column metadata injected as context, no semantic layer, no orchestration. Represents the strongest single-call baseline [9, 13].
- **𝔅₃ (C2C without semantic layer):** Full six-stage pipeline operating on raw schemas, no $\mathcal{S}$, no $\delta$, no $\mathcal{V}$ updates.

**Metrics.**
- *Execution Accuracy (EA):* % of queries that execute without runtime error.
- *Result Correctness (RC):* % of queries whose result set matches the gold answer (exact set match).
- *SQL Exact Match (EM):* % of generated SQL matching gold SQL after normalization [7].
- *Error Class Rate:* % of failures attributed to each of E1–E5.
- *Latency P50/P95:* End-to-end response time in milliseconds.

### 8.2 Experiment 1: Baseline vs. C2C (Primary Proof of Claim)

**Maps to:** Central falsifiable claim; RQ3  
**Goal:** Demonstrate that C2C outperforms direct and schema-aware LLM approaches on all query tiers.

**Setup:** Evaluate 𝔅₁, 𝔅₂, and C2C Full (V5) on the complete 50-question suite. Report EA, RC, and EM per tier and overall.

**Expected main results table:**

| System | L1 EA | L2 EA | L3 EA | L4 EA | Overall EA | Overall RC |
|---|---|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — | — | — | — |
| 𝔅₂: Schema-aware LLM | — | — | — | — | — | — |
| C2C Full (V5) | — | — | — | — | — | — |

*Results to be filled upon experimental runs.*

**Falsifiable prediction:** EA(V5) ≥ EA(𝔅₁) + 25pp overall; EA(V5) on L3 > 0% while EA(𝔅₁) = 0% (cross-source queries are categorically unsolvable without a semantic layer).

**Failure condition:** If improvement is < 5pp, the central claim does not hold and the architecture requires revision.

### 8.3 Experiment 2: Semantic Layer Impact

**Maps to:** Mechanism I; RQ1, RQ2  
**Goal:** Isolate the contribution of the automated semantic layer.

**Setup:** Compare 𝔅₂ (schema-aware, no $\mathcal{S}$) against 𝔅₃ (full pipeline, no $\mathcal{S}$) against V5 (full pipeline, full $\mathcal{S}$). Report E1, E2, E3 error class rates in addition to EA/RC.

| System | E1 Rate | E2 Rate | E3 Rate | L2 EA | L3 EA |
|---|---|---|---|---|---|
| 𝔅₂: Schema-aware LLM | — | — | — | — | — |
| 𝔅₃: Pipeline, no 𝒮 | — | — | — | — | — |
| V5: Full C2C | — | — | — | — | — |

*Results to be filled upon experimental runs.*

**Falsifiable predictions:** E1 rate decreases significantly from 𝔅₂ to V5 (synonym resolution); E3 rate decreases significantly from 𝔅₃ to V5 (cross-source join grounding); E5 rate is > 0% in 𝔅₂ and 𝔅₃ and 0% in V5 on L3 questions.

**Semantic synthesis quality sub-experiment (RQ1):** Report entity coverage, metric coverage, mapping F1 (precision/recall against gold $\mathcal{S}$), and human review hours.

| Metric | Result |
|---|---|
| Entities inferred / gold | — / — |
| Metrics inferred / gold | — / — |
| Cross-source relationships inferred / gold | — / — |
| Mapping F1 (κ ≥ 0.80 subset) | — |
| Human review time to acceptable 𝒮 | — hours |

*Results to be filled upon experimental runs.*

### 8.4 Experiment 3: Agent Ablation Study

**Maps to:** Mechanism II; RQ3  
**Goal:** Demonstrate that pipeline decomposition contributes beyond the semantic layer alone, and that each stage matters.

**Variants:**

| Variant | Components Active | Hypothesis |
|---|---|---|
| **V0: Monolithic LLM** | Single LLM call, full 𝒮 context, no decomposition | E-class rates higher than V1; establishes decomposition baseline |
| **V1: No Planner** | Direct query → SQL Generator → Validator → Executor | E4, E5 rates increase vs. V5 |
| **V2: No Validator** | Full pipeline, validator disabled | E3 rate increases; policy violations increase |
| **V3: No Retry (K=0)** | Full pipeline, no retry loop | E1 rate increases vs. V5 |
| **V5: C2C Full** | All stages active | Minimum error rates |

| Variant | EA | RC | E1 Rate | E3 Rate | P50 (ms) |
|---|---|---|---|---|---|
| V0: Monolithic LLM + 𝒮 | — | — | — | — | — |
| V1: No Planner | — | — | — | — | — |
| V2: No Validator | — | — | — | — | — |
| V3: No Retry | — | — | — | — | — |
| V5: C2C Full | — | — | — | — | — |

*Results to be filled upon experimental runs.*

**Falsifiable predictions:** EA(V5) > EA(V0) on L2–L3 (pipeline decomposition matters beyond semantic layer alone); EA(V3) < EA(V5) demonstrating retry contribution; removing validator increases policy violations to > 0.

### 8.5 Experiment 4: Heterogeneous Data Handling

**Maps to:** Core claim on heterogeneous data; RQ4  
**Goal:** Demonstrate that C2C degrades less than baselines as data complexity increases from clean structured to heterogeneous multi-source.

**Setup:** Measure EA/RC across the four tiers (L1–L4) for all three systems, treating tier as a proxy for data heterogeneity. Additionally report performance on structured-only (L1+L2) vs. heterogeneous (L3+L4) splits.

| System | Structured (L1+L2) EA | Heterogeneous (L3+L4) EA | Degradation |
|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — |
| 𝔅₂: Schema-aware LLM | — | — | — |
| C2C Full (V5) | — | — | — |

*Results to be filled upon experimental runs.*

**Falsifiable prediction:** C2C's degradation from L1+L2 to L3+L4 is < 50% of 𝔅₁'s degradation, demonstrating superior handling of data heterogeneity.

### 8.6 Experiment 5: Feedback Learning Loop

**Maps to:** Mechanism IV; RQ5  
**Goal:** Demonstrate measurable improvement over time through the feedback-driven learning loop.

**Setup:** Run the 50-question suite in four sequential batches of 50 queries each (200 queries total), with feedback enabled between batches for V5 (full C2C) and disabled for V4 (no feedback, $\alpha = 0$).

| Checkpoint | V5 Full EA | V4 No-Feedback EA | V5 E1 Rate | V4 E1 Rate |
|---|---|---|---|---|
| T=50 (batch 1) | — | — | — | — |
| T=100 (batch 2) | — | — | — | — |
| T=150 (batch 3) | — | — | — | — |
| T=200 (batch 4) | — | — | — | — |

*Results to be filled upon experimental runs.*

**Expected output:** A graph with X-axis = query batch (T), Y-axis = EA and E1 error rate. V5 should show monotonically improving EA and declining E1 rate; V4 should be flat.

**Falsifiable prediction:** EA(V5, T=200) ≥ EA(V5, T=50) + 5pp; EA(V4) is statistically flat across all four checkpoints. If both curves are flat, Mechanism IV contributes nothing and requires redesign.

### 8.7 Experiment 6: Retrieval / Vector Grounding Impact

**Maps to:** Mechanism III; RQ5  
**Goal:** Demonstrate that vector-grounded reasoning reduces hallucination rate and improves first-pass EA.

**Setup:** Compare V3 (full pipeline, no $\mathcal{V}$) against V5 (full pipeline, $\mathcal{V}$ pre-populated with 50 warm-up queries). Report E1 rate, first-pass EA (EA before any retry), and EA improvement over T=50 to T=200.

| System | First-Pass EA | Final EA (after retry) | E1 Rate | Hallucination Rate |
|---|---|---|---|---|
| V3: No 𝒱 grounding | — | — | — | — |
| V5: Full C2C | — | — | — | — |

*Results to be filled upon experimental runs.*

**Falsifiable prediction:** First-pass EA(V5) > First-pass EA(V3) by ≥ 8pp on L1+L2; E1 rate significantly lower in V5 on queries with $\mathcal{V}$ coverage (cosine similarity ≥ 0.85 match in $\mathcal{V}$).

---

## 9. Secondary Experiments

### 9.1 Experiment 7: Error Taxonomy Distribution Analysis

**Goal:** Characterize where each system fails, confirming the error taxonomy's predictions.

For each of 𝔅₁, 𝔅₂, V0, and V5, report the distribution of failures across E1–E5. Expected output: a stacked bar chart showing error class distribution per system. This directly validates the taxonomy's claim that different architectural decisions suppress different error classes.

| System | E1 | E2 | E3 | E4 | E5 | No Error |
|---|---|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — | — | — | — |
| 𝔅₂: Schema-aware LLM | — | — | — | — | — | — |
| V5: C2C Full | — | — | — | — | — | — |

*Results to be filled upon experimental runs.*

### 9.2 Experiment 8: Latency–Accuracy Tradeoff

**Goal:** Provide practitioners with explicit cost-benefit data for deployment decisions.

Report P50/P95 latency vs. EA for each ablation variant and baseline, producing a Pareto frontier. Report the breakdown of latency overhead per pipeline stage.

| Variant | P50 (ms) | P95 (ms) | Overall EA | Latency premium over 𝔅₁ |
|---|---|---|---|---|
| 𝔅₁: Direct LLM-to-SQL | — | — | — | baseline |
| 𝔅₂: Schema-aware LLM | — | — | — | — |
| V3: No retry | — | — | — | — |
| V5: C2C Full | — | — | — | — |
| V5: Cache hit | — | — | — (same as V5) | — |

*Results to be filled upon experimental runs.*

**Expected insight:** "C2C trades X ms P50 latency for Y pp accuracy improvement. On warm query distributions (cache hit rate ≥ Z%), C2C's P50 falls below the baseline."

---

## 10. Full Evaluation Protocol

### Phase 1: Experiments 1–8 (Offline)

Run Experiments 1–8 on the 50-question retail prototype dataset. All results are reproducible with a fixed $\mathcal{S}$ snapshot and fixed $\mathcal{V}$ warm-up state. Statistical significance reported via McNemar's test on EA differences [7] and Mann-Whitney U on latency distributions (α = 0.05).

### Phase 2: Robustness and Drift

Inject four controlled schema perturbations using the Dr. Spider taxonomy [34]:

1. **Column rename:** `order_total` → `line_value`
2. **Table restructure:** Split `orders` into `orders_header` + `orders_lines`
3. **New source addition:** Second CRM export with partially overlapping entities
4. **Policy change:** Mark `email_id` as PII requiring masking

For each perturbation: measure immediate EA drop, $t^*$ (interactions to restore 90% of pre-drift EA via $\delta$), and $\mathcal{V}$ invalidation behavior.

**Drift recovery hypothesis.** $t^* \leq 50$ interactions for column rename and policy change; $t^* \leq 100$ for table restructure and new source addition.

### Phase 3: User Study

Within-subjects pilot study (n = 10–20 business analyst participants). Task-order counterbalanced. Post-task surveys: SUS usability, NASA-TLX cognitive load, custom 5-item trust scale. Paired Wilcoxon signed-rank tests (α = 0.05).

**Hypotheses:**
- **H1:** Task success rate non-inferior to existing tools (ΔTSR ≥ −5%, one-sided Wilcoxon, α = 0.05).
- **H2:** Time-to-insight lower with C2C than existing tools (p < 0.05, two-sided Wilcoxon).
- **H3:** Trust score ≥ 3.5/5 on first use, increasing after each feedback-refinement cycle.

---

## 11. Discussion

### Design Rationale: Why Four Mechanisms

The four-mechanism design responds to a specific failure analysis. Existing BI systems fail on uncurated heterogeneous data in two distinguishable ways: *at query time* (wrong SQL, wrong join, hallucinated column) and *across queries* (repeating the same mistake). Single-mechanism interventions are insufficient: a semantic layer without a learning loop produces quality at deployment time but degrades as schemas evolve; a learning loop without semantic grounding learns to navigate a schema it still doesn't understand [5, 10]. The four mechanisms address four distinct failure modes (missing semantics, monolithic fragility, repeated hallucination, no adaptation), and their combination enables the self-improving property.

### Limitations

LLM-inferred semantic mappings may exhibit hallucination or inconsistency on ambiguous schemas [21, 19], representing the irreducible residual error of $\kappa$ estimation. Multi-source query planning incurs latency proportional to cross-system join complexity. The feedback loop's prompt refinement requires reaching batch threshold $\theta_\text{batch}$ before updating, creating a cold-start period for rare error types. Vector store grounding provides no benefit at deployment time before warm-up queries have been processed; the warm-up requirement is a real deployment cost. The evaluation is confined to a single domain (retail); generalization is the subject of the companion paper.

### Future Work

1. Extending 𝓛₂ with domain ontologies (FIBO for finance, HL7/FHIR for healthcare) to reduce bootstrap time in specialized domains.
2. Integrating differential privacy [35] into $f_\text{vrf}$ for PII-sensitive deployments where masking alone is insufficient.
3. Fine-tuning domain-specific SQL generator models on the $\mathcal{V}$ store to reduce latency while maintaining grounding benefit [13].
4. Defining open benchmarks for AI-over-BI on heterogeneous, uncurated data, complementing Spider [7], BIRD [12], and Spider 2.0 [8].

---

## 12. Conclusion

We introduced **Chaos 2 Clarity** (C2C), a self-improving semantic orchestration framework for LLM-driven business intelligence over heterogeneous, uncurated enterprise data. The paper's central insight—that reliable LLM-over-data systems require semantic grounding and adaptive learning together, not separately—motivates a four-mechanism design: an Automated Semantic Layer that builds and continuously updates a semantic model from raw data; a decomposed six-stage Agentic Query Orchestration Pipeline that isolates failure modes for targeted recovery; Vector-Grounded BI Reasoning that suppresses repeated hallucination errors; and a Feedback-Driven Continuous Learning Loop that ingests four structured signal types to drive prompt refinement, schema enrichment, embedding updates, and rule injection.

The paper presents a deployed three-source retail prototype, a five-class error taxonomy grounded in prototype operation, and a six-experiment evaluation protocol with explicit falsifiable predictions. Experimental results will be reported upon completion of evaluation runs. C2C addresses the gap identified by recent data agent surveys [3, 5] between current AI-over-data systems and the heterogeneous realities of enterprise data environments.

---

## Acknowledgements

The author thanks the open-source communities behind LangChain, LlamaIndex, FastAPI, and Neo4j, whose tools informed the prototype design. No external funding was received for this work.

---

## Ethics Statement

This paper presents a system architecture and evaluation methodology. No human subjects data was collected in the work reported here. The user study (Section 10, Phase 3) will be conducted under appropriate IRB review prior to execution. The system includes a governance layer ($\mathcal{P}$, $f_\text{vrf}$) specifically designed to enforce PII protection and data access policies.

---

## Reproducibility Statement

The prototype implementation, prompt templates, BibTeX reference file, and TikZ figure sources are available at:

```
https://github.com/bankupalliravi/chaos2clarity
```

The gold semantic model annotation protocol, the 50-question BI question suite with gold SQL and result sets, and all evaluation scripts will be released alongside the companion experimental paper.

---

## References

[1] OpenAI. GPT-4 Technical Report. 2023. arXiv:2303.08774  
[2] Minaee, S. et al. Large Language Models: A Survey. 2024. arXiv:2402.06196  
[3] Rahman, M. et al. LLM-Based Data Science Agents: A Survey. 2025. arXiv:2510.04023  
[4] Jiang, J. et al. SiriusBI: A Comprehensive LLM-Powered Solution for BI. 2024. arXiv:2411.06102  
[5] Zhu, Y. et al. A Survey of Data Agents: Emerging Paradigm or Overstated Hype? 2025. arXiv:2510.23587  
[6] Various Authors. A Survey of LLM × DATA. 2025. arXiv:2505.18458  
[7] Yu, T. et al. Spider. EMNLP 2018. arXiv:1809.08887  
[8] Lei, F. et al. Spider 2.0. 2024. arXiv:2411.07763  
[9] Shi, L. et al. A Survey on LLMs for Text-to-SQL. 2024. arXiv:2407.15186  
[10] Chen, W. et al. LLM/Agent-as-Data-Analyst: A Survey. 2025. arXiv:2509.23988  
[11] Various Authors. A Survey of LLM × DATA. 2025. arXiv:2505.18458 *(cite specifically for semantic layer manual effort)*  
[12] Li, J. et al. BIRD. NeurIPS 2023. arXiv:2305.03111  
[13] Gao, D. et al. DAIL-SQL. 2023. arXiv:2308.15363  
[14] Wu, Q. et al. AutoGen. ICLR 2024. arXiv:2308.08155  
[15] Yao, S. et al. ReAct. ICLR 2023. arXiv:2210.03629  
[16] Arunkumar, V. et al. Agentic AI. 2026. arXiv:2601.12560  
[17] Lewis, P. et al. RAG. NeurIPS 2020. arXiv:2005.11401  
[18] Gao, Y. et al. RAG Survey. 2024. arXiv:2312.10997  
[19] Gungor, O.E. et al. SCHEMORA. 2025. arXiv:2507.14376  
[20] Rahm, E. & Bernstein, P.A. Schema Matching Survey. VLDB Journal, 2001.  
[21] Singh, M. et al. LLM Metadata Enrichment. 2025. arXiv:2503.09003  
[22] An, Q. et al. LEDD. 2025. arXiv:2502.15182  
[23] Ma, P. et al. InsightPilot. EMNLP Demo 2023.  
[24] Cheng, L. et al. Is GPT-4 a Good Data Analyst? 2023. arXiv:2305.15038  
[25] Chen, W. et al. (same as [10])  
[26] Karim, S.F. et al. LLMDapCAT. CEUR 2024.  
[27] Adimulam, A. et al. Multi-Agent Orchestration. 2026. arXiv:2601.13671  
[28] Bogavelli, T. et al. AgentArch. 2025. arXiv:2509.10769  
[29] Del Rosario, R.F. et al. Plan-then-Execute. 2025. arXiv:2509.08646  
[30] Cheerla, C. RAG for Structured Enterprise Data. 2025. arXiv:2507.12425  
[31] Es, S. et al. RAGAS. 2023. arXiv:2309.15217  
[32] Pan, F. et al. Table QA via RAG. 2022. arXiv:2203.16714  
[33] Wei, J. et al. Chain-of-Thought Prompting. NeurIPS 2022. arXiv:2201.11903  
[34] Chang, S. et al. Dr. Spider. ICLR 2023. arXiv:2301.08881  
[35] Dwork, C. et al. Calibrating Noise to Sensitivity. TCC 2006.  

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

### B.1 Planner Prompt

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
Grounding context (k verified similar plans): {grounding_plans}
Active policies: {active_policies}
```

### B.2 SQL Generator Prompt

```
System: You are a BI SQL generator.
Generate SQL conditioned on the execution plan
and grounding context from verified similar queries.
If a grounding example shows the correct column
name for a concept, prefer it over inference.

Plan: {execution_plan}
Semantic model: {sm_json}
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
3. Join plausibility against semantic model
4. Entity references: all must have κ ≥ {theta_exec}

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
Given the result and execution trace:
1. Generate a clear natural-language insight.
2. Identify result anomalies or semantic mismatches.
3. Rate result usefulness 0-1.

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

| Capability | C2C | NL2SQL [9] | InsightPilot [23] | SiriusBI [4] | Catalogs [21] | Commercial BI |
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

---

## Appendix E: Feedback Signal Taxonomy

| Signal | Source | Trigger | Update Targets |
|---|---|---|---|
| $f_\text{sql}$ | Executor | Any SQL success or failure | Schema enrichment (E1/E3), 𝒱 κ updates, rule injection |
| $f_\text{usr}$ | Conversational UI | User edits an answer or correction | Schema enrichment, prompt refinement, synonym embedding updates |
| $f_\text{qrm}$ | Insight Agent | Agent flags semantic anomaly between intent and result | Prompt refinement (aggregation), schema enrichment (metric formulas) |
| $f_\text{ins}$ | UI / Insight Agent | User rates insight OR agent self-rates | Prompt refinement (narrator), 𝒱 κ_entry decay for low-rated entries |

---

## Pre-Submission Checklist

- [ ] Register at orcid.org and replace `0000-0000-0000-0000` with your real ORCID
- [ ] Replace `ravi@example.com` with your real email address
- [ ] Create `github.com/bankupalliravi/chaos2clarity` and push prototype code, prompt templates, and TikZ sources
- [ ] Run Experiments 1–8; fill all `—` cells in result tables before arXiv submission
- [ ] Remove unused .bib entries: `touvron2023llama2`; decide on `gupta2024governance` (citable in governance discussion) and `zhang2024tablellama` (citable in RAG over tables)
- [ ] Deduplicate `jiang2024siriusbi` (currently [4] and [5]; merge to single reference)
- [ ] Note: reference [11] currently points to same entry as [6] — find a dedicated citation for the semantic layer manual effort claim (Singh et al. [21] partially covers this)
- [ ] Update LaTeX source: add Definitions 5–6, update agent table to six stages, update contributions to C1–C6, add Experiments section (Section 8), add Appendix E
- [ ] Update `f_bi` signature in LaTeX to include $\mathcal{V}$ as fourth argument throughout
- [ ] Test LaTeX compilation: `pdflatex → bibtex → pdflatex → pdflatex`
- [ ] Verify `acmart` compiles on arXiv; if it fails, switch to `\documentclass[preprint]{acmart}`
- [ ] Have one domain expert review for technical accuracy before submission
