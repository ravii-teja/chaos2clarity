"""
Chaos 2 Clarity — Mechanism II: Agentic Query Orchestration Pipeline
Implements Algorithm 1: 6-stage Planner → Retriever → SQL Generator → Validator → Executor → Insight Agent.
"""

import json
import re
import time
import duckdb
from typing import Tuple, Any, Dict, Optional, List

from src.prompts import (
    PLANNER_SYSTEM_PROMPT, PLANNER_USER_TEMPLATE,
    SQL_GENERATOR_SYSTEM_PROMPT, SQL_GENERATOR_USER_TEMPLATE,
    VALIDATOR_SYSTEM_PROMPT, VALIDATOR_USER_TEMPLATE,
    INSIGHT_AGENT_SYSTEM_PROMPT, INSIGHT_AGENT_USER_TEMPLATE,
)


class C2CPipeline:
    """
    Full 6-stage C2C orchestration pipeline.
    Implements Algorithm 1 from the paper.
    """

    def __init__(self, llm_client, conn, semantic_model, vector_store,
                 feedback_loop, schema_ddl: str, max_retries: int = 1):
        self.llm = llm_client
        self.conn = conn
        self.semantic_model = semantic_model
        self.vector_store = vector_store
        self.feedback_loop = feedback_loop
        self.schema_ddl = schema_ddl
        self.max_retries = max_retries

        # Stage timing instrumentation
        self.stage_times = {
            'planner': [],
            'retriever': [],
            'sql_generator': [],
            'validator': [],
            'executor': [],
            'insight_agent': [],
        }

    def __call__(self, nl_prompt: str) -> Tuple[str, Any, dict]:
        """
        Main entry point. Runs Algorithm 1.

        Args:
            nl_prompt: Natural language BI question

        Returns:
            (generated_sql, result, metadata)
        """
        meta = {
            'retry_count': 0,
            'grounding_used': False,
            'grounding_sim': 0.0,
            'first_pass': False,
            'cross_source_planned': False,
            'stage_times': {},
        }

        # Stage 1: Planner
        t0 = time.perf_counter()
        plan = self._planner(nl_prompt)
        meta['stage_times']['planner'] = (time.perf_counter() - t0) * 1000
        meta['cross_source_planned'] = plan.get('cross_source_planned', False)

        # Stage 2: Retriever
        t0 = time.perf_counter()
        grounding = self._retriever(nl_prompt)
        meta['stage_times']['retriever'] = (time.perf_counter() - t0) * 1000
        if grounding:
            meta['grounding_used'] = True
            meta['grounding_sim'] = max(g.get('similarity', 0) for g in grounding)

        # Retry loop (Lines 4-22 of Algorithm 1)
        error_ctx = ""
        for attempt in range(self.max_retries + 1):
            # Stage 3: SQL Generator
            t0 = time.perf_counter()
            sql = self._sql_generator(nl_prompt, plan, grounding, error_ctx)
            meta['stage_times']['sql_generator'] = (time.perf_counter() - t0) * 1000

            # Stage 4: Validator
            t0 = time.perf_counter()
            approved, validation = self._validator(sql)
            meta['stage_times']['validator'] = (time.perf_counter() - t0) * 1000

            if not approved:
                # Policy violation — emit feedback and return failure
                self.feedback_loop.emit_sql_signal(
                    nl_prompt, sql, success=False,
                    error_class='E3', error_msg='Policy violation: ' + str(validation.get('violations', []))
                )
                if validation.get('modified_query'):
                    sql = validation['modified_query']
                else:
                    return sql, {'error': 'Policy violation', 'violations': validation.get('violations', [])}, meta

            # Stage 5: Executor
            t0 = time.perf_counter()
            result, error = self._executor(sql)
            meta['stage_times']['executor'] = (time.perf_counter() - t0) * 1000

            if error is None:
                # Success!
                if attempt == 0:
                    meta['first_pass'] = True

                # Stage 6: Insight Agent
                t0 = time.perf_counter()
                insight = self._insight_agent(nl_prompt, result, sql)
                meta['stage_times']['insight_agent'] = (time.perf_counter() - t0) * 1000

                # Write to vector store (Algorithm 1, Line 14)
                entry_id = self.vector_store.add_verified_plan(
                    query_normalized=nl_prompt.lower().strip(),
                    plan=plan,
                    sql_verified=sql,
                    result_gold=result,
                )

                # Emit success feedback (Algorithm 1, Line 15)
                entities_used = plan.get('entities', [])
                self.feedback_loop.emit_sql_signal(
                    nl_prompt, sql, success=True, entities_used=entities_used
                )
                if insight.get('usefulness_score', 1.0) < 0.5:
                    self.feedback_loop.emit_insight_signal(
                        nl_prompt, insight.get('usefulness_score', 0.5), entry_id
                    )
                if insight.get('feedback_signals', {}).get('f_qrm', 0):
                    self.feedback_loop.emit_qrm_signal(nl_prompt, sql, result)

                meta['retry_count'] = attempt
                return sql, result, meta

            else:
                # Failure — extract error context for retry
                error_ctx = str(error)
                meta['retry_count'] = attempt + 1

                # Emit failure feedback (Algorithm 1, Line 19)
                self.feedback_loop.emit_sql_signal(
                    nl_prompt, sql, success=False,
                    error_class=_classify_error_quick(error_ctx),
                    error_msg=error_ctx,
                    entities_used=plan.get('entities', [])
                )

        # Max retries exceeded (Algorithm 1, Line 23)
        return sql, {'error': f'Max retries ({self.max_retries}) exceeded', 'last_error': error_ctx}, meta

    def _planner(self, nl_prompt: str) -> dict:
        """Stage 1: Classify intent + build execution plan."""
        prompt_refinements = self.feedback_loop.get_prompt_refinements('planner')

        user_msg = PLANNER_USER_TEMPLATE.format(
            user_question=nl_prompt,
            sm_summary=self.semantic_model.to_summary(confidence_threshold=0.3),
            grounding_plans="(retrieved in next stage)",
            active_policies=json.dumps(self.semantic_model.policies, default=str),
        )

        full_system = PLANNER_SYSTEM_PROMPT
        if prompt_refinements:
            full_system += "\n" + prompt_refinements

        try:
            response = self.llm.generate_content(
                [{'role': 'user', 'parts': [full_system + "\n\n" + user_msg]}]
            )
            text = response.text if hasattr(response, 'text') else str(response)
            plan = _extract_json_safe(text)
            return plan if plan else {'task_type': 'other', 'entities': [], 'metrics': [],
                                      'plan_steps': [], 'confidence': 0.5,
                                      'cross_source_planned': False}
        except Exception as e:
            return {'task_type': 'other', 'entities': [], 'metrics': [],
                    'plan_steps': [], 'confidence': 0.0, 'error': str(e),
                    'cross_source_planned': False}

    def _retriever(self, nl_prompt: str, k: int = 5) -> list:
        """Stage 2: Fetch k verified grounding plans from V."""
        return self.vector_store.retrieve(nl_prompt, k=k)

    def _sql_generator(self, nl_prompt: str, plan: dict, grounding: list,
                       error_ctx: str = "") -> str:
        """Stage 3: Generate SQL conditioned on plan + grounding context."""
        prompt_refinements = self.feedback_loop.get_prompt_refinements('sql_generator')
        grounding_text = self.vector_store.format_grounding_context(grounding)

        user_msg = SQL_GENERATOR_USER_TEMPLATE.format(
            execution_plan=json.dumps(plan, default=str),
            sm_json=self.semantic_model.to_json(),
            schema_ddl=self.schema_ddl,
            verified_sql_examples=grounding_text,
            error_ctx=error_ctx if error_ctx else "None (first attempt)",
            nl_prompt=nl_prompt,
        )

        full_system = SQL_GENERATOR_SYSTEM_PROMPT
        if prompt_refinements:
            full_system += "\n" + prompt_refinements

        try:
            response = self.llm.generate_content(
                [{'role': 'user', 'parts': [full_system + "\n\n" + user_msg]}]
            )
            text = response.text if hasattr(response, 'text') else str(response)
            sql = _extract_sql(text)
            return sql
        except Exception as e:
            return f"-- SQL generation error: {e}"

    def _validator(self, sql: str) -> Tuple[bool, dict]:
        """Stage 4: Semantic consistency + policy check."""
        user_msg = VALIDATOR_USER_TEMPLATE.format(
            proposed_sql=sql,
            sm_summary=self.semantic_model.to_summary(),
            schema_ddl=self.schema_ddl,
            policies=json.dumps(self.semantic_model.policies, default=str),
        )

        try:
            response = self.llm.generate_content(
                [{'role': 'user', 'parts': [VALIDATOR_SYSTEM_PROMPT.format(max_rows=100000) + "\n\n" + user_msg]}]
            )
            text = response.text if hasattr(response, 'text') else str(response)
            validation = _extract_json_safe(text)
            if validation:
                return validation.get('approved', True), validation
            return True, {}
        except Exception:
            # If validator fails, approve by default (fail-open)
            return True, {}

    def _executor(self, sql: str) -> Tuple[Any, Optional[str]]:
        """Stage 5: Execute SQL against DuckDB."""
        try:
            sql_clean = _extract_sql(sql)
            result = self.conn.execute(sql_clean).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            # Return as list of dicts
            rows = [dict(zip(columns, row)) for row in result]
            return rows, None
        except Exception as e:
            return None, str(e)

    def _insight_agent(self, nl_prompt: str, result: Any, sql: str) -> dict:
        """Stage 6: Generate narrative insight + emit feedback signals."""
        user_msg = INSIGHT_AGENT_USER_TEMPLATE.format(
            nl_prompt=nl_prompt,
            result_set=json.dumps(result[:10] if isinstance(result, list) else result, default=str),
            provenance=sql,
        )

        try:
            response = self.llm.generate_content(
                [{'role': 'user', 'parts': [INSIGHT_AGENT_SYSTEM_PROMPT + "\n\n" + user_msg]}]
            )
            text = response.text if hasattr(response, 'text') else str(response)
            insight = _extract_json_safe(text)
            return insight if insight else {'narrative': text, 'usefulness_score': 0.7,
                                           'feedback_signals': {'f_qrm': 0, 'f_ins': 0.7}}
        except Exception:
            return {'narrative': '', 'usefulness_score': 0.5,
                    'feedback_signals': {'f_qrm': 0, 'f_ins': 0.5}}

    def apply_feedback_batch(self):
        """Process accumulated feedback (called between experimental batches)."""
        return self.feedback_loop.process_feedback_batch(
            self.semantic_model, self.vector_store
        )

    def reset_state(self):
        """Reset vector store and feedback for fresh experiment run."""
        self.vector_store.clear()
        self.feedback_loop.reset()
        self.stage_times = {k: [] for k in self.stage_times}

    def get_stage_latency_stats(self) -> dict:
        """Get stage-level latency for Experiment 8."""
        import numpy as np
        stats = {}
        for stage, times in self.stage_times.items():
            if times:
                stats[stage] = {
                    'p50': np.median(times),
                    'p95': np.percentile(times, 95) if len(times) >= 20 else max(times),
                    'mean': np.mean(times),
                    'count': len(times),
                }
        return stats


