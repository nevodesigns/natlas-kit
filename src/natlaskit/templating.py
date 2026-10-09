"""N-ATLaS prompt templating.

N-ATLaS uses the Llama-3 chat format with a *dated* system header. Getting this
right by hand is error-prone (the official model card even forgets to import
`datetime`), so natlas-kit builds the prompt for you and injects today's date.

For chat-style endpoints (vLLM / TGI messages API) the server applies the chat
template itself; we only make sure a correct N-ATLaS system message is present.
For raw text-generation endpoints we build the full prompt string here.
"""
from datetime import date
from typing import List, Optional

from .types import Message

BOT = "<|begin_of_text|>"
SH = "<|start_header_id|>"
EH = "<|end_header_id|>"
EOT = "<|eot_id|>"

DEFAULT_SYSTEM = (
    "You are N-ATLaS, a helpful multilingual assistant trained by Awarri "
    "technologies for the National Centre for Artificial Intelligence and "
    "Robotics (NCAIR). You understand English, Hausa, Igbo, Yoruba and "
    "Nigerian Pidgin."
)


def system_text(system: Optional[str] = None, today: Optional[str] = None) -> str:
    """The N-ATLaS system message, with today's date appended (its dated header)."""
    base = DEFAULT_SYSTEM if system is None else system
    d = today or date.today().isoformat()
    return f"{base}\nToday's date: {d}."


def ensure_system(messages: List[Message], system: Optional[str] = None,
                  today: Optional[str] = None) -> List[Message]:
    """Return messages with a correct N-ATLaS system message at the front.
    If the caller already supplied a system message we leave it untouched."""
    if messages and messages[0].role == "system":
        return list(messages)
    return [Message("system", system_text(system, today))] + list(messages)


def build_prompt(messages: List[Message], add_generation_prompt: bool = True) -> str:
    """Build the raw Llama-3 / N-ATLaS prompt string for text-generation endpoints."""
    parts = [BOT]
    for m in messages:
        parts.append(f"{SH}{m.role}{EH}\n\n{m.content}{EOT}")
    if add_generation_prompt:
        parts.append(f"{SH}assistant{EH}\n\n")
    return "".join(parts)
