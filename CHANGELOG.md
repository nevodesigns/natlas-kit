# Changelog

## 0.1.1 — 2026-10-10 (fixes from external beta testing)
Found and fixed during beta testing by 3 external developers. Full detail and attribution
in [BETA_TESTING.md](BETA_TESTING.md).
- `extract()`: the JSON scanner no longer miscounts braces found inside quoted string values.
- `extract()`: malformed-JSON quote repair no longer corrupts apostrophes inside valid strings.
- `extract()`: a numeric field correctly rejects booleans in Python (matching TypeScript).
- `extract()`: integer coercion now truncates toward zero consistently, in both languages,
  whether the value arrives as a string or an already-numeric type.
- `extract()` (Python): a still-malformed reply after repair is now caught and retried
  instead of crashing the call.
- `classify()`: an exact label match is now preferred over a shorter label that merely
  appears as a substring of a longer one.
- CLI: `extract` reports a clean error (not a traceback) for a missing or invalid schema
  file; `ask`/`extract` reject empty input instead of silently sending it to the model.
- Docs/website: install instructions now show the method that works today
  (`pip install git+https://github.com/nevodesigns/natlas-kit.git`), since the package is
  not yet published to PyPI/npm.
- Added 6 Python and 7 TypeScript regression tests covering the above.

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