# ─────────────────────────────────────────────
# Ablation Variants (built as wrappers/modifications)
# ─────────────────────────────────────────────

class C2CNoPlanner(C2CPipeline):
    """ABL-NoPlanner: Skip planning stage."""
    def _planner(self, nl_prompt: str) -> dict:
        return {'task_type': 'unknown', 'entities': [], 'metrics': [],
                'plan_steps': [{'step': 'direct_sql', 'data_source': 'all'}],
                'confidence': 0.0, 'cross_source_planned': False}


class C2CNoValidator(C2CPipeline):
    """ABL-NoValidator: Validator always approves."""
    def _validator(self, sql: str) -> Tuple[bool, dict]:
        return True, {'approved': True, 'violations': [], 'warnings': []}


class C2CNoRetry(C2CPipeline):
    """ABL-NoRetry: K=0, no retry loop."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = 0


class C2CNoVector(C2CPipeline):
    """ABL-NoVector: Vector store retrieval disabled (G = ∅)."""
    def _retriever(self, nl_prompt: str, k: int = 5) -> list:
        return []  # Always return empty grounding context


class C2CNoFeedback(C2CPipeline):
    """ABL-NoFeedback: α=0, S frozen, V not updated."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback_loop.disable()
        self.semantic_model.freeze()

    def __call__(self, nl_prompt: str) -> Tuple[str, Any, dict]:
        # Run pipeline but don't write to V or update S
        meta = {
            'retry_count': 0,
            'grounding_used': False,
            'grounding_sim': 0.0,
            'first_pass': False,
            'cross_source_planned': False,
            'stage_times': {},
        }

        plan = self._planner(nl_prompt)
        meta['cross_source_planned'] = plan.get('cross_source_planned', False)
        grounding = self._retriever(nl_prompt)

        error_ctx = ""
        for attempt in range(self.max_retries + 1):
            sql = self._sql_generator(nl_prompt, plan, grounding, error_ctx)
            approved, _ = self._validator(sql)
            if not approved:
                return sql, {'error': 'Policy violation'}, meta

            result, error = self._executor(sql)
            if error is None:
                if attempt == 0:
                    meta['first_pass'] = True
                meta['retry_count'] = attempt
                # Do NOT write to V, do NOT emit feedback
                return sql, result, meta
            else:
                error_ctx = str(error)
                meta['retry_count'] = attempt + 1

        return sql, {'error': f'Max retries exceeded', 'last_error': error_ctx}, meta


