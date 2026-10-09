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

export async function classify(client: NatlasClient, text: string, labels: string[]) {
  const out = (await client.chat([
    { role: "system", content: "You are a classifier. Reply with exactly one label and nothing else.\nLabels: " + labels.join(", ") },
    { role: "user", content: text },
  ], { maxNewTokens: 16 })).text.trim();
  const low = out.toLowerCase();
  return labels.find((l) => low.includes(l.toLowerCase())) ?? out;
}

export async function summarize(client: NatlasClient, text: string, sentences = 3, lang = "English") {
  return (await client.chat([
    { role: "system", content: `Summarize clearly in ${name(lang)}, in at most ${sentences} sentences.` },
    { role: "user", content: text },
  ])).text.trim();
}
