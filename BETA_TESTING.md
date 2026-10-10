# Beta testing record

natlas-kit was beta-tested by developers outside the core team ahead of its NAIC 2026
submission. This file records what they found and what was done about it, in full, including
the issues that turned out not to be bugs.

## Testers

1. **Dayo** — CLI-focused testing (empty input, missing/malformed arguments).
2. **Mario** — fresh-install testing (`pip install natlas-kit` from the website).
3. **Ebube** — deep edge-case testing of `extract()`, `classify()` and the retry logic, in
   both the Python and TypeScript implementations, with a written regression report.

## Confirmed issues, fixed

| # | Found by | Issue | Fix |
|---|---|---|---|
| 1 | Ebube | `extract()`'s JSON scanner counted `{`/`}` inside quoted string values, breaking on text like `{"note": "closing brace } inside text"}` | Both `_find_json` (Python) and `findJson` (TypeScript) now track string state and ignore braces inside quotes. |
| 2 | Ebube | Malformed-JSON repair blindly replaced `'` with `"`, corrupting apostrophes inside already-valid strings (e.g. `"O'Connor"` became `"O"Connor"`) | Replaced the repair with a quote-aware scanner (`_repair_quotes` / `repairQuotes`) that only converts single-quote *delimiters*, not apostrophes inside double-quoted text. |
| 3 | Ebube | In Python, a boolean (`true`/`false`) was silently accepted for a `number`/`integer` field, because `bool` is a subclass of `int` | `_validate()` now explicitly rejects booleans for numeric fields (TypeScript's `typeof` check already did this correctly). |
| 4 | Ebube | Fractional values in an `integer` field were handled inconsistently: Python truncated a numeric *string*, TypeScript rounded it, and neither coerced an already-numeric fractional value | Both implementations now truncate toward zero (`int()` / `Math.trunc`) in every case: string input, numeric input, Python and TypeScript alike. |
| 5 | Ebube | In Python, a reply that was malformed even after repair (e.g. an unquoted value) raised a raw `json.JSONDecodeError` that escaped `extract()`'s retry loop instead of being caught and retried (TypeScript already handled this correctly) | `_loads()` now wraps every JSON parse failure in `SchemaError`, so `extract()`'s existing retry handling covers it. |
| 6 | Ebube | `classify()` could return the wrong label when one label is a substring of another, e.g. with `["in", "income"]` and a reply of `"income"`, it returned `"in"` | `classify()` now checks for an exact match first, then falls back to substring matching on the longest labels first. |
| 7 | Dayo | `natlas extract` with a missing or malformed schema file raised a raw Python traceback | The CLI now catches `FileNotFoundError` / `json.JSONDecodeError` on the schema file and prints a one-line error with a non-zero exit code. |
| 8 | Dayo | `natlas ask ""` / `natlas extract "" ...` silently accepted an empty prompt/text | The CLI now rejects empty input with a clear error instead of sending it to the model. |
| 9 | Mario | `pip install natlas-kit` (as shown on the website and in the Python README) fails, because the package is not yet published to PyPI | README, `js/README.md` and the website now show the install method that works today: `pip install git+https://github.com/nevodesigns/natlas-kit.git` (verified working end-to-end in a clean virtualenv), and the equivalent clone-and-build steps for the TypeScript package. PyPI/npm publishing is still planned. |

All nine fixes have regression tests: `tests/test_core.py` (Python, issues 1-6) and
`js/test/mock.test.mjs` (TypeScript, issues 1, 2, 4, 6 — issues 3 and 5 did not reproduce in
TypeScript to begin with, as noted above).

## Reviewed and intentionally unchanged

- **`classify()` returning text outside the supplied label list when nothing matches at
  all.** Ebube flagged that this weakens the guarantee that `classify()` always returns one
  of the provided labels. This is documented, intentional fallback behaviour (callers that
  need a hard guarantee can check `result in labels` themselves); changing it to raise or
  clamp would be a breaking API change we did not want to make without more real-world usage
  first. Now called out explicitly in both functions' docstrings.
- **Unsupported top-level JSON types** (`null`, an array, a bare string) correctly raise
  `SchemaError`, since the schema format only describes objects. No change needed.
- **10,000-character input** was handled without error by the CLI (Dayo's test 3). No bug
  found; full performance characteristics against a live model were not part of this round.

## What this round did not cover

Per Ebube's own scope note: no live N-ATLaS inference, no accuracy testing across Hausa,
Igbo, Yoruba or Pidgin outputs, no real ASR audio testing, no live-endpoint failure modes
(timeouts, auth errors, outages), no concurrency/performance testing, and no full package
distribution testing (since the package isn't published yet). The real N-ATLaS integration
evidence is tracked separately, in `evidence/NATLAS_integration_evidence.md`, which *was* run
against a live N-ATLaS deployment.
