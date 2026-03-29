"""
Chaos 2 Clarity — Mechanism III: Vector-Grounded BI Reasoning
Persistent vector store of verified query–plan–result triples.
Backed by ChromaDB for Colab compatibility.
"""

import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple, Any


class VectorStore:
    """
    Vector Knowledge Store V for verified query–plan–result triples.
    V = {(q_norm, π_verified, SQL*_verified, r_gold, κ_entry, emb(q_norm))}

    Architecturally distinct from the result cache:
    - Cache returns RESULTS for identical queries
    - V returns EXECUTION PATTERNS for semantically similar queries
    """

    def __init__(self, collection_name: str = "c2c_verified_plans",
                 max_entries: int = 500, prune_threshold: float = 0.3):
        self.collection_name = collection_name
        self.max_entries = max_entries
        self.prune_threshold = prune_threshold
        self._collection = None
        self._entries = {}  # id -> entry dict (fallback if ChromaDB unavailable)
        self._use_chroma = False
        self._init_store()

    def _init_store(self):
        """Initialize ChromaDB collection or fall back to in-memory dict."""
        try:
            import chromadb
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._use_chroma = True
            print(f"✅ Vector store initialized with ChromaDB (collection: {self.collection_name})")
        except ImportError:
            print("⚠️ ChromaDB not available. Using in-memory fallback.")
            self._use_chroma = False
        except Exception as e:
            print(f"⚠️ ChromaDB init failed: {e}. Using in-memory fallback.")
            self._use_chroma = False

    def add_verified_plan(self, query_normalized: str, plan: dict, sql_verified: str,
                          result_gold: Any, confidence: float = 1.0,
                          embedding_fn=None) -> str:
        """
        Write a verified query–plan–result triple to the store.
        Called on every successful query execution (Algorithm 1, Line 14).
        """
        entry_id = hashlib.md5(query_normalized.encode()).hexdigest()[:12]

        entry = {
            'id': entry_id,
            'query_normalized': query_normalized,
            'plan': plan if isinstance(plan, str) else json.dumps(plan, default=str),
            'sql_verified': sql_verified,
            'result_summary': _summarize_result(result_gold),
            'confidence': confidence,
            'timestamp': time.time(),
        }

        if self._use_chroma and self._collection is not None:
            try:
                # Use ChromaDB's built-in embedding or provided function
                self._collection.upsert(
                    ids=[entry_id],
                    documents=[query_normalized],
                    metadatas=[{
                        'plan': entry['plan'],
                        'sql_verified': sql_verified,
                        'result_summary': entry['result_summary'],
                        'confidence': str(confidence),
                        'timestamp': str(entry['timestamp']),
                    }],
                )
            except Exception as e:
                print(f"⚠️ ChromaDB upsert failed: {e}")
                self._entries[entry_id] = entry
        else:
            self._entries[entry_id] = entry

        # Capacity management
        self._enforce_capacity()

        return entry_id

    def retrieve(self, query: str, k: int = 5) -> List[dict]:
        """
        Retrieve k most semantically similar verified plans.
        Retrieve(q, k): Q → (V)^k
        """
        if self._use_chroma and self._collection is not None:
            try:
                count = self._collection.count()
                if count == 0:
                    return []

                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(k, count),
                )

                plans = []
                if results and results['ids'] and len(results['ids']) > 0:
                    for i, doc_id in enumerate(results['ids'][0]):
                        meta = results['metadatas'][0][i] if results['metadatas'] else {}
                        dist = results['distances'][0][i] if results['distances'] else 1.0
                        similarity = 1 - dist  # ChromaDB returns distances

                        plans.append({
                            'id': doc_id,
                            'query': results['documents'][0][i] if results['documents'] else '',
                            'sql_verified': meta.get('sql_verified', ''),
                            'plan': meta.get('plan', ''),
                            'result_summary': meta.get('result_summary', ''),
                            'confidence': float(meta.get('confidence', 0)),
                            'similarity': similarity,
                        })
                return plans
            except Exception as e:
                print(f"⚠️ ChromaDB query failed: {e}")
                return self._fallback_retrieve(query, k)
        else:
            return self._fallback_retrieve(query, k)

    def _fallback_retrieve(self, query: str, k: int) -> list:
        """Simple keyword-based fallback retrieval."""
        if not self._entries:
            return []

        query_words = set(query.lower().split())
        scored = []
        for entry_id, entry in self._entries.items():
            entry_words = set(entry['query_normalized'].lower().split())
            overlap = len(query_words & entry_words)
            score = overlap / max(len(query_words | entry_words), 1)
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{
            'id': e['id'],
            'query': e['query_normalized'],
            'sql_verified': e['sql_verified'],
            'plan': e['plan'],
            'result_summary': e['result_summary'],
            'confidence': e['confidence'],
            'similarity': s,
        } for s, e in scored[:k] if s > 0.1]

    def update_confidence(self, entry_id: str, confirmed: bool, alpha: float = 0.15):
        """Update κ_entry via Equation 1 when subsequent queries confirm/reject a pattern."""
        if self._use_chroma and self._collection is not None:
            try:
                results = self._collection.get(ids=[entry_id])
                if results['ids']:
                    old_conf = float(results['metadatas'][0].get('confidence', 0.5))
                    new_conf = (1 - alpha) * old_conf + alpha * (1.0 if confirmed else 0.0)
                    meta = results['metadatas'][0]
                    meta['confidence'] = str(new_conf)
                    self._collection.update(
                        ids=[entry_id],
                        metadatas=[meta],
                    )
            except Exception:
                pass
        elif entry_id in self._entries:
            old_conf = self._entries[entry_id]['confidence']
            self._entries[entry_id]['confidence'] = (1 - alpha) * old_conf + alpha * (1.0 if confirmed else 0.0)

    def invalidate_for_schema_change(self, affected_tables: List[str]):
        """Set κ_entry = 0 for entries referencing changed tables."""
        if self._use_chroma and self._collection is not None:
            try:
                all_entries = self._collection.get()
                for i, entry_id in enumerate(all_entries['ids']):
                    sql = all_entries['metadatas'][i].get('sql_verified', '')
                    if any(table in sql.lower() for table in affected_tables):
                        meta = all_entries['metadatas'][i]
                        meta['confidence'] = '0.0'
                        self._collection.update(ids=[entry_id], metadatas=[meta])
            except Exception:
                pass
        else:
            for entry_id, entry in self._entries.items():
                if any(table in entry['sql_verified'].lower() for table in affected_tables):
                    entry['confidence'] = 0.0

    def _enforce_capacity(self):
        """Evict low-confidence entries when capacity is reached."""
        size = self.size()
        if size <= self.max_entries:
            return

        # For now, only prune in-memory store
        if not self._use_chroma:
            prunable = [
                eid for eid, e in self._entries.items()
                if e['confidence'] < self.prune_threshold
            ]
            for eid in prunable[:size - self.max_entries]:
                del self._entries[eid]

    def size(self) -> int:
        """Current number of entries in the store."""
        if self._use_chroma and self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                return len(self._entries)
        return len(self._entries)

    def clear(self):
        """Clear all entries (for experiment reset)."""
        if self._use_chroma and self._collection is not None:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception:
                pass
        self._entries = {}

    def format_grounding_context(self, plans: List[dict]) -> str:
        """Format retrieved plans as grounding context for SQL Generator prompt."""
        if not plans:
            return "No grounding context available (vector store empty or no similar queries found)."

        lines = ["=== GROUNDING CONTEXT: Verified Similar Queries ===\n"]
        for i, plan in enumerate(plans):
            lines.append(f"--- Example {i+1} (similarity: {plan.get('similarity', 0):.2f}) ---")
            lines.append(f"Question: {plan.get('query', 'N/A')}")
            lines.append(f"Verified SQL: {plan.get('sql_verified', 'N/A')}")
            lines.append(f"Result: {plan.get('result_summary', 'N/A')}")
            lines.append("")
        return '\n'.join(lines)


def _summarize_result(result) -> str:
    """Create a brief summary of a query result for storage."""
    if result is None:
        return "null"
    if isinstance(result, (int, float, str)):
        return str(result)
    if isinstance(result, dict):
        return json.dumps(result, default=str)[:200]
    if isinstance(result, list):
        if len(result) == 0:
            return "empty"
        return f"{len(result)} rows: {json.dumps(result[:3], default=str)[:200]}"
    return str(result)[:200]


class ResultCache:
    """
    Simple result cache (distinct from VectorStore).
    Cache returns RESULTS for identical queries.
    V returns PATTERNS for similar queries.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        self._cache = {}  # normalized_query -> (result, timestamp)
        self.similarity_threshold = similarity_threshold
        self.hits = 0
        self.misses = 0

    def get(self, query: str):
        """Check cache for a matching query."""
        key = query.lower().strip()
        if key in self._cache:
            self.hits += 1
            return self._cache[key][0]
        self.misses += 1
        return None

    def put(self, query: str, result):
        """Store a result in the cache."""
        key = query.lower().strip()
        self._cache[key] = (result, time.time())

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / max(total, 1)

    def clear(self):
        self._cache = {}
        self.hits = 0
        self.misses = 0
