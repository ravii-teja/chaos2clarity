"""
Chaos 2 Clarity — Baseline Systems (Ollama-compatible)
B1: Direct LLM-to-SQL (raw schema, no orchestration)
B2: Schema-aware LLM (schema + column descriptions)
B3: Full pipeline on raw schemas (no semantic layer)

All use the same underlying LLM for fair comparison.
"""

import json
import re
import time
from typing import Tuple, Any, Optional

from src.prompts import (
    B1_DIRECT_SYSTEM_PROMPT, B1_DIRECT_USER_TEMPLATE,
    B2_SCHEMA_AWARE_SYSTEM_PROMPT, B2_SCHEMA_AWARE_USER_TEMPLATE,
    SQL_GENERATOR_SYSTEM_PROMPT,
)


class B1DirectLLM:
    """
    𝔅₁: Direct LLM-to-SQL
    Single LLM call with raw schema. No semantic layer, no orchestration.
    """

    def __init__(self, llm_client, conn, schema_ddl: str):
        self.llm = llm_client
        self.conn = conn
        self.schema_ddl = schema_ddl

    def __call__(self, nl_prompt: str) -> Tuple[str, Any, dict]:
        meta = {'retry_count': 0, 'grounding_used': False, 'grounding_sim': 0.0,
                'first_pass': False, 'cross_source_planned': False}

        user_msg = B1_DIRECT_USER_TEMPLATE.format(
            raw_schema_ddl=self.schema_ddl, nl_prompt=nl_prompt)

        try:
            response = self.llm.chat(system=B1_DIRECT_SYSTEM_PROMPT, user=user_msg)
            sql = _extract_sql(response.text)
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
            if not sql_clean:
                return None, "Empty SQL"
            result = self.conn.execute(sql_clean).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            return [dict(zip(columns, row)) for row in result], None
        except Exception as e:
            return None, str(e)


class B2SchemaAwareLLM:
    """
    𝔅₂: Schema-aware LLM
    LLM with schema DDL + column descriptions injected.
    """

    def __init__(self, llm_client, conn, schema_ddl: str, column_descriptions: str):
        self.llm = llm_client
        self.conn = conn
        self.schema_ddl = schema_ddl
        self.column_descriptions = column_descriptions

    def __call__(self, nl_prompt: str) -> Tuple[str, Any, dict]:
        meta = {'retry_count': 0, 'grounding_used': False, 'grounding_sim': 0.0,
                'first_pass': False, 'cross_source_planned': False}

        user_msg = B2_SCHEMA_AWARE_USER_TEMPLATE.format(
            raw_schema_ddl=self.schema_ddl,
            column_descriptions=self.column_descriptions,
            nl_prompt=nl_prompt)

        try:
            response = self.llm.chat(system=B2_SCHEMA_AWARE_SYSTEM_PROMPT, user=user_msg)
            sql = _extract_sql(response.text)
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
            if not sql_clean:
                return None, "Empty SQL"
            result = self.conn.execute(sql_clean).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            return [dict(zip(columns, row)) for row in result], None
        except Exception as e:
            return None, str(e)


class B3PipelineNoSem:
    """
    𝔅₃: Full pipeline on raw schemas (no Semantic Model S).
    """

    def __init__(self, llm_client, conn, schema_ddl: str, max_retries: int = 2):
        self.llm = llm_client
        self.conn = conn
        self.schema_ddl = schema_ddl
        self.max_retries = max_retries

    def __call__(self, nl_prompt: str) -> Tuple[str, Any, dict]:
        meta = {'retry_count': 0, 'grounding_used': False, 'grounding_sim': 0.0,
                'first_pass': False, 'cross_source_planned': False}

        error_ctx = ""
        sql = ""
        for attempt in range(self.max_retries + 1):
            prompt = f"""{SQL_GENERATOR_SYSTEM_PROMPT}

Database schema: {self.schema_ddl}
Error context: {error_ctx if error_ctx else 'None (first attempt)'}
Question: {nl_prompt}

Return ONLY valid SQL. No explanation."""

            try:
                response = self.llm.generate_content(prompt)
                sql = _extract_sql(response.text)
                result, error = self._execute(sql)
                if error is None:
                    if attempt == 0:
                        meta['first_pass'] = True
                    meta['retry_count'] = attempt
                    return sql, result, meta
                else:
                    error_ctx = error
                    meta['retry_count'] = attempt + 1
            except Exception as e:
                error_ctx = str(e)
                meta['retry_count'] = attempt + 1

        return sql, Exception(f"Max retries exceeded: {error_ctx}"), meta

    def _execute(self, sql: str) -> Tuple[Any, Optional[str]]:
        try:
            sql_clean = _extract_sql(sql)
            if not sql_clean:
                return None, "Empty SQL"
            result = self.conn.execute(sql_clean).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            return [dict(zip(columns, row)) for row in result], None
        except Exception as e:
            return None, str(e)


def _extract_sql(text: str) -> str:
    """Extract clean SQL from LLM response."""
    if not text:
        return ""
    # Remove markdown code blocks
    text = re.sub(r'^```(?:sql)?\s*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text.strip(), flags=re.MULTILINE)
    text = text.strip()
    # Try to find SELECT statement if there's other text
    match = re.search(r'(SELECT\s+.+?)(?:;|\Z)', text, re.IGNORECASE | re.DOTALL)
    if match:
        text = match.group(1).strip()
    # Remove trailing semicolons
    if text.endswith(';'):
        text = text[:-1].strip()
    return text
