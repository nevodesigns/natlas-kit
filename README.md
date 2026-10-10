# natlas-kit

**A developer toolkit that makes [N-ATLaS](https://huggingface.co/NCAIR1/N-ATLaS) easy to build with.**

🌐 **Website:** https://nevodesigns.github.io/natlas-kit/

N-ATLaS (the Nigerian Atlas for Languages and AI at Scale) is NCAIR's open LLM for
English, Hausa, Igbo and Yoruba, plus a set of speech-to-text models. It is powerful,
but building *applications* on top of it is harder than it should be:

- There is **no hosted inference API**, so you must self-host and speak the right protocol.
- It uses the **Llama-3 chat format with a dated system header** that is easy to get wrong (the official example even forgets to `import datetime`).
- Like any chat model, it does **not reliably return structured data** (JSON) for forms, fintech or pipelines.
- The **ASR models are separate repos** with no unified client.

`natlas-kit` fixes all four. It is a small, dependency-light Python package (plus a CLI)
that gives you one clean way to call N-ATLaS for text and speech, get **validated JSON**
out of it, run Nigerian-language tasks, and **measure** your integration.

> Built while adding Nigerian-language AI to [EgoTrack](https://egotrack-app.vercel.app)
> (a ledger for market traders), then open-sourced for every N-ATLaS builder.
> Submitted to the NITDA/NCAIR **National AI Innovation Challenge (NAIC) 2026**,
> Problem Statement 1: *Developer Infrastructure*.

`natlas-kit` is an independent community SDK. It is **not affiliated** with NCAIR, NITDA
or Awarri Technologies; see [NOTICE](NOTICE) for required attribution and the model license.

**Two languages, one toolkit.** natlas-kit ships a **Python** package (this directory, for the
AI/ML ecosystem) *and* a **TypeScript/JavaScript** client ([`js/`](js/), for the web, React,
React Native and Next.js apps most Nigerian developers build). Same API, same structured-output
feature, in the language you already use.

---

## Install

Not yet on PyPI, so install straight from GitHub for now:

```bash
pip install git+https://github.com/nevodesigns/natlas-kit.git
# or, from a local clone:
git clone https://github.com/nevodesigns/natlas-kit.git && cd natlas-kit && pip install -e .
```

Core install needs only `requests`. Optional extras: `pip install "natlas-kit[hf] @ git+https://github.com/nevodesigns/natlas-kit.git"`
(Hugging Face client), `[dev]` (tests, from a local clone: `pip install -e .[dev]`).

## Quickstart

```python
from natlaskit import NatlasClient

nat = NatlasClient.from_env()          # reads NATLAS_BACKEND / NATLAS_ENDPOINT / NATLAS_TOKEN
print(nat.ask("Translate 'good morning' into Yoruba. Reply with only the translation."))
```

No endpoint yet? Everything runs offline against a mock backend, so you can develop and
test with no GPU:

```python
from natlaskit import NatlasClient
from natlaskit.backends import MockBackend
nat = NatlasClient(backend=MockBackend("Ẹ kú àárọ̀"))
```

## Point it at a real N-ATLaS endpoint

N-ATLaS has no public API, so you host the weights once and give natlas-kit the URL.
Two supported shapes (see [docs/BACKENDS.md](docs/BACKENDS.md) for full commands):

| Backend | Serve N-ATLaS with | natlas-kit config |
| --- | --- | --- |
| `tgi` | Hugging Face **Inference Endpoints** (TGI image) | `NATLAS_BACKEND=tgi`, `NATLAS_ENDPOINT=https://…`, `NATLAS_TOKEN=hf_…` |
| `openai` | **vLLM** (`--served-model-name N-ATLaS`) | `NATLAS_BACKEND=openai`, `NATLAS_ENDPOINT=http://host:8000`, `NATLAS_MODEL=N-ATLaS` |

The toolkit builds the correct Llama-3 / N-ATLaS prompt (with today's date) for you, and
applies the model card's defaults (`temperature=0.1`, `repetition_penalty=1.12`).

## What you get

**1. Clean chat/generate**
```python
nat.ask("Kini oruko re?", system="Reply in Yoruba.")
nat.chat([{"role": "user", "content": "Explain VAT simply in Pidgin"}], max_new_tokens=200)
```

**2. Structured extraction** (the headline feature) — turn free text into validated JSON:
```python
from natlaskit import extract
schema = {
  "item":   {"type": "string",  "required": True},
  "amount": {"type": "number",  "required": True, "description": "total in naira"},
  "buyer":  {"type": "string"},
  "on_credit": {"type": "boolean", "default": False},
}
extract(nat, "Sold 2 brake pads for 15k to Musa on credit", schema)
# -> {'item': 'brake pads', 'amount': 15000, 'buyer': 'Musa', 'on_credit': True}
```
It parses messy replies (prose, code fences, single quotes, trailing commas), coerces
`"15,000"` to a number, validates against your schema, and retries with the error fed back.

**3. Nigerian-language task helpers**
```python
from natlaskit import translate, detect_language, classify, summarize
translate(nat, "How much is this?", to_lang="ha")
detect_language(nat, "Kedu ka ọ dị")
classify(nat, "bought fuel for the generator", ["income", "expense"])
```

**4. Speech-to-text** with the N-ATLaS ASR models:
```python
from natlaskit import ASRClient
text = ASRClient(endpoint="https://your-asr-endpoint").transcribe_file("sale.wav")
```

**5. An eval harness** to prove (and keep proving) your integration works:
```bash
natlas eval evals/suite_core.json          # pass rate + latency report
```

## CLI

```bash
natlas ping
natlas ask "Translate 'welcome' into Igbo"
natlas extract "Sold 2 tyres for 30k to Musa on credit" --schema examples/sale.json
natlas transcribe clip.wav --asr-endpoint https://your-asr-endpoint
natlas eval evals/suite_core.json
```

## The EgoTrack example

`examples/egotrack_voice_to_ledger.py` takes a sentence a trader *speaks* in Pidgin and
turns it into a ledger entry (and detects the resulting debt) — the "Nigerians who do not
type" use case, powered end to end by N-ATLaS + natlas-kit:

```
Heard: I sell one alternator for sixty-eight thousand give Emeka Motors, dem pay fifty, remaining go be credit.
Ledger entry: {"kind":"income","item":"alternator","amount":68000,"amount_paid":50000,"counterparty":"Emeka Motors","on_credit":true}
-> Also opens a debt of N18,000 for Emeka Motors.
```

## Develop & test

```bash
PYTHONPATH=src python -m pytest        # 8 offline tests, no GPU/network needed
```

## License & attribution

natlas-kit is released under the [MIT License](LICENSE). It calls N-ATLaS; it does not
contain or modify the model weights. N-ATLaS itself is published by **Awarri Technologies**
for **NCAIR** under its own license (use limited to ≤1,000 active users / 30 days without a
commercial agreement, attribution required). See [NOTICE](NOTICE).
