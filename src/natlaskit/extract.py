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
    """Pull the first balanced {...} object out of a reply, tolerating prose and fences.

    Quote-aware: braces inside a quoted string (single or double) do not count toward
    the balance, so values like {"note": "closing brace } inside text"} are found whole.
    """
    text = text.replace("```json", "```").strip()
    if "```" in text:
        text = text.split("```")[1] if len(text.split("```")) > 1 else text
    start = text.find("{")
    if start == -1:
        raise SchemaError("no JSON object found in model reply")
    depth = 0
    in_str = False
    quote = ""
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < n:      # skip escaped char, incl. escaped quote
                i += 2
                continue
            if c == quote:
                in_str = False
            i += 1
            continue
        if c in ("'", '"'):
            in_str = True
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise SchemaError("unbalanced JSON object in model reply")


def _repair_quotes(blob: str) -> str:
    """Convert Python-dict-style single quotes to JSON double quotes without
    corrupting apostrophes that occur inside already-double-quoted strings
    (e.g. {'name': "O'Connor"} -> {"name": "O'Connor"})."""
    out = []
    in_double = False
    in_single = False
    i = 0
    n = len(blob)
    while i < n:
        c = blob[i]
        if in_double:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(blob[i + 1])
                i += 2
                continue
            if c == '"':
                in_double = False
            i += 1
            continue
        if in_single:
            if c == "\\" and i + 1 < n:
                nxt = blob[i + 1]
                out.append("'" if nxt == "'" else "\\" + nxt)
                i += 2
                continue
            if c == "'":
                out.append('"')          # close the single-quoted run as a JSON string
                in_single = False
                i += 1
                continue
            if c == '"':
                out.append('\\"')        # an unescaped " inside a single-quoted run
                i += 1
                continue
            out.append(c)
            i += 1
            continue
        if c == '"':
            out.append('"')
            in_double = True
        elif c == "'":
            out.append('"')
            in_single = True
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _loads(blob: str) -> Dict[str, Any]:
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        repaired = _repair_quotes(blob)
        repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)    # trailing commas
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            # Funnel every parse failure through SchemaError so callers (extract's
            # retry loop) only ever have to catch one exception type.
            raise SchemaError(f"invalid JSON in model reply: {e}") from e


def _validate(obj: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> List[str]:
    errs = []
    for name, spec in schema.items():
        if name not in obj or obj[name] is None:
            if spec.get("required"):
                errs.append(f"missing required field '{name}'")
            elif "default" in spec:
                obj[name] = spec["default"]
            continue
        t = spec.get("type", "string")
        v = obj[name]

        if t in ("number", "integer"):
            # bool is a subclass of int in Python, so exclude it explicitly: a
            # numeric field must never silently accept true/false.
            if isinstance(v, bool):
                errs.append(f"field '{name}' should be {t}, got boolean")
                continue
            if isinstance(v, (int, float)):
                # truncate toward zero for 'integer', matching str-coercion below
                obj[name] = int(v) if t == "integer" else v
                continue
            if isinstance(v, str):
                try:                              # coerce "30,000" -> 30000
                    num = float(v.replace(",", "").strip())
                except ValueError:
                    errs.append(f"field '{name}' should be {t}, got a non-numeric string")
                    continue
                obj[name] = int(num) if t == "integer" else num
                continue
            errs.append(f"field '{name}' should be {t}, got {type(v).__name__}")
            continue

        want = _TYPES.get(t)
        if want and not isinstance(v, want):
            errs.append(f"field '{name}' should be {t}, got {type(v).__name__}")
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
