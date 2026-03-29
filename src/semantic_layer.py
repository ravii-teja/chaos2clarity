"""
Chaos 2 Clarity — Mechanism I: Automated Semantic Layer
Implements f_synth: D → S — building a semantic model from raw data.
Uses LLM-based profiling + NetworkX for the semantic graph.
"""

import json
import networkx as nx
import numpy as np
from typing import Dict, List, Optional, Any


class SemanticModel:
    """
    The semantic model S = <E, M, R, P, κ> as a typed labeled graph.
    Backed by NetworkX DiGraph.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities = {}      # name -> entity dict
        self.metrics = {}       # name -> metric dict
        self.relationships = [] # list of relationship dicts
        self.policies = []      # list of policy dicts
        self.aliases = {}       # alias -> canonical name
        self._frozen = False

    def add_entity(self, name: str, aliases: List[str], source_tables: List[str],
                   key_column: str = None, confidence: float = 0.5, pii_flag: bool = False):
        """Add a business entity to the semantic model."""
        entity = {
            'name': name,
            'aliases': aliases,
            'source_tables': source_tables,
            'key_column': key_column,
            'confidence': confidence,
            'pii_flag': pii_flag,
            'type': 'Entity',
        }
        self.entities[name] = entity
        self.graph.add_node(name, **entity)

        # Register aliases
        for alias in aliases:
            self.aliases[alias.lower()] = name

    def add_metric(self, name: str, aliases: List[str], formula: str, unit: str,
                   source_columns: List[str], confidence: float = 0.5):
        """Add a business metric to the semantic model."""
        metric = {
            'name': name,
            'aliases': aliases,
            'formula': formula,
            'unit': unit,
            'source_columns': source_columns,
            'confidence': confidence,
            'type': 'Metric',
        }
        self.metrics[name] = metric
        self.graph.add_node(name, **metric)

        for alias in aliases:
            self.aliases[alias.lower()] = name

    def add_relationship(self, from_entity: str, to_entity: str, rel_type: str,
                        join_key: str = None, confidence: float = 0.5):
        """Add a typed relationship (edge) between entities/metrics."""
        rel = {
            'from': from_entity,
            'to': to_entity,
            'type': rel_type,
            'join_key': join_key,
            'confidence': confidence,
        }
        self.relationships.append(rel)
        self.graph.add_edge(from_entity, to_entity, **rel)

    def add_policy(self, policy_type: str, rule: str, scope: str, priority: int = 1):
        """Add a governance policy."""
        policy = {
            'type': policy_type,
            'rule': rule,
            'scope': scope,
            'priority': priority,
        }
        self.policies.append(policy)

    def get_confidence(self, element_name: str) -> float:
        """Get confidence κ for any element."""
        if element_name in self.entities:
            return self.entities[element_name]['confidence']
        if element_name in self.metrics:
            return self.metrics[element_name]['confidence']
        return 0.0

    def update_confidence(self, element_name: str, confirmed: bool, alpha: float = 0.15):
        """Update confidence via Equation 1: κ_{t+1} = (1-α)·κ_t + α·𝟙[confirm]."""
        if self._frozen:
            return

        target = None
        if element_name in self.entities:
            target = self.entities[element_name]
        elif element_name in self.metrics:
            target = self.metrics[element_name]

        if target:
            old_k = target['confidence']
            target['confidence'] = (1 - alpha) * old_k + alpha * (1.0 if confirmed else 0.0)
            # Update graph node too
            if element_name in self.graph:
                self.graph.nodes[element_name]['confidence'] = target['confidence']

    def resolve_alias(self, term: str) -> Optional[str]:
        """Resolve a business term to its canonical entity/metric name."""
        term_lower = term.lower()
        if term_lower in self.aliases:
            return self.aliases[term_lower]
        # Check entity/metric names directly
        for name in list(self.entities.keys()) + list(self.metrics.keys()):
            if name.lower() == term_lower:
                return name
        return None

    def get_join_path(self, entity_a: str, entity_b: str) -> Optional[List[dict]]:
        """Find join path between two entities via the semantic graph."""
        try:
            path = nx.shortest_path(self.graph.to_undirected(), entity_a, entity_b)
            edges = []
            for i in range(len(path) - 1):
                if self.graph.has_edge(path[i], path[i+1]):
                    edges.append(self.graph.edges[path[i], path[i+1]])
                elif self.graph.has_edge(path[i+1], path[i]):
                    edges.append(self.graph.edges[path[i+1], path[i]])
            return edges
        except (nx.NetworkXError, nx.NodeNotFound):
            return None

    def get_sources_for_query(self, entities_needed: List[str]) -> List[str]:
        """Determine which data sources are needed for a set of entities."""
        sources = set()
        for ent_name in entities_needed:
            ent = self.entities.get(ent_name)
            if ent:
                for table in ent['source_tables']:
                    # Extract source prefix
                    if table.startswith('sf_') or table.startswith('sf.'):
                        sources.add('salesforce')
                    elif table.startswith('logistics') or table.startswith('log.'):
                        sources.add('logistics')
                    else:
                        sources.add('postgres')
        return list(sources)

    def to_summary(self, confidence_threshold: float = 0.0) -> str:
        """Generate a text summary for LLM prompt injection."""
        lines = ["=== SEMANTIC MODEL SUMMARY ===\n"]

        lines.append("ENTITIES:")
        for name, ent in self.entities.items():
            if ent['confidence'] >= confidence_threshold:
                aliases_str = ', '.join(ent['aliases']) if ent['aliases'] else 'none'
                lines.append(f"  - {name} (aliases: {aliases_str}) → tables: {ent['source_tables']} [κ={ent['confidence']:.2f}]")

        lines.append("\nMETRICS:")
        for name, met in self.metrics.items():
            if met['confidence'] >= confidence_threshold:
                lines.append(f"  - {name}: {met['formula']} ({met['unit']}) [κ={met['confidence']:.2f}]")

        lines.append("\nRELATIONSHIPS:")
        for rel in self.relationships:
            if rel['confidence'] >= confidence_threshold:
                lines.append(f"  - {rel['from']} --[{rel['type']}]--> {rel['to']} via {rel.get('join_key', 'N/A')} [κ={rel['confidence']:.2f}]")

        lines.append("\nPOLICIES:")
        for pol in self.policies:
            lines.append(f"  - [{pol['type']}] {pol['rule']} (scope: {pol['scope']})")

        return '\n'.join(lines)

    def to_json(self) -> str:
        """Serialize to JSON for prompt injection."""
        return json.dumps({
            'entities': list(self.entities.values()),
            'metrics': list(self.metrics.values()),
            'relationships': self.relationships,
            'policies': self.policies,
        }, indent=2, default=str)

    def freeze(self):
        """Freeze the model — no more confidence updates (for ABL-NoFeedback)."""
        self._frozen = True

    def unfreeze(self):
        """Unfreeze the model."""
        self._frozen = False

    def get_elements_needing_review(self, threshold: float = 0.75) -> List[dict]:
        """Get elements with κ < threshold for human-in-the-loop review."""
        needs_review = []
        for name, ent in self.entities.items():
            if ent['confidence'] < threshold:
                needs_review.append({'type': 'entity', **ent})
        for name, met in self.metrics.items():
            if met['confidence'] < threshold:
                needs_review.append({'type': 'metric', **met})
        return needs_review

    @classmethod
    def from_json(cls, json_str: str) -> 'SemanticModel':
        """Deserialize from JSON."""
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        model = cls()
        for ent in data.get('entities', []):
            model.add_entity(
                name=ent['name'],
                aliases=ent.get('aliases', []),
                source_tables=ent.get('source_tables', []),
                key_column=ent.get('key_column'),
                confidence=ent.get('confidence', 0.5),
                pii_flag=ent.get('pii_flag', False),
            )
        for met in data.get('metrics', []):
            model.add_metric(
                name=met['name'],
                aliases=met.get('aliases', []),
                formula=met.get('formula', ''),
                unit=met.get('unit', ''),
                source_columns=met.get('source_columns', []),
                confidence=met.get('confidence', 0.5),
            )
        for rel in data.get('relationships', []):
            model.add_relationship(
                from_entity=rel['from'],
                to_entity=rel['to'],
                rel_type=rel.get('type', 'Related'),
                join_key=rel.get('join_key'),
                confidence=rel.get('confidence', 0.5),
            )
        for pol in data.get('policies', []):
            model.add_policy(
                policy_type=pol['type'],
                rule=pol['rule'],
                scope=pol['scope'],
                priority=pol.get('priority', 1),
            )
        return model


def synthesize_semantic_model(conn, llm_client, schema_ddl: str) -> SemanticModel:
    """
    f_synth: D → S
    Automatically construct a semantic model from raw data sources.
    Uses LLM for concept inference, confidence scoring via embeddings.
    """
    from src.prompts import SEMANTIC_PROFILER_PROMPT
    from src.data_generator import get_sample_data, get_column_stats

    model = SemanticModel()

    # Get all tables
    tables = conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]

    # Profile each table
    all_profiles = []
    for table in table_names:
        sample = get_sample_data(conn, table, n=5)
        stats = get_column_stats(conn, table)
        all_profiles.append({
            'table': table,
            'sample': sample,
            'stats': stats,
        })

    # LLM-based semantic inference
    combined_schema = schema_ddl
    combined_samples = '\n\n'.join([
        f"--- Table: {p['table']} ---\n{p['sample']}" for p in all_profiles
    ])
    combined_stats = json.dumps(
        {p['table']: p['stats'] for p in all_profiles}, indent=2, default=str
    )

    prompt = SEMANTIC_PROFILER_PROMPT.format(
        schema_info=combined_schema,
        sample_data=combined_samples,
        column_stats=combined_stats,
    )

    try:
        response = llm_client.generate_content(prompt)
        # Parse LLM response
        response_text = response.text if hasattr(response, 'text') else str(response)
        # Extract JSON from response
        json_match = _extract_json(response_text)
        if json_match:
            inferred = json.loads(json_match)
        else:
            inferred = {'entities': [], 'metrics': [], 'relationships': [], 'cross_source_hints': []}
    except Exception as e:
        print(f"⚠️ LLM semantic inference failed: {e}")
        inferred = {'entities': [], 'metrics': [], 'relationships': [], 'cross_source_hints': []}

    # Build model from LLM output
    for ent in inferred.get('entities', []):
        model.add_entity(
            name=ent.get('name', 'Unknown'),
            aliases=ent.get('aliases', []),
            source_tables=[ent.get('source_table', '')] if isinstance(ent.get('source_table'), str)
                          else ent.get('source_tables', ent.get('source_table', [])),
            key_column=ent.get('key_column'),
            confidence=float(ent.get('confidence', 0.5)),
        )

    for met in inferred.get('metrics', []):
        model.add_metric(
            name=met.get('name', 'Unknown'),
            aliases=met.get('aliases', []),
            formula=met.get('formula', ''),
            unit=met.get('unit', ''),
            source_columns=met.get('source_columns', []),
            confidence=float(met.get('confidence', 0.5)),
        )

    for rel in inferred.get('relationships', []):
        model.add_relationship(
            from_entity=rel.get('from_entity', rel.get('from', '')),
            to_entity=rel.get('to_entity', rel.get('to', '')),
            rel_type=rel.get('type', 'Related'),
            join_key=rel.get('join_key'),
            confidence=float(rel.get('confidence', 0.5)),
        )

    # Add default governance policies
    model.add_policy('pii', 'Mask email columns in output', 'customers.email, sf_accounts.email_address', 1)
    model.add_policy('access', 'Require authentication for all queries', 'global', 1)
    model.add_policy('compute', 'Reject full table scans > 100K rows', 'global', 2)

    return model


def build_gold_semantic_model() -> SemanticModel:
    """
    Build the gold (ground truth) semantic model manually.
    Used as the reference for Experiment 2 synthesis quality evaluation.
    """
    model = SemanticModel()

    # --- Entities ---
    model.add_entity('Customer', ['client', 'account', 'buyer', 'purchaser'],
                     ['customers', 'sf_accounts'], 'id', confidence=1.0,
                     pii_flag=True)
    model.add_entity('Order', ['purchase', 'transaction', 'sale'],
                     ['orders'], 'id', confidence=1.0)
    model.add_entity('Product', ['item', 'SKU', 'merchandise', 'goods'],
                     ['products'], 'id', confidence=1.0)
    model.add_entity('OrderItem', ['line item', 'order line'],
                     ['order_items'], 'id', confidence=1.0)
    model.add_entity('SalesRep', ['salesperson', 'sales representative', 'rep', 'account executive'],
                     ['sales_reps'], 'id', confidence=1.0)
    model.add_entity('Return', ['refund', 'return request'],
                     ['returns'], 'id', confidence=1.0)
    model.add_entity('Deal', ['opportunity', 'CRM deal', 'pipeline deal'],
                     ['sf_opportunities'], 'opp_id', confidence=1.0)
    model.add_entity('SalesforceAccount', ['SF account', 'CRM account'],
                     ['sf_accounts'], 'account_id', confidence=1.0)
    model.add_entity('Delivery', ['shipment', 'logistics event', 'shipping'],
                     ['logistics_deliveries'], 'tracking_id', confidence=1.0)

    # --- Metrics ---
    model.add_metric('Revenue', ['gross revenue', 'sales', 'total revenue', 'income', 'line value'],
                     'SUM(orders.line_value)', 'USD',
                     ['orders.line_value'], confidence=1.0)
    model.add_metric('OrderCount', ['number of orders', 'order volume', 'total orders'],
                     'COUNT(orders.id)', 'count',
                     ['orders.id'], confidence=1.0)
    model.add_metric('AverageOrderValue', ['AOV', 'avg order value', 'average order size'],
                     'AVG(orders.line_value)', 'USD',
                     ['orders.line_value'], confidence=1.0)
    model.add_metric('CustomerCount', ['number of customers', 'unique customers'],
                     'COUNT(DISTINCT orders.customer_id)', 'count',
                     ['orders.customer_id'], confidence=1.0)
    model.add_metric('ReturnRate', ['return percentage', 'refund rate'],
                     'COUNT(CASE WHEN status=returned) / COUNT(*)', 'percentage',
                     ['orders.status'], confidence=1.0)
    model.add_metric('DeliveryDelayDays', ['shipping delay', 'late delivery days'],
                     'delivery_date - expected_date', 'days',
                     ['logistics_deliveries.delivery_date', 'logistics_deliveries.expected_date'],
                     confidence=1.0)
    model.add_metric('DealSize', ['deal amount', 'opportunity value', 'deal value'],
                     'sf_opportunities.amount', 'USD',
                     ['sf_opportunities.amount'], confidence=1.0)
    model.add_metric('COGS', ['cost of goods sold', 'cost of sales'],
                     'SUM(products.cost_price * orders.quantity)', 'USD',
                     ['products.cost_price', 'orders.quantity'], confidence=1.0)

    # --- Within-source Relationships ---
    model.add_relationship('Order', 'Customer', 'PlacedBy',
                          'orders.customer_id = customers.id', confidence=1.0)
    model.add_relationship('Order', 'Product', 'Contains',
                          'orders.product_id = products.id', confidence=1.0)
    model.add_relationship('Order', 'SalesRep', 'ManagedBy',
                          'orders.sales_rep_id = sales_reps.id', confidence=1.0)
    model.add_relationship('OrderItem', 'Order', 'BelongsTo',
                          'order_items.order_id = orders.id', confidence=1.0)
    model.add_relationship('OrderItem', 'Product', 'References',
                          'order_items.product_id = products.id', confidence=1.0)
    model.add_relationship('Return', 'Order', 'RefundsOrder',
                          'returns.order_id = orders.id', confidence=1.0)
    model.add_relationship('Deal', 'SalesforceAccount', 'OwnedBy',
                          'sf_opportunities.account_id = sf_accounts.account_id', confidence=1.0)

    # --- Cross-source Relationships (the key differentiator) ---
    model.add_relationship('Customer', 'SalesforceAccount', 'SynonymousWith',
                          'customers.email = sf_accounts.email_address', confidence=0.85)
    model.add_relationship('Order', 'Delivery', 'ShippedVia',
                          'orders.shipping_id = logistics_deliveries.shipping_ref', confidence=0.80)
    model.add_relationship('Customer', 'Deal', 'HasOpportunity',
                          'customers.email = sf_accounts.email_address AND sf_accounts.account_id = sf_opportunities.account_id',
                          confidence=0.75)

    # --- Governance Policies ---
    model.add_policy('pii', 'Mask email addresses in query output', 'customers.email, sf_accounts.email_address')
    model.add_policy('access', 'All queries require authenticated user context', 'global')
    model.add_policy('compute', 'Block full table scans exceeding 100,000 rows without WHERE clause', 'global')

    # --- Metric-Entity Links ---
    model.add_relationship('Revenue', 'Order', 'DerivedFrom',
                          'SUM(orders.line_value)', confidence=1.0)
    model.add_relationship('Revenue', 'Product', 'SliceableBy',
                          'orders.product_id = products.id', confidence=1.0)
    model.add_relationship('Revenue', 'Customer', 'SliceableBy',
                          'orders.customer_id = customers.id', confidence=1.0)

    return model


def measure_synthesis_quality(auto_model: SemanticModel, gold_model: SemanticModel) -> dict:
    """
    Compare automatically inferred S against gold semantic model.
    Returns coverage, precision, F1 metrics for Experiment 2.
    """
    auto_entities = set(auto_model.entities.keys())
    gold_entities = set(gold_model.entities.keys())

    auto_metrics = set(auto_model.metrics.keys())
    gold_metrics = set(gold_model.metrics.keys())

    # Also check alias-based matching (LLM might use different canonical names)
    auto_entity_aliases = set()
    for ent in auto_model.entities.values():
        auto_entity_aliases.add(ent['name'].lower())
        for alias in ent.get('aliases', []):
            auto_entity_aliases.add(alias.lower())

    gold_entity_aliases = set()
    for ent in gold_model.entities.values():
        gold_entity_aliases.add(ent['name'].lower())
        for alias in ent.get('aliases', []):
            gold_entity_aliases.add(alias.lower())

    # Fuzzy entity matching
    entity_matches = auto_entity_aliases & gold_entity_aliases
    entity_precision = len(entity_matches) / max(len(auto_entity_aliases), 1)
    entity_recall = len(entity_matches) / max(len(gold_entity_aliases), 1)
    entity_f1 = (2 * entity_precision * entity_recall / max(entity_precision + entity_recall, 1e-9))

    # Metric matching (strict name match)
    metric_matches = auto_metrics & gold_metrics
    metric_coverage = len(metric_matches) / max(len(gold_metrics), 1)

    # Cross-source relationships
    auto_rels = set((r['from'] + '->' + r['to']) for r in auto_model.relationships)
    gold_rels = set((r['from'] + '->' + r['to']) for r in gold_model.relationships)
    cross_source_gold = set(
        (r['from'] + '->' + r['to']) for r in gold_model.relationships
        if r.get('type') in ['SynonymousWith', 'ShippedVia', 'HasOpportunity']
    )
    cross_source_auto = auto_rels & cross_source_gold
    cross_source_coverage = len(cross_source_auto) / max(len(cross_source_gold), 1)

    # High-confidence subset (κ ≥ 0.80)
    high_conf_entities = [e for e in auto_model.entities.values() if e.get('confidence', 0) >= 0.80]
    high_conf_count = len(high_conf_entities)

    return {
        'entities_inferred': len(auto_entities),
        'entities_gold': len(gold_entities),
        'entity_coverage': round(entity_recall, 4),
        'entity_precision': round(entity_precision, 4),
        'entity_f1': round(entity_f1, 4),
        'metrics_inferred': len(auto_metrics),
        'metrics_gold': len(gold_metrics),
        'metric_coverage': round(metric_coverage, 4),
        'cross_source_rels_inferred': len(auto_rels & gold_rels),
        'cross_source_rels_gold': len(cross_source_gold),
        'cross_source_rel_coverage': round(cross_source_coverage, 4),
        'high_confidence_entities': high_conf_count,
        'mapping_f1_high_conf': round(entity_f1, 4),  # Will be refined with actual κ-filtered F1
    }


def _extract_json(text: str) -> Optional[str]:
    """Extract JSON from LLM response (may be wrapped in code blocks)."""
    import re
    # Try to find JSON in code blocks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    # Try to find raw JSON
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None
