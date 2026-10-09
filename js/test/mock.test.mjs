import { test } from "node:test";
import assert from "node:assert/strict";
import { NatlasClient, MockBackend, extract, classify } from "../dist/index.js";
import { buildPrompt, ensureSystem } from "../dist/llama3.js";

test("templating builds a Llama-3 prompt with a dated system header", () => {
  const msgs = ensureSystem([{ role: "user", content: "Hello" }]);
  assert.equal(msgs[0].role, "system");
  assert.ok(msgs[0].content.includes("Today's date:"));
  const p = buildPrompt(msgs);
  assert.ok(p.startsWith("<|begin_of_text|>"));
  assert.ok(p.includes("<|start_header_id|>assistant<|end_header_id|>"));
});

test("mock chat round-trip", async () => {
  const nat = new NatlasClient({ backend: new MockBackend("Barka da safe") });
  assert.equal(await nat.ask("translate good morning to Hausa"), "Barka da safe");
  assert.equal(await nat.ping(), true);
});

test("extract clean JSON", async () => {
  const nat = new NatlasClient({
    backend: new MockBackend('{"item":"brake pads","amount":15000,"buyer":"Musa","on_credit":true}'),
  });
  const schema = {
    item: { type: "string", required: true },
    amount: { type: "number", required: true },
    buyer: { type: "string" },
    on_credit: { type: "boolean", default: false },
  };
  const got = await extract(nat, "Sold brake pads for 15k to Musa on credit", schema);
  assert.deepEqual(got, { item: "brake pads", amount: 15000, buyer: "Musa", on_credit: true });
});

test("extract repairs messy output and coerces numbers", async () => {
  const nat = new NatlasClient({
    backend: new MockBackend("Sure!\n```json\n{'item':'tyre','amount':'30,000',}\n```"),
  });
  const got = await extract(nat, "x", {
    item: { type: "string", required: true },
    amount: { type: "number", required: true },
  });
  assert.equal(got.item, "tyre");
  assert.equal(got.amount, 30000);
});

test("extract retries then succeeds", async () => {
  const nat = new NatlasClient({ backend: new MockBackend(["{}", '{"item":"oil","amount":5000}']) });
  const got = await extract(nat, "x", {
    item: { type: "string", required: true },
    amount: { type: "number", required: true },
  });
  assert.equal(got.item, "oil");
});

test("classify snaps to a provided label", async () => {
  const nat = new NatlasClient({ backend: new MockBackend("This looks like an EXPENSE to me") });
  assert.equal(await classify(nat, "bought fuel", ["income", "expense"]), "expense");
});
