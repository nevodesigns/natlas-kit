import type { NatlasClient } from "./client.js";

const LANGS: Record<string, string> = {
  en: "English", ha: "Hausa", ig: "Igbo", yo: "Yoruba", pcm: "Nigerian Pidgin",
};
const name = (c: string) => LANGS[c.toLowerCase()] ?? c;

export async function translate(client: NatlasClient, text: string, toLang: string, fromLang?: string) {
  const src = fromLang ? `from ${name(fromLang)} ` : "";
  return (await client.chat([
    { role: "system", content: "You are a professional translator for Nigerian languages. Reply with only the translation." },
    { role: "user", content: `Translate the following ${src}into ${name(toLang)}:\n\n${text}` },
  ])).text.trim();
}

export async function detectLanguage(client: NatlasClient, text: string) {
  return (await client.chat([
    { role: "system", content: "Identify the language. Reply with exactly one of: English, Hausa, Igbo, Yoruba, Nigerian Pidgin." },
    { role: "user", content: text },
  ], { maxNewTokens: 8 })).text.trim();
}

/** Classify `text` into one of `labels`. Returns the raw model text unchanged if
 * nothing matches (callers that need a hard guarantee should check the result
 * is one of `labels` themselves). */
export async function classify(client: NatlasClient, text: string, labels: string[]) {
  const out = (await client.chat([
    { role: "system", content: "You are a classifier. Reply with exactly one label and nothing else.\nLabels: " + labels.join(", ") },
    { role: "user", content: text },
  ], { maxNewTokens: 16 })).text.trim();
  const low = out.toLowerCase();
  const exact = labels.find((l) => l.trim().toLowerCase() === low);
  if (exact) return exact;
  // longest labels first, so a short label ("in") can't win just because it
  // happens to be a substring of a longer one ("income")
  const bySize = [...labels].sort((a, b) => b.length - a.length);
  return bySize.find((l) => low.includes(l.toLowerCase())) ?? out;
}

export async function summarize(client: NatlasClient, text: string, sentences = 3, lang = "English") {
  return (await client.chat([
    { role: "system", content: `Summarize clearly in ${name(lang)}, in at most ${sentences} sentences.` },
    { role: "user", content: text },
  ])).text.trim();
}
