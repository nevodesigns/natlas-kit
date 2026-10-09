"""Smallest possible N-ATLaS call through natlas-kit.

Run for real:
    export NATLAS_BACKEND=tgi
    export NATLAS_ENDPOINT=https://your-n-atlas-endpoint
    export NATLAS_TOKEN=hf_xxx
    python examples/quickstart.py
Run offline (mock), just to see the shape:
    python examples/quickstart.py
"""
import os

from natlaskit import NatlasClient
from natlaskit.backends import MockBackend

if os.getenv("NATLAS_BACKEND"):
    nat = NatlasClient.from_env()
else:
    print("(no NATLAS_BACKEND set, using offline mock)\n")
    nat = NatlasClient(backend=MockBackend("Ẹ kú àárọ̀ (good morning in Yoruba)."))

print(nat.ask("Translate 'good morning' into Yoruba. Reply with only the translation."))
