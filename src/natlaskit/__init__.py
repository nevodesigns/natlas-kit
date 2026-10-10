"""natlas-kit: a community developer toolkit for NCAIR's N-ATLaS models.

Quickstart:
    from natlaskit import NatlasClient
    nat = NatlasClient.from_env()          # or NatlasClient("tgi", endpoint=..., token=...)
    print(nat.ask("Translate 'good morning' to Hausa"))

Not affiliated with NCAIR, NITDA or Awarri Technologies. N-ATLaS is their work;
see NOTICE for required attribution and the model's license.
"""
from .client import NatlasClient
from .types import GenerationConfig, Message, ChatResult
from .extract import extract
from .tasks import translate, detect_language, classify, summarize
from .asr import ASRClient
from .errors import NatlasError, BackendError, SchemaError

__version__ = "0.1.1"

__all__ = [
    "NatlasClient", "GenerationConfig", "Message", "ChatResult",
    "extract", "translate", "detect_language", "classify", "summarize",
    "ASRClient", "NatlasError", "BackendError", "SchemaError", "__version__",
]
