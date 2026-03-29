"""
Chaos 2 Clarity — Unified LLM Client
Wraps Ollama (local) with OpenAI-compatible interface.
All systems use the same LLM for fair comparison.
"""

import json
import requests
import re
import time
from dataclasses import dataclass
from typing import Optional


OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:3b"


@dataclass
class LLMResponse:
    """Unified LLM response wrapper."""
    text: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0


class OllamaClient:
    """
    Ollama LLM client with OpenAI-like interface.
    Used for BOTH C2C pipeline AND baselines (fair comparison).
    """

    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = OLLAMA_BASE_URL,
                 temperature: float = 0.0, max_tokens: int = 512):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.total_calls = 0
        self.total_tokens = 0

    def generate_content(self, prompt, **kwargs) -> LLMResponse:
        """
        Generate content — compatible with google.generativeai interface.
        Accepts either a string or a list of message dicts.
        """
        # Normalize prompt input
        if isinstance(prompt, list):
            # Extract text from message list format
            text_parts = []
            for msg in prompt:
                if isinstance(msg, dict):
                    parts = msg.get('parts', [])
                    for p in parts:
                        if isinstance(p, str):
                            text_parts.append(p)
                elif isinstance(msg, str):
                    text_parts.append(msg)
            prompt_text = '\n'.join(text_parts)
        else:
            prompt_text = str(prompt)

        t0 = time.perf_counter()
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt_text,
                    "stream": False,
                    "keep_alive": "30m",
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response", "")
            tokens = data.get("eval_count", 0)
        except Exception as e:
            text = f"Error: {e}"
            tokens = 0

        latency = (time.perf_counter() - t0) * 1000
        self.total_calls += 1
        self.total_tokens += tokens

        return LLMResponse(text=text, model=self.model, tokens_used=tokens, latency_ms=latency)

    def chat(self, system: str, user: str, **kwargs) -> LLMResponse:
        """Chat-style interface for baselines."""
        t0 = time.perf_counter()
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "keep_alive": "30m",
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "")
            tokens = data.get("eval_count", 0)
        except Exception as e:
            text = f"Error: {e}"
            tokens = 0

        latency = (time.perf_counter() - t0) * 1000
        self.total_calls += 1
        self.total_tokens += tokens

        return LLMResponse(text=text, model=self.model, tokens_used=tokens, latency_ms=latency)

    def get_stats(self) -> dict:
        return {
            'model': self.model,
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
        }


def test_ollama_connection(model: str = DEFAULT_MODEL) -> bool:
    """Quick health check."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models = [m['name'] for m in r.json().get('models', [])]
        if any(model in m for m in models):
            print(f"✅ Ollama connected: {model} available")
            return True
        else:
            print(f"⚠️ Ollama running but model '{model}' not found. Available: {models}")
            return False
    except Exception as e:
        print(f"❌ Ollama not running: {e}")
        return False
