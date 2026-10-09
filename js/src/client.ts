import { Backend, makeBackend } from "./backends.js";
import { ChatResult, DEFAULTS, GenerationConfig, Message } from "./types.js";

export interface NatlasClientOptions {
  backend?: string | Backend;
  endpoint?: string;
  token?: string;
  model?: string;
  config?: GenerationConfig;
  responses?: string | string[] | ((m: Message[]) => string); // mock only
}

export class NatlasClient {
  readonly backend: Backend;
  private config: Required<GenerationConfig>;

  constructor(opts: NatlasClientOptions = {}) {
    this.backend =
      typeof opts.backend === "object"
        ? opts.backend
        : makeBackend(opts.backend ?? "mock", {
            endpoint: opts.endpoint, token: opts.token, model: opts.model, responses: opts.responses,
          });
    this.config = { ...DEFAULTS, ...opts.config };
  }

  /** Build from NATLAS_BACKEND / NATLAS_ENDPOINT / NATLAS_TOKEN / NATLAS_MODEL (Node). */
  static fromEnv(overrides: NatlasClientOptions = {}): NatlasClient {
    const env = (typeof process !== "undefined" ? process.env : {}) as Record<string, string | undefined>;
    return new NatlasClient({
      backend: overrides.backend ?? env.NATLAS_BACKEND ?? "mock",
      endpoint: overrides.endpoint ?? env.NATLAS_ENDPOINT,
      token: overrides.token ?? env.NATLAS_TOKEN,
      model: overrides.model ?? env.NATLAS_MODEL ?? "N-ATLaS",
      ...overrides,
    });
  }

  async chat(messages: Message[], params: GenerationConfig = {}): Promise<ChatResult> {
    return this.backend.generate(messages, { ...this.config, ...params });
  }

  async ask(prompt: string, opts: { system?: string } & GenerationConfig = {}): Promise<string> {
    const { system, ...params } = opts;
    const msgs: Message[] = [];
    if (system) msgs.push({ role: "system", content: system });
    msgs.push({ role: "user", content: prompt });
    return (await this.chat(msgs, params)).text;
  }

  async ping(): Promise<boolean> {
    try {
      await this.chat([{ role: "user", content: "Reply with: OK" }], { maxNewTokens: 8 });
      return true;
    } catch {
      return false;
    }
  }
}
