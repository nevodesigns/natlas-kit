# N-ATLaS integration evidence

This is a real run of natlas-kit against the **actual N-ATLaS model** (NAIC 2026,
Problem Statement 1 requirement: "N-ATLaS integration evidence").

- **Date:** 2026-10-09
- **Model:** N-ATLaS (NCAIR1/N-ATLaS, Llama-3 8B), run from the community GGUF
  `QuantFactory/N-ATLaS-GGUF` (Q4_K_M), served with **ollama** on a Google Colab
  **T4 GPU**, exposing an OpenAI-compatible API on `localhost:11434`.
- **Client:** natlas-kit `openai` backend (`NATLAS_BACKEND=openai`,
  `NATLAS_ENDPOINT=http://localhost:11434`, `NATLAS_MODEL=natlas`).
- **Commands:** `natlas ping`, `natlas ask ...`, `natlas eval evals/suite_core.json`,
  `python examples/egotrack_voice_to_ledger.py`.

## Raw output

```
ok
Ẹ kaaro
# N-ATLaS eval report
- Pass rate: **5/7** (71%)
- Avg latency: 384.0 ms

| Case | Result | Latency | Detail |
| --- | --- | --- | --- |
| translate_en_to_yoruba | PASS | 140 ms | ok |
| translate_en_to_hausa | PASS | 111 ms | ok |
| detect_language_hausa | FAIL | 138 ms | missing ['Hausa'] |
| detect_language_igbo | PASS | 130 ms | ok |
| classify_expense | PASS | 117 ms | ok |
| extract_sale_pidgin | PASS | 1361 ms | ok |
| extract_expense | FAIL | 690 ms | field 'amount': got 6000.0, want 6000 |

Heard: I sell one alternator for sixty-eight thousand give Emeka Motors, dem pay fifty, remaining go be credit.

Ledger entry:
{
  "kind": "income",
  "item": "alternator",
  "quantity": 1,
  "amount": 68000.0,
  "amount_paid": 50000.0,
  "counterparty": "Emeka Motors",
  "on_credit": true
}

-> Also opens a debt of N18,000 for Emeka Motors.
```

## What this proves

- natlas-kit connects to a real N-ATLaS deployment and gets correct Nigerian-language
  output: "good morning" to Yoruba returns **"Ẹ kaaro"**; Hausa translation, Igbo language
  detection and expense classification all pass.
- The **structured-extraction** feature works on the real model: a sale spoken in Nigerian
  Pidgin is turned into a validated JSON ledger entry (the EgoTrack voice-to-ledger use
  case), including deriving the ₦18,000 outstanding debt.
- Average latency ~384 ms per call on a T4 GPU.

## Honest notes on the two non-passes (real validation, not cherry-picked)

- `detect_language_hausa` (FAIL): N-ATLaS answered without the literal token "Hausa"
  (it phrased the language differently), so the substring check missed. A genuine model
  behaviour worth knowing, kept here rather than hidden.
- `extract_expense` (FAIL): the model actually returned the **correct** value `6000`, but
  as a float (`6000.0`), and an early version of the eval compared values as text
  (`"6000.0" != "6000"`). The eval now compares numbers numerically, so this case passes;
  this raw log is kept to show the real run.
