"""Ready-made task helpers for Nigerian-language work with N-ATLaS."""
from typing import List, Optional

from .types import Message

LANGS = {"en": "English", "ha": "Hausa", "ig": "Igbo", "yo": "Yoruba", "pcm": "Nigerian Pidgin"}


def _name(code_or_name: str) -> str:
    return LANGS.get(code_or_name.lower(), code_or_name)


def translate(client, text: str, to_lang: str, from_lang: Optional[str] = None, **params) -> str:
    src = f"from {_name(from_lang)} " if from_lang else ""
    sys = "You are a professional translator for Nigerian languages. Reply with only the translation."
    prompt = f"Translate the following {src}into {_name(to_lang)}:\n\n{text}"
    return client.chat([Message("system", sys), Message("user", prompt)], **params).text.strip()


def detect_language(client, text: str, **params) -> str:
    sys = ("Identify the language. Reply with exactly one of: "
           "English, Hausa, Igbo, Yoruba, Nigerian Pidgin.")
    return client.chat([Message("system", sys), Message("user", text)],
                       max_new_tokens=8, **params).text.strip()


def classify(client, text: str, labels: List[str], **params) -> str:
    """Classify `text` into one of `labels`. Returns the raw model text unchanged
    if nothing matches (callers that need a hard guarantee should check the
    result is `in labels` themselves)."""
    sys = ("You are a classifier. Reply with exactly one label from the list and nothing else.\n"
           "Labels: " + ", ".join(labels))
    out = client.chat([Message("system", sys), Message("user", text)],
                      max_new_tokens=16, **params).text.strip()
    low = out.lower()
    for lab in labels:                       # 1) exact match first
        if lab.strip().lower() == low:
            return lab
    # 2) longest labels first, so a short label (e.g. "in") can't win just
    #    because it happens to be a substring of a longer one (e.g. "income").
    for lab in sorted(labels, key=len, reverse=True):
        if lab.lower() in low:
            return lab
    return out


def summarize(client, text: str, sentences: int = 3, lang: str = "English", **params) -> str:
    sys = f"Summarize clearly in {_name(lang)}, in at most {sentences} sentences."
    return client.chat([Message("system", sys), Message("user", text)], **params).text.strip()
