# natlas-kit (TypeScript / JavaScript)

The JS/TS half of [natlas-kit](../README.md) — the same N-ATLaS developer toolkit, for the
language most Nigerian app and web developers actually build in. Works in Node 18+ and the
browser, zero runtime dependencies (uses the built-in `fetch`).

Not yet on npm, so for now, clone and build it locally:

```bash
git clone https://github.com/nevodesigns/natlas-kit.git
cd natlas-kit/js
npm install && npm run build
```

Then import it with a relative or `file:` path, e.g. from your project:
```bash
npm install file:../natlas-kit/js
```

```ts
import { NatlasClient, extract } from "natlas-kit";

const nat = NatlasClient.fromEnv(); // NATLAS_BACKEND / NATLAS_ENDPOINT / NATLAS_TOKEN / NATLAS_MODEL
// or: new NatlasClient({ backend: "openai", endpoint: "http://localhost:11434", model: "natlas" });

await nat.ask("Translate 'good morning' into Yoruba. Reply with only the translation.");

// Structured output (the headline feature): free text -> validated JSON
const sale = await extract(nat, "Sold 2 brake pads for 15k to Musa on credit", {
  item:   { type: "string",  required: true },
  amount: { type: "number",  required: true },
  buyer:  { type: "string" },
  on_credit: { type: "boolean", default: false },
});
// -> { item: "brake pads", amount: 15000, buyer: "Musa", on_credit: true }
```

It parses messy replies (prose, code fences, single quotes, trailing commas), coerces
`"15,000"` to a number, validates against your schema, and retries with the error fed back.

## Backends

| Backend | Serve N-ATLaS with | Config |
| --- | --- | --- |
| `openai` | vLLM / **ollama** / any OpenAI-compatible server | `new NatlasClient({ backend: "openai", endpoint, model })` |
| `tgi` | Hugging Face Inference Endpoints (TGI) | `new NatlasClient({ backend: "tgi", endpoint, token })` |
| `mock` | offline, deterministic (dev + tests) | `new NatlasClient({ backend: new MockBackend("...") })` |

## Also included

```ts
import { translate, detectLanguage, classify, summarize } from "natlas-kit";
await translate(nat, "How much?", "ha");
await detectLanguage(nat, "Kedu ka ọ dị");
await classify(nat, "bought fuel for the generator", ["income", "expense"]);
```

## Why a JS client matters

EgoTrack is a Next.js app. So are most Nigerian web and React Native products. Shipping the
same N-ATLaS toolkit in TypeScript means a web team can add Nigerian-language AI without
leaving their stack. This is the client EgoTrack uses for its own voice-to-ledger feature.

## Develop

```bash
npm install && npm run build && npm test   # 6 offline tests, no GPU/network
```

MIT. Not affiliated with NCAIR/NITDA/Awarri. See [../NOTICE](../NOTICE).
