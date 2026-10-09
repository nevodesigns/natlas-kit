"""Small shared data types."""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """One turn in a chat. role is 'system' | 'user' | 'assistant'."""
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class GenerationConfig:
    """Decoding settings. Defaults mirror the N-ATLaS model card
    (temperature 0.1, repetition_penalty 1.12)."""
    max_new_tokens: int = 512
    temperature: float = 0.1
    top_p: float = 0.9
    repetition_penalty: float = 1.12
    stop: List[str] = field(default_factory=lambda: ["<|eot_id|>"])

    def merge(self, **overrides: Any) -> "GenerationConfig":
        data = asdict(self)
        data.update({k: v for k, v in overrides.items() if v is not None})
        return GenerationConfig(**data)


@dataclass
class ChatResult:
    """A completion plus a little metadata, so callers can log latency/usage."""
    text: str
    raw: Any = None
    latency_ms: Optional[float] = None
    backend: Optional[str] = None
