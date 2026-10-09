export type Role = "system" | "user" | "assistant";

export interface Message {
  role: Role;
  content: string;
}

export interface GenerationConfig {
  maxNewTokens?: number;
  temperature?: number;
  topP?: number;
  repetitionPenalty?: number;
  stop?: string[];
}

/** Defaults mirror the N-ATLaS model card (temperature 0.1, repetition_penalty 1.12). */
export const DEFAULTS: Required<GenerationConfig> = {
  maxNewTokens: 512,
  temperature: 0.1,
  topP: 0.9,
  repetitionPenalty: 1.12,
  stop: ["<|eot_id|>"],
};

export interface ChatResult {
  text: string;
  latencyMs?: number;
  backend?: string;
  raw?: unknown;
}

export class NatlasError extends Error {}
export class BackendError extends NatlasError {}
export class SchemaError extends NatlasError {}
