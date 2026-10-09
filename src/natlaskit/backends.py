"""Backends: where the N-ATLaS weights actually run.

N-ATLaS has no hosted inference provider, so teams self-host it. The two common
ways are Hugging Face Text-Generation-Inference (TGI) and an OpenAI-compatible
server (vLLM). natlas-kit speaks both, plus a MockBackend so you can develop and
run the test suite with no GPU and no network.
"""
import json
import time
from typing import Any, Callable, Dict, List, Optional, Union

import requests

from .errors import BackendError
from .templating import build_prompt, ensure_system
from .types import ChatResult, GenerationConfig, Message


class Backend:
    name = "base"

    def generate(self, messages: List[Message], cfg: GenerationConfig) -> ChatResult:
        raise NotImplementedError


class TGIBackend(Backend):
    """Hugging Face Text-Generation-Inference (e.g. an Inference Endpoint).
    Talks to POST {endpoint}/generate with the raw N-ATLaS prompt."""
    name = "tgi"

    def __init__(self, endpoint: str, token: Optional[str] = None, timeout: int = 120):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def generate(self, messages: List[Message], cfg: GenerationConfig) -> ChatResult:
        prompt = build_prompt(ensure_system(messages))
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": cfg.max_new_tokens,
                "temperature": max(cfg.temperature, 1e-3),
                "top_p": cfg.top_p,
                "repetition_penalty": cfg.repetition_penalty,
                "stop": cfg.stop,
                "return_full_text": False,
            },
        }
        t0 = time.time()
        try:
            r = requests.post(f"{self.endpoint}/generate", headers=self._headers(),
                              data=json.dumps(payload), timeout=self.timeout)
        except requests.RequestException as e:
            raise BackendError(f"TGI request failed: {e}") from e
        if r.status_code >= 400:
            raise BackendError(f"TGI {r.status_code}: {r.text[:300]}")
        data = r.json()
        text = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", "")
        return ChatResult(text=_clean(text), raw=data,
                          latency_ms=(time.time() - t0) * 1000, backend=self.name)


class OpenAIBackend(Backend):
    """OpenAI-compatible chat server (vLLM `--served-model-name`, etc.).
    Talks to POST {endpoint}/v1/chat/completions."""
    name = "openai"

    def __init__(self, endpoint: str, token: Optional[str] = None,
                 model: str = "N-ATLaS", timeout: int = 120):
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.model = model
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "true"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def generate(self, messages: List[Message], cfg: GenerationConfig) -> ChatResult:
        msgs = [m.to_dict() for m in ensure_system(messages)]
        payload = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": cfg.max_new_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stop": [s for s in cfg.stop if not s.startswith("<|")] or None,
        }
        t0 = time.time()
        try:
            r = requests.post(f"{self.endpoint}/v1/chat/completions", headers=self._headers(),
                              data=json.dumps(payload), timeout=self.timeout)
        except requests.RequestException as e:
            raise BackendError(f"OpenAI-compatible request failed: {e}") from e
        if r.status_code >= 400:
            raise BackendError(f"Endpoint {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise BackendError(f"Unexpected response shape: {json.dumps(data)[:300]}") from e
        return ChatResult(text=_clean(text), raw=data,
                          latency_ms=(time.time() - t0) * 1000, backend=self.name)


class MockBackend(Backend):
    """Deterministic, offline backend for development, examples and CI.

    `responses` may be a string, a list (cycled), or a callable(messages)->str.
    """
    name = "mock"

    def __init__(self, responses: Union[str, List[str], Callable[[List[Message]], str], None] = None):
        self.responses = responses
        self._i = 0

    def generate(self, messages: List[Message], cfg: GenerationConfig) -> ChatResult:
        if callable(self.responses):
            text = self.responses(messages)
        elif isinstance(self.responses, list) and self.responses:
            text = self.responses[self._i % len(self.responses)]
            self._i += 1
        elif isinstance(self.responses, str):
            text = self.responses
        else:
            last = next((m.content for m in reversed(messages) if m.role == "user"), "")
            text = f"[mock N-ATLaS reply to: {last[:80]}]"
        return ChatResult(text=text, raw={"mock": True}, latency_ms=0.0, backend=self.name)


def _clean(text: str) -> str:
    for tok in ("<|eot_id|>", "<|end_of_text|>"):
        text = text.replace(tok, "")
    return text.strip()


def make_backend(kind: str, endpoint: Optional[str] = None, token: Optional[str] = None,
                 model: str = "N-ATLaS", **kw: Any) -> Backend:
    kind = (kind or "mock").lower()
    if kind == "mock":
        return MockBackend(kw.get("responses"))
    if not endpoint:
        raise BackendError(f"backend '{kind}' needs an endpoint URL")
    if kind == "tgi":
        return TGIBackend(endpoint, token=token, timeout=kw.get("timeout", 120))
    if kind in ("openai", "vllm"):
        return OpenAIBackend(endpoint, token=token, model=model, timeout=kw.get("timeout", 120))
    raise BackendError(f"unknown backend '{kind}' (use tgi | openai | mock)")