class C2CMonolithic:
    """ABL-Mono: Single LLM call with full S context, no decomposition."""

    def __init__(self, llm_client, conn, semantic_model, schema_ddl: str):
        self.llm = llm_client
        self.conn = conn
        self.semantic_model = semantic_model
        self.schema_ddl = schema_ddl

    def __call__(self, nl_prompt: str) -> Tuple[str, Any, dict]:
        from src.prompts import ABL_MONO_SYSTEM_PROMPT, ABL_MONO_USER_TEMPLATE

        meta = {
            'retry_count': 0,
            'grounding_used': False,
            'grounding_sim': 0.0,
            'first_pass': False,
            'cross_source_planned': False,
        }

        user_msg = ABL_MONO_USER_TEMPLATE.format(
            full_sm_json=self.semantic_model.to_json(),
            raw_schema_ddl=self.schema_ddl,
            nl_prompt=nl_prompt,
        )

        try:
            response = self.llm.generate_content(
                [{'role': 'user', 'parts': [ABL_MONO_SYSTEM_PROMPT + "\n\n" + user_msg]}]
            )
            text = response.text if hasattr(response, 'text') else str(response)
            sql = _extract_sql(text)

            result, error = self._execute(sql)
            if error is None:
                meta['first_pass'] = True
                return sql, result, meta
            else:
                return sql, Exception(error), meta
        except Exception as e:
            return "", e, meta

    def _execute(self, sql: str) -> Tuple[Any, Optional[str]]:
        try:
            sql_clean = _extract_sql(sql)
            result = self.conn.execute(sql_clean).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            rows = [dict(zip(columns, row)) for row in result]
            return rows, None
        except Exception as e:
            return None, str(e)


# ─────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────

def _extract_sql(text: str) -> str:
    """Extract clean SQL from LLM response."""
    if not text:
        return ""
    # Remove markdown code blocks
    text = re.sub(r'^```(?:sql)?\s*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text.strip(), flags=re.MULTILINE)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove trailing semicolons (DuckDB handles both)
    if text.endswith(';'):
        text = text[:-1].strip()
    return text


def _extract_json_safe(text: str) -> Optional[dict]:
    """Safely extract JSON from LLM response."""
    if not text:
        return None
    try:
        # Direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from code blocks
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding raw JSON
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _classify_error_quick(error_msg: str) -> str:
    """Quick error classification from error message."""
    error_lower = error_msg.lower()
    if any(kw in error_lower for kw in ['column', 'does not exist', 'not found', 'binder error']):
        return 'E1'
    if any(kw in error_lower for kw in ['join', 'foreign key', 'ambiguous']):
        return 'E3'
    return 'E4'
