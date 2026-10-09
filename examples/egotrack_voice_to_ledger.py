"""EgoTrack example: a trader speaks a sale in Pidgin/Yoruba, N-ATLaS turns it into
a clean ledger entry. This is the real reason natlas-kit exists.

Flow:  microphone --(N-ATLaS ASR)--> text --(natlas-kit extract)--> transaction JSON

Here we start from the transcribed text (swap in ASRClient.transcribe_file for audio).
Run for real with NATLAS_* env vars; offline it uses a scripted mock so you can see
the output shape without a GPU.
"""
import json
import os

from natlaskit import NatlasClient, extract
from natlaskit.backends import MockBackend

SALE_SCHEMA = {
    "kind": {"type": "string", "required": True, "description": "income or expense"},
    "item": {"type": "string", "required": True, "description": "what was sold or bought"},
    "quantity": {"type": "integer", "default": 1},
    "amount": {"type": "number", "required": True, "description": "total value in naira"},
    "amount_paid": {"type": "number", "description": "cash received now (<= amount if on credit)"},
    "counterparty": {"type": "string", "description": "customer or supplier name"},
    "on_credit": {"type": "boolean", "default": False},
}

# What the trader said, as N-ATLaS ASR would transcribe it (Nigerian Pidgin):
spoken = "I sell one alternator for sixty-eight thousand give Emeka Motors, dem pay fifty, remaining go be credit."

if os.getenv("NATLAS_BACKEND"):
    nat = NatlasClient.from_env()
else:
    print("(offline mock; set NATLAS_BACKEND to run against a real N-ATLaS endpoint)\n")
    scripted = json.dumps({
        "kind": "income", "item": "alternator", "quantity": 1, "amount": 68000,
        "amount_paid": 50000, "counterparty": "Emeka Motors", "on_credit": True,
    })
    nat = NatlasClient(backend=MockBackend(scripted))

print("Heard:", spoken, "\n")
entry = extract(nat, spoken, SALE_SCHEMA,
                instructions="This is a market trader describing one transaction in Nigerian Pidgin.")
print("Ledger entry:")
print(json.dumps(entry, ensure_ascii=False, indent=2))

balance = (entry["amount"] or 0) - (entry.get("amount_paid") or 0)
if entry.get("on_credit") and balance > 0:
    print(f"\n-> Also opens a debt of N{balance:,.0f} for {entry.get('counterparty')}.")
