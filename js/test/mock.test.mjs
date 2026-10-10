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

// --- regression tests for issues found during external beta testing ---

test("extract handles a brace inside a string value", async () => {
  const nat = new NatlasClient({
    backend: new MockBackend('{"note":"closing brace } inside text","amount":1200}'),
  });
  const got = await extract(nat, "x", {
    note: { type: "string", required: true },
    amount: { type: "number", required: true },
  });
  assert.deepEqual(got, { note: "closing brace } inside text", amount: 1200 });
});

test("extract preserves an apostrophe during quote repair", async () => {
  const nat = new NatlasClient({ backend: new MockBackend(`{'name': "O'Connor", 'amount': 15000}`) });
  const got = await extract(nat, "x", {
    name: { type: "string", required: true },
    amount: { type: "number", required: true },
  });
  assert.equal(got.name, "O'Connor");
  assert.equal(got.amount, 15000);
});

test("extract rejects a boolean in a numeric field", async () => {
  const nat = new NatlasClient({ backend: new MockBackend(['{"amount": true}', '{"amount": 500}']) });
  const got = await extract(nat, "x", { amount: { type: "number", required: true } });
  assert.equal(got.amount, 500);
});

test("extract truncates a fractional string in an integer field", async () => {
  const nat = new NatlasClient({ backend: new MockBackend('{"quantity": "3.5"}') });
  const got = await extract(nat, "x", { quantity: { type: "integer", required: true } });
  assert.equal(got.quantity, 3);
});

test("extract truncates a fractional number in an integer field", async () => {
  const nat = new NatlasClient({ backend: new MockBackend('{"quantity": 3.5}') });
  const got = await extract(nat, "x", { quantity: { type: "integer", required: true } });
  assert.equal(got.quantity, 3);
});

test("classify prefers an exact match over a shorter substring label", async () => {
  const nat = new NatlasClient({ backend: new MockBackend("income") });
  assert.equal(await classify(nat, "salary received", ["in", "income"]), "income");
});
