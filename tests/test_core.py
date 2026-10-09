"""Offline tests. They run against MockBackend, so no GPU or network is needed."""
import json

import pytest

from natlaskit import NatlasClient, Message, extract, classify
from natlaskit.backends import MockBackend
from natlaskit.templating import build_prompt, ensure_system, EOT, SH, EH
from natlaskit.eval import run_suite


def test_templating_builds_llama3_prompt():
    msgs = ensure_system([Message("user", "Hello")])
    assert msgs[0].role == "system"
    assert "Today's date:" in msgs[0].content
    prompt = build_prompt(msgs)
    assert prompt.startswith("<|begin_of_text|>")
    assert f"{SH}user{EH}" in prompt
    assert EOT in prompt
    assert f"{SH}assistant{EH}" in prompt  # generation prompt appended


def test_ensure_system_respects_existing_system():
    msgs = ensure_system([Message("system", "custom"), Message("user", "hi")])
    assert msgs[0].content == "custom"


def test_mock_chat_roundtrip():
    nat = NatlasClient(backend=MockBackend("Barka da safe"))
    assert nat.ask("Translate good morning to Hausa") == "Barka da safe"
    assert nat.ping() is True


def test_extract_clean_json():
    payload = '{"item": "brake pads", "amount": 15000, "buyer": "Musa", "credit": true}'
    nat = NatlasClient(backend=MockBackend(payload))
    schema = {
        "item": {"type": "string", "required": True},
        "amount": {"type": "number", "required": True},
        "buyer": {"type": "string"},
        "credit": {"type": "boolean", "default": False},
    }
    got = extract(nat, "Sold brake pads for 15k to Musa on credit", schema)
    assert got == {"item": "brake pads", "amount": 15000, "buyer": "Musa", "credit": True}


def test_extract_repairs_messy_output():
    messy = "Sure! Here you go:\n```json\n{'item': 'tyre', 'amount': '30,000',}\n```"
    nat = NatlasClient(backend=MockBackend(messy))
    schema = {"item": {"type": "string", "required": True}, "amount": {"type": "number", "required": True}}
    got = extract(nat, "x", schema)
    assert got["item"] == "tyre"
    assert got["amount"] == 30000.0  # coerced from "30,000"


def test_extract_retries_then_succeeds():
    nat = NatlasClient(backend=MockBackend(["{}", '{"item":"oil","amount":5000}']))
    schema = {"item": {"type": "string", "required": True}, "amount": {"type": "number", "required": True}}
    got = extract(nat, "x", schema)
    assert got["item"] == "oil"


def test_classify_snaps_to_label():
    nat = NatlasClient(backend=MockBackend("This looks like an EXPENSE to me"))
    assert classify(nat, "bought fuel", ["income", "expense"]) == "expense"


def test_eval_suite_runs():
    nat = NatlasClient(backend=MockBackend("The answer is Lagos"))
    cases = [{"name": "cap", "kind": "chat", "input": "Capital?", "contains": ["Lagos"]}]
    report = run_suite(nat, cases)
    assert report["passed"] == 1 and report["pass_rate"] == 1.0
