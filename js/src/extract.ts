import { SchemaError } from "./types.js";
import type { Message } from "./types.js";
import type { NatlasClient } from "./client.js";

export interface FieldSpec {
  type?: "string" | "number" | "integer" | "boolean" | "array" | "object";
  required?: boolean;
  description?: string;
  default?: unknown;
}
export type Schema = Record<string, FieldSpec>;

function schemaLines(schema: Schema): string {
  return Object.entries(schema)
    .map(([name, s]) => {
      const req = s.required ? "required" : "optional";
      return `  "${name}": <${s.type ?? "string"}>  (${req})${s.description ? " - " + s.description : ""}`;
    })
    .join("\n");
}

function findJson(text: string): string {
  let t = text.replace(/```json/gi, "```").trim();
  if (t.includes("```")) {
    const parts = t.split("```");
    if (parts.length > 1) t = parts[1];
  }
  const start = t.indexOf("{");
  if (start === -1) throw new SchemaError("no JSON object found in model reply");
  let depth = 0;
  for (let i = start; i < t.length; i++) {
    if (t[i] === "{") depth++;
    else if (t[i] === "}" && --depth === 0) return t.slice(start, i + 1);
  }
  throw new SchemaError("unbalanced JSON object in model reply");
}

function parse(blob: string): Record<string, unknown> {
  try {
    return JSON.parse(blob);
  } catch {
    const repaired = blob.replace(/,(\s*[}\]])/g, "$1").replace(/'/g, '"');
    return JSON.parse(repaired);
  }
}

function validate(obj: Record<string, unknown>, schema: Schema): string[] {
  const errs: string[] = [];
  for (const [name, s] of Object.entries(schema)) {
    const v = obj[name];
    if (v === undefined || v === null) {
      if (s.required) errs.push(`missing required field '${name}'`);
      else if ("default" in s) obj[name] = s.default;
      continue;
    }
    const t = s.type ?? "string";
    const ok =
      (t === "string" && typeof v === "string") ||
      (t === "boolean" && typeof v === "boolean") ||
      ((t === "number" || t === "integer") && typeof v === "number") ||
      (t === "array" && Array.isArray(v)) ||
      (t === "object" && typeof v === "object" && !Array.isArray(v));
    if (!ok) {
      if ((t === "number" || t === "integer") && typeof v === "string") {
        const n = Number(v.replace(/,/g, "").trim());
        if (!Number.isNaN(n)) {
          obj[name] = t === "integer" ? Math.round(n) : n;
          continue;
        }
      }
      errs.push(`field '${name}' should be ${t}, got ${Array.isArray(v) ? "array" : typeof v}`);
    }
  }
  return errs;
}

export async function extract(
  client: NatlasClient,
  text: string,
  schema: Schema,
  opts: { instructions?: string; retries?: number } = {},
): Promise<Record<string, unknown>> {
  const retries = opts.retries ?? 1;
  const sys =
    "You are a precise information extraction engine. Reply with ONE JSON object and " +
    "nothing else, no prose, no code fences.";
  const prompt =
    (opts.instructions ? opts.instructions + "\n\n" : "") +
    "Extract the fields below from the text. Use null when a value is absent.\n\n" +
    "Fields:\n" + schemaLines(schema) + "\n\nText:\n" + text.trim() + "\n\nJSON:";
  const messages: Message[] = [
    { role: "system", content: sys },
    { role: "user", content: prompt },
  ];
  let lastErr = "";
  for (let attempt = 0; attempt <= retries; attempt++) {
    const reply = (await client.chat(messages)).text;
    try {
      const obj = parse(findJson(reply));
      const errs = validate(obj, schema);
      if (errs.length === 0) {
        const out: Record<string, unknown> = {};
        for (const k of Object.keys(schema)) out[k] = k in obj ? obj[k] : schema[k].default;
        return out;
      }
      lastErr = errs.join("; ");
    } catch (e) {
      lastErr = (e as Error).message;
    }
    messages.push({ role: "assistant", content: reply });
    messages.push({ role: "user", content: `That was invalid (${lastErr}). Return corrected JSON only.` });
  }
  throw new SchemaError(`could not extract valid data after ${retries + 1} tries: ${lastErr}`);
}
