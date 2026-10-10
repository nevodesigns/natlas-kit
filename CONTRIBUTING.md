# Contributing to natlas-kit

Thanks for considering a contribution. natlas-kit is a small, dependency-light toolkit, and
the easiest way to keep it that way is small, focused pull requests.

## Ways to help

- **Bug reports / feature requests** — open a GitHub issue. Include a minimal repro where you
  can (a snippet, the schema you passed to `extract`, the backend you used).
- **New task helpers** (e.g. sentiment, NER) — add them to `src/natlaskit/tasks.py` (Python)
  and the equivalent in `js/src/tasks.ts` (TypeScript), with a test for each.
- **New backends** — if you've hosted N-ATLaS somewhere not yet supported, a new `Backend`
  subclass in `backends.py` / `backends.ts` is welcome.
- **Docs** — fixes to the README, `docs/BACKENDS.md`, or the website in `web/` are always
  appreciated, especially real deployment notes from your own setup.

## Development setup

**Python**
```bash
pip install -e .[dev]
PYTHONPATH=src pytest        # offline, no GPU/network needed (mock backend)
```

**TypeScript**
```bash
cd js
npm install
npm run build
npm test                     # offline, no GPU/network needed
```

## Pull requests

1. Fork the repo and branch from `main`.
2. Keep the change focused; unrelated reformatting makes review harder.
3. Add or update tests for any behavior change — both language implementations should stay
   in sync in capability.
4. Make sure `pytest` (Python) and `npm test` (TypeScript) pass.
5. Open a PR describing what changed and why. Link any related issue.

## Reporting a problem with N-ATLaS itself

natlas-kit is a client library and doesn't control N-ATLaS's own behavior. If you've found a
model-quality issue (wrong translation, bad classification), that's valuable to document in
an issue here too — it helps calibrate the eval suite — but the fix belongs with NCAIR/Awarri.

## Code of conduct

Be respectful and constructive. This project exists to make it easier for people to build in
Nigerian languages; keep that spirit in reviews and discussion.

## License

By contributing, you agree your contribution is licensed under the project's
[MIT License](LICENSE).
