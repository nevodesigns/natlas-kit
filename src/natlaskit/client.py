"""NatlasClient: one friendly entry point to N-ATLaS."""
import os
from typing import Any, Dict, List, Optional, Union

from .backends import Backend, make_backend
from .types import ChatResult, GenerationConfig, Message

MessageLike = Union[Message, Dict[str, str]]


def _coerce(messages: List[MessageLike]) -> List[Message]:
    out = []
    for m in messages:
        out.append(m if isinstance(m, Message) else Message(m["role"], m["content"]))
    return out


class NatlasClient:
    """Wraps a backend and sensible N-ATLaS defaults.

    >>> nat = NatlasClient.from_env()              # reads NATLAS_* env vars
    >>> nat = NatlasClient(backend="tgi", endpoint="https://...", token="hf_...")
    >>> nat.ask("Translate 'good morning' to Yoruba")
    """

    def __init__(self, backend: Union[str, Backend] = "mock",
                 endpoint: Optional[str] = None, token: Optional[str] = None,
                 model: str = "N-ATLaS", config: Optional[GenerationConfig] = None,
                 **backend_kw: Any):
        self.backend = backend if isinstance(backend, Backend) else make_backend(
            backend, endpoint=endpoint, token=token, model=model, **backend_kw)
        self.config = config or GenerationConfig()

    @classmethod
    def from_env(cls, **overrides: Any) -> "NatlasClient":
        """Build from NATLAS_BACKEND, NATLAS_ENDPOINT, NATLAS_TOKEN, NATLAS_MODEL.
        Explicit None overrides (e.g. unset CLI flags) fall back to the env var."""
        overrides = {k: v for k, v in overrides.items() if v is not None}
        return cls(
            backend=overrides.pop("backend", os.getenv("NATLAS_BACKEND", "mock")),
            endpoint=overrides.pop("endpoint", os.getenv("NATLAS_ENDPOINT")),
            token=overrides.pop("token", os.getenv("NATLAS_TOKEN")),
            model=overrides.pop("model", os.getenv("NATLAS_MODEL", "N-ATLaS")),
            **overrides,
        )

    def chat(self, messages: List[MessageLike], **params: Any) -> ChatResult:
        cfg = self.config.merge(**params)
        return self.backend.generate(_coerce(messages), cfg)

    def ask(self, prompt: str, system: Optional[str] = None, **params: Any) -> str:
        """Single-turn convenience: returns just the text."""
        msgs: List[MessageLike] = []
        if system:
            msgs.append(Message("system", system))
        msgs.append(Message("user", prompt))
        return self.chat(msgs, **params).text

    def ping(self) -> bool:
        """Cheap round-trip to confirm the endpoint answers."""
        try:
            self.chat([Message("user", "Reply with: OK")], max_new_tokens=8)
            return True
        except Exception:
            return False
