"""Speech-to-text with the N-ATLaS ASR models.

The N-ATLaS suite ships four ASR models (one per language family) alongside the
LLM, but they are separate repos with no hosted API. ASRClient posts audio bytes
to a Hugging Face Inference Endpoint running one of them (standard HF audio
pipeline: raw bytes in, {"text": ...} out), so a voice app can go straight from
microphone to N-ATLaS text.

Point it at whichever ASR endpoint you deploy; set NATLAS_ASR_ENDPOINT / _TOKEN,
or pass them in. This keeps voice-first apps (the people who do not type) one call
away from the rest of the toolkit.
"""
import os
from typing import Optional

import requests

from .errors import BackendError


class ASRClient:
    def __init__(self, endpoint: Optional[str] = None, token: Optional[str] = None,
                 timeout: int = 120):
        self.endpoint = (endpoint or os.getenv("NATLAS_ASR_ENDPOINT") or "").rstrip("/")
        self.token = token or os.getenv("NATLAS_ASR_TOKEN")
        self.timeout = timeout

    def _headers(self, content_type: str):
        h = {"Content-Type": content_type}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def transcribe(self, audio: bytes, content_type: str = "audio/wav") -> str:
        """Transcribe raw audio bytes to text."""
        if not self.endpoint:
            raise BackendError("no ASR endpoint set (NATLAS_ASR_ENDPOINT or endpoint=)")
        try:
            r = requests.post(self.endpoint, headers=self._headers(content_type),
                              data=audio, timeout=self.timeout)
        except requests.RequestException as e:
            raise BackendError(f"ASR request failed: {e}") from e
        if r.status_code >= 400:
            raise BackendError(f"ASR {r.status_code}: {r.text[:300]}")
        data = r.json()
        if isinstance(data, dict) and "text" in data:
            return data["text"].strip()
        if isinstance(data, list) and data and "text" in data[0]:
            return data[0]["text"].strip()
        raise BackendError(f"unexpected ASR response: {str(data)[:200]}")

    def transcribe_file(self, path: str) -> str:
        ct = "audio/wav" if path.lower().endswith(".wav") else "application/octet-stream"
        with open(path, "rb") as f:
            return self.transcribe(f.read(), content_type=ct)
