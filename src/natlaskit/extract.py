"""Structured extraction: turn free N-ATLaS text into validated JSON.

N-ATLaS is a chat model, not a JSON engine, so getting reliable structured output
(for fintech, forms, data pipelines) is the #1 integration pain. `extract` builds a
strict JSON instruction from a tiny schema, parses and repairs the reply, validates
it, and retries once with the validation error fed back to the model.

Schema format (stdlib only, no pydantic required):
    {
      "item":   {"type": "string",  "required": True,  "description": "what was sold"},
      "amount": {"type": "number",  "required": True},
      "credit": {"type": "boolean", "required": False, "default": False},
      "tags":   {"type": "array"},
    }
"""
import json
import re
from typing import Any, Dict, List, Optional

from .errors import SchemaError
from .types import Message

_TYPES = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _schema_lines(schema: Dict[str, Dict[str, Any]]) -> str:
    lines = []
    for name, spec in schema.items():
        t = spec.get("type", "string")
        req = "required" if spec.get("required") else "optional"
        desc = spec.get("description", "")
        lines.append(f'  "{name}": <{t}>  ({req}){(" - " + desc) if desc else ""}')
    return "\n".join(lines)


def _find_json(text: str) -> str:
    """Pull the first balanced {...} object out of a reply, tolerating prose and fences."""
    text = text.replace("```json", "```").strip()
    if "```" in text:
        text = text.split("```")[1] if len(text.split("```")) > 1 else text
    start = text.find("{")
    if start == -1:
        raise SchemaError("no JSON object found in model reply")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise SchemaError("unbalanced JSON object in model reply")


def _loads(blob: str) -> Dict[str, Any]:
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        repaired = re.sub(r",(\s*[}\]])", r"\1", blob)        # trailing commas
        repaired = repaired.replace("'", '"')                 # single quotes
        return json.loads(repaired)


def _validate(obj: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> List[str]:
    errs = []
    for name, spec in schema.items():
        if name not in obj or obj[name] is None:
            if spec.get("required"):
                errs.append(f"missing required field '{name}'")
            elif "default" in spec:
                obj[name] = spec["default"]
            continue
        want = _TYPES.get(spec.get("type", "string"))
        if want and not isinstance(obj[name], want):
            if spec.get("type") in ("number", "integer") and isinstance(obj[name], str):
                try:                              # coerce "30,000" -> 30000
                    num = float(obj[name].replace(",", "").strip())
                    obj[name] = int(num) if spec.get("type") == "integer" else num
                    continue
                except ValueError:
                    pass
            errs.append(f"field '{name}' should be {spec.get('type')}, got {type(obj[name]).__name__}")
    return errs


def extract(client, text: str, schema: Dict[str, Dict[str, Any]],
            instructions: Optional[str] = None, retries: int = 1,
            **params: Any) -> Dict[str, Any]:
    """Extract structured data from `text` according to `schema`. Returns a dict."""
    sys = (
        "You are a precise information extraction engine. "
        "Reply with ONE JSON object and nothing else, no prose, no code fences."
    )
    prompt = (
        (instructions + "\n\n" if instructions else "")
        + "Extract the fields below from the text. Use null when a value is absent.\n\n"
        + "Fields:\n" + _schema_lines(schema) + "\n\n"
        + "Text:\n" + text.strip() + "\n\nJSON:"
    )
    messages = [Message("system", sys), Message("user", prompt)]
    last_err = None
    for attempt in range(retries + 1):
        reply = client.chat(messages, **params).text
        try:
            obj = _loads(_find_json(reply))
            errs = _validate(obj, schema)
            if not errs:
                return {k: obj.get(k, schema[k].get("default")) for k in schema}
            last_err = "; ".join(errs)
        except SchemaError as e:
            last_err = str(e)
        messages.append(Message("assistant", reply))
        messages.append(Message("user", f"That was invalid ({last_err}). Return corrected JSON only."))
    raise SchemaError(f"could not extract valid data after {retries + 1} tries: {last_err}")
