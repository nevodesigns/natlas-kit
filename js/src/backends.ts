import { buildPrompt, clean, ensureSystem } from "./llama3.js";
import { BackendError, ChatResult, DEFAULTS, GenerationConfig, Message } from "./types.js";

export interface Backend {
  name: string;
  generate(messages: Message[], cfg: Required<GenerationConfig>): Promise<ChatResult>;
}

function headers(token?: string): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

/** Hugging Face Text-Generation-Inference (/generate). */
export class TgiBackend implements Backend {
  name = "tgi";
  constructor(private endpoint: string, private token?: string, private timeout = 120000) {
    this.endpoint = endpoint.replace(/\/$/, "");
  }
  async generate(messages: Message[], cfg: Required<GenerationConfig>): Promise<ChatResult> {
    const payload = {
      inputs: buildPrompt(ensureSystem(messages)),
      parameters: {
        max_new_tokens: cfg.maxNewTokens,
        temperature: Math.max(cfg.temperature, 1e-3),
        top_p: cfg.topP,
        repetition_penalty: cfg.repetitionPenalty,
        stop: cfg.stop,
        return_full_text: false,
      },
    };
    const t0 = Date.now();
    const r = await fetchJson(`${this.endpoint}/generate`, payload, headers(this.token), this.timeout);
    const text = Array.isArray(r) ? r[0]?.generated_text : r?.generated_text;
    return { text: clean(text ?? ""), raw: r, latencyMs: Date.now() - t0, backend: this.name };
  }
}

/** OpenAI-compatible server (vLLM, ollama, …) (/v1/chat/completions). */
export class OpenAIBackend implements Backend {
  name = "openai";
  constructor(private endpoint: string, private token?: string,
              private model = "N-ATLaS", private timeout = 120000) {
    this.endpoint = endpoint.replace(/\/$/, "");
  }
  async generate(messages: Message[], cfg: Required<GenerationConfig>): Promise<ChatResult> {
    const payload = {
      model: this.model,
      messages: ensureSystem(messages),
      max_tokens: cfg.maxNewTokens,
      temperature: cfg.temperature,
      top_p: cfg.topP,
      stop: cfg.stop.filter((s) => !s.startsWith("<|")),
    };
    const t0 = Date.now();
    const r = await fetchJson(`${this.endpoint}/v1/chat/completions`, payload, headers(this.token), this.timeout);
    const text = r?.choices?.[0]?.message?.content;
    if (typeof text !== "string") throw new BackendError(`unexpected response: ${JSON.stringify(r).slice(0, 200)}`);
    return { text: clean(text), raw: r, latencyMs: Date.now() - t0, backend: this.name };
  }
}

/** Deterministic offline backend for development and tests. */
export class MockBackend implements Backend {
  name = "mock";
  private i = 0;
  constructor(private responses?: string | string[] | ((m: Message[]) => string)) {}
  async generate(messages: Message[]): Promise<ChatResult> {
    let text: string;
    if (typeof this.responses === "function") text = this.responses(messages);
    else if (Array.isArray(this.responses) && this.responses.length)
      text = this.responses[this.i++ % this.responses.length];
    else if (typeof this.responses === "string") text = this.responses;
    else {
      const last = [...messages].reverse().find((m) => m.role === "user")?.content ?? "";
      text = `[mock N-ATLaS reply to: ${last.slice(0, 80)}]`;
    }
    return { text, raw: { mock: true }, latencyMs: 0, backend: this.name };
  }
}

async function fetchJson(url: string, body: unknown, hdrs: Record<string, string>, timeout: number) {
  const ctrl = new AbortController();
  const id = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(url, { method: "POST", headers: hdrs, body: JSON.stringify(body), signal: ctrl.signal });
    if (!res.ok) throw new BackendError(`${res.status}: ${(await res.text()).slice(0, 300)}`);
    return await res.json();
  } catch (e) {
    if (e instanceof BackendError) throw e;
    throw new BackendError(`request to ${url} failed: ${(e as Error).message}`);
  } finally {
    clearTimeout(id);
  }
}

export function makeBackend(kind: string, opts: { endpoint?: string; token?: string; model?: string;
  responses?: string | string[] | ((m: Message[]) => string) } = {}): Backend {
  switch ((kind || "mock").toLowerCase()) {
    case "mock": return new MockBackend(opts.responses);
    case "tgi":
      if (!opts.endpoint) throw new BackendError("tgi backend needs an endpoint");
      return new TgiBackend(opts.endpoint, opts.token);
    case "openai":
    case "vllm":
      if (!opts.endpoint) throw new BackendError("openai backend needs an endpoint");
      return new OpenAIBackend(opts.endpoint, opts.token, opts.model ?? "N-ATLaS");
    default: throw new BackendError(`unknown backend '${kind}' (use tgi | openai | mock)`);
  }
}

export { DEFAULTS };
