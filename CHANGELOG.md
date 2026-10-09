# Changelog

## 0.1.0 — 2026-10 (NAIC 2026 submission)
- First release.
- `NatlasClient` with TGI, OpenAI-compatible (vLLM) and mock backends.
- Automatic N-ATLaS Llama-3 chat templating with dated system header and model-card defaults.
- `extract()` structured JSON extraction with parsing, repair, schema validation and retry.
- Task helpers: `translate`, `detect_language`, `classify`, `summarize`.
- `ASRClient` for the N-ATLaS speech-to-text models.
- Eval harness (`natlas eval`) with latency and pass-rate reporting.
- CLI: `ping`, `ask`, `extract`, `transcribe`, `eval`, `version`.
- 8 offline tests (mock backend); CI on Python 3.9/3.11/3.12.
