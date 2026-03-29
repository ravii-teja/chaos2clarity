"""
Chaos 2 Clarity — Mechanism IV: Feedback-Driven Continuous Learning Loop
Implements δ: S × F → S — updating the semantic model from feedback events.
Four signal types: f_sql, f_usr, f_qrm, f_ins.
"""

import json
import time
from typing import Dict, List, Optional, Any
from collections import defaultdict


class FeedbackLoop:
    """
    The feedback loop δ that makes C2C self-improving.
    Processes four signal types and routes updates to:
    - Schema enrichment (semantic model κ, aliases, formulas)
    - Prompt refinement (few-shot examples injected per error class)
    - Embedding updates (synonyms → re-embed affected V entries)
    - Rule injection (repeated policy violations → persistent rules)
    """

    def __init__(self, alpha: float = 0.15, batch_threshold: int = 10):
        self.alpha = alpha
        self.batch_threshold = batch_threshold

        # Feedback stores
        self.f_sql_log = []          # SQL execution outcomes
        self.f_usr_log = []          # User corrections
        self.f_qrm_log = []         # Query-result mismatches
        self.f_ins_log = []          # Insight usefulness ratings

        # Failure pattern accumulator Φ
        self.failure_patterns = defaultdict(list)  # error_class -> [pattern_dicts]

        # Prompt refinement store
        self.refined_examples = defaultdict(list)  # agent_stage -> [few_shot_examples]

        # Schema enrichment proposals
        self.enrichment_proposals = []

        # Statistics
        self.total_signals = 0
        self.updates_applied = 0
        self._enabled = True

    def disable(self):
        """Disable feedback processing (for ABL-NoFeedback)."""
        self._enabled = False

    def enable(self):
        """Enable feedback processing."""
        self._enabled = True

    @property
    def is_enabled(self):
        return self._enabled

    # ─────────────────────────────────────────────
    # Signal Ingestion
    # ─────────────────────────────────────────────

    def emit_sql_signal(self, query: str, sql: str, success: bool,
                        error_class: Optional[str] = None, error_msg: str = "",
                        entities_used: List[str] = None):
        """f_sql: SQL execution outcome signal."""
        if not self._enabled:
            return

        signal = {
            'type': 'f_sql',
            'query': query,
            'sql': sql,
            'success': success,
            'error_class': error_class,
            'error_msg': error_msg,
            'entities_used': entities_used or [],
            'timestamp': time.time(),
        }
        self.f_sql_log.append(signal)
        self.total_signals += 1

        if not success and error_class:
            self.failure_patterns[error_class].append(signal)

    def emit_user_correction(self, query: str, original_sql: str, corrected_sql: str,
                             correction_type: str = "sql_fix",
                             new_synonyms: Dict[str, str] = None):
        """f_usr: User correction signal."""
        if not self._enabled:
            return

        signal = {
            'type': 'f_usr',
            'query': query,
            'original_sql': original_sql,
            'corrected_sql': corrected_sql,
            'correction_type': correction_type,
            'new_synonyms': new_synonyms or {},
            'timestamp': time.time(),
        }
        self.f_usr_log.append(signal)
        self.total_signals += 1

    def emit_qrm_signal(self, query: str, sql: str, result: Any,
                        mismatch_type: str = "aggregation"):
        """f_qrm: Query-result mismatch signal (from Insight Agent)."""
        if not self._enabled:
            return

        signal = {
            'type': 'f_qrm',
            'query': query,
            'sql': sql,
            'result_summary': str(result)[:200],
            'mismatch_type': mismatch_type,
            'timestamp': time.time(),
        }
        self.f_qrm_log.append(signal)
        self.total_signals += 1
        self.failure_patterns['E2'].append(signal)

    def emit_insight_signal(self, query: str, usefulness_score: float,
                           entry_id: Optional[str] = None):
        """f_ins: Insight usefulness rating signal."""
        if not self._enabled:
            return

        signal = {
            'type': 'f_ins',
            'query': query,
            'usefulness_score': usefulness_score,
            'entry_id': entry_id,
            'timestamp': time.time(),
        }
        self.f_ins_log.append(signal)
        self.total_signals += 1

    # ─────────────────────────────────────────────
    # Batch Processing (between query batches)
    # ─────────────────────────────────────────────

    def process_feedback_batch(self, semantic_model, vector_store=None):
        """
        Process accumulated feedback signals and apply updates.
        Called between batches in Experiment 5.

        Updates:
        1. Schema enrichment (κ updates for confirmed/rejected entities)
        2. Prompt refinement (few-shot examples for error classes at threshold)
        3. Embedding updates (synonyms from user corrections)
        4. Rule injection (repeated policy violations)
        """
        if not self._enabled:
            return {'updates': 0, 'reason': 'feedback disabled'}

        updates = 0

        # 1. Schema Enrichment — Update κ from f_sql signals
        for signal in self.f_sql_log:
            for entity_name in signal.get('entities_used', []):
                semantic_model.update_confidence(
                    entity_name,
                    confirmed=signal['success'],
                    alpha=self.alpha
                )
                updates += 1

        # 2. Prompt Refinement — Generate few-shot examples for frequent error classes
        for error_class, patterns in self.failure_patterns.items():
            if len(patterns) >= self.batch_threshold:
                examples = self._generate_few_shot_examples(error_class, patterns)
                self.refined_examples[error_class].extend(examples)
                updates += 1
                # Clear processed patterns (keep newer ones)
                self.failure_patterns[error_class] = patterns[-5:]  # keep recent 5 for context

        # 3. Embedding Updates — Process user corrections with new synonyms
        for signal in self.f_usr_log:
            for alias, canonical in signal.get('new_synonyms', {}).items():
                resolved = semantic_model.resolve_alias(canonical)
                if resolved:
                    # Add the new alias
                    if resolved in semantic_model.entities:
                        semantic_model.entities[resolved]['aliases'].append(alias)
                        semantic_model.aliases[alias.lower()] = resolved
                    elif resolved in semantic_model.metrics:
                        semantic_model.metrics[resolved]['aliases'].append(alias)
                        semantic_model.aliases[alias.lower()] = resolved
                    updates += 1

        # 4. Schema enrichment for E1 failures — Column re-profiling proposals
        e1_failures = self.failure_patterns.get('E1', [])
        if len(e1_failures) >= 3:
            # Extract column names that were hallucinated
            hallucinated_cols = set()
            for signal in e1_failures:
                error_msg = signal.get('error_msg', '')
                # Simple extraction — look for quoted column names in error
                import re
                cols = re.findall(r'"(\w+)"', error_msg)
                cols += re.findall(r"'(\w+)'", error_msg)
                hallucinated_cols.update(cols)

            for col in hallucinated_cols:
                self.enrichment_proposals.append({
                    'type': 'column_alias',
                    'hallucinated_name': col,
                    'frequency': len([s for s in e1_failures if col in s.get('error_msg', '')]),
                    'timestamp': time.time(),
                })
                updates += 1

        # 5. Vector store κ updates from f_ins signals
        if vector_store:
            for signal in self.f_ins_log:
                entry_id = signal.get('entry_id')
                if entry_id and signal['usefulness_score'] < 0.5:
                    vector_store.update_confidence(entry_id, confirmed=False, alpha=self.alpha)
                    updates += 1

        # Clear processed signals
        self.f_sql_log = []
        self.f_usr_log = []
        self.f_qrm_log = []
        self.f_ins_log = []

        self.updates_applied += updates

        return {
            'updates': updates,
            'refined_examples_count': sum(len(v) for v in self.refined_examples.values()),
            'enrichment_proposals': len(self.enrichment_proposals),
            'total_signals_processed': self.total_signals,
        }

    def _generate_few_shot_examples(self, error_class: str, patterns: list) -> list:
        """Generate few-shot correction examples from accumulated failure patterns."""
        examples = []

        if error_class == 'E1':
            # Column name hallucinations → correct column mapping examples
            for p in patterns[:3]:
                examples.append({
                    'error_class': 'E1',
                    'bad_query': p.get('sql', ''),
                    'error': p.get('error_msg', ''),
                    'correction_hint': 'Use actual column names from schema. Revenue is stored as line_value.',
                })

        elif error_class == 'E2':
            # Aggregation errors → correct function usage examples
            for p in patterns[:3]:
                examples.append({
                    'error_class': 'E2',
                    'query': p.get('query', ''),
                    'bad_sql': p.get('sql', ''),
                    'correction_hint': 'Verify aggregation function matches business meaning (SUM for total, AVG for average).',
                })

        elif error_class == 'E3':
            # Join path errors → correct join examples
            for p in patterns[:3]:
                examples.append({
                    'error_class': 'E3',
                    'bad_sql': p.get('sql', ''),
                    'correction_hint': 'Check join keys in semantic model. Cross-source joins require email matching.',
                })

        return examples

    def get_prompt_refinements(self, agent_stage: str = None) -> str:
        """Get accumulated few-shot examples for prompt injection.

        Returns formatted text to append to agent prompts.
        """
        if not self.refined_examples:
            return ""

        lines = ["\n=== LEARNED CORRECTIONS (from previous queries) ===\n"]

        relevant_classes = list(self.refined_examples.keys())
        if agent_stage == 'sql_generator':
            relevant_classes = [c for c in relevant_classes if c in ['E1', 'E2', 'E3']]
        elif agent_stage == 'planner':
            relevant_classes = [c for c in relevant_classes if c in ['E4', 'E5']]

        for error_class in relevant_classes:
            examples = self.refined_examples[error_class][-3:]  # Last 3 per class
            for ex in examples:
                lines.append(f"⚠️ Previous error ({error_class}): {ex.get('correction_hint', '')}")
                if ex.get('bad_sql'):
                    lines.append(f"   Bad SQL: {ex['bad_sql'][:100]}")
                lines.append("")

        return '\n'.join(lines) if len(lines) > 1 else ""

    def get_stats(self) -> dict:
        """Get feedback loop statistics."""
        return {
            'total_signals': self.total_signals,
            'updates_applied': self.updates_applied,
            'pending_f_sql': len(self.f_sql_log),
            'pending_f_usr': len(self.f_usr_log),
            'pending_f_qrm': len(self.f_qrm_log),
            'pending_f_ins': len(self.f_ins_log),
            'failure_patterns': {k: len(v) for k, v in self.failure_patterns.items()},
            'refined_examples': {k: len(v) for k, v in self.refined_examples.items()},
            'enrichment_proposals': len(self.enrichment_proposals),
            'enabled': self._enabled,
        }

    def reset(self):
        """Reset all feedback state (for experiment reset)."""
        self.f_sql_log = []
        self.f_usr_log = []
        self.f_qrm_log = []
        self.f_ins_log = []
        self.failure_patterns = defaultdict(list)
        self.refined_examples = defaultdict(list)
        self.enrichment_proposals = []
        self.total_signals = 0
        self.updates_applied = 0
