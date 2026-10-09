import type { Message } from "./types.js";

const BOT = "<|begin_of_text|>";
const SH = "<|start_header_id|>";
const EH = "<|end_header_id|>";
const EOT = "<|eot_id|>";

export const DEFAULT_SYSTEM =
  "You are N-ATLaS, a helpful multilingual assistant trained by Awarri technologies " +
  "for the National Centre for Artificial Intelligence and Robotics (NCAIR). You " +
  "understand English, Hausa, Igbo, Yoruba and Nigerian Pidgin.";

export function systemText(system?: string, today?: string): string {
  const base = system ?? DEFAULT_SYSTEM;
  const d = today ?? new Date().toISOString().slice(0, 10);
  return `${base}\nToday's date: ${d}.`;
}

/** Put a correct N-ATLaS system message at the front unless the caller already did. */
export function ensureSystem(messages: Message[], system?: string, today?: string): Message[] {
  if (messages.length && messages[0].role === "system") return [...messages];
  return [{ role: "system", content: systemText(system, today) }, ...messages];
}

/** Raw Llama-3 / N-ATLaS prompt string, for text-generation endpoints (TGI). */
export function buildPrompt(messages: Message[], addGenerationPrompt = true): string {
  const parts = [BOT];
  for (const m of messages) parts.push(`${SH}${m.role}${EH}\n\n${m.content}${EOT}`);
  if (addGenerationPrompt) parts.push(`${SH}assistant${EH}\n\n`);
  return parts.join("");
}

export function clean(text: string): string {
  return text.replace(/<\|eot_id\|>|<\|end_of_text\|>/g, "").trim();
}
