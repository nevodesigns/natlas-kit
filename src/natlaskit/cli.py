"""Command-line interface: `natlas <command>`.

Config comes from env (NATLAS_BACKEND, NATLAS_ENDPOINT, NATLAS_TOKEN, NATLAS_MODEL)
or flags. Examples:
    natlas ping
    natlas ask "Translate 'welcome' to Igbo"
    natlas extract "Sold 2 tyres for 30k to Musa on credit" --schema sale.json
    natlas eval evals/suite_core.json
    natlas transcribe clip.wav
"""
import argparse
import json
import sys

from . import __version__
from .asr import ASRClient
from .client import NatlasClient
from .eval import load_suite, run_suite, to_markdown
from .extract import extract


def _client(args) -> NatlasClient:
    return NatlasClient.from_env(
        backend=args.backend, endpoint=args.endpoint, token=args.token, model=args.model)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="natlas", description="Developer toolkit for N-ATLaS.")
    p.add_argument("--backend", help="tgi | openai | mock (default: env NATLAS_BACKEND or mock)")
    p.add_argument("--endpoint", help="N-ATLaS endpoint URL")
    p.add_argument("--token", help="bearer token for the endpoint")
    p.add_argument("--model", help="served model name (openai backend)")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("version")
    sub.add_parser("ping")

    a = sub.add_parser("ask")
    a.add_argument("prompt")
    a.add_argument("--system")
    a.add_argument("--max-new-tokens", type=int, default=None)

    e = sub.add_parser("extract")
    e.add_argument("text")
    e.add_argument("--schema", required=True, help="path to a JSON schema file")

    t = sub.add_parser("transcribe")
    t.add_argument("audio")
    t.add_argument("--asr-endpoint")
    t.add_argument("--asr-token")

    v = sub.add_parser("eval")
    v.add_argument("suite", help="path to a JSON eval suite")
    v.add_argument("--json", action="store_true", help="print raw JSON report")

    args = p.parse_args(argv)

    if args.cmd in (None, "version"):
        print(f"natlas-kit {__version__}")
        return 0

    if args.cmd == "ping":
        ok = _client(args).ping()
        print("ok" if ok else "unreachable")
        return 0 if ok else 1

    if args.cmd == "ask":
        extra = {"max_new_tokens": args.max_new_tokens} if args.max_new_tokens else {}
        print(_client(args).ask(args.prompt, system=args.system, **extra))
        return 0

    if args.cmd == "extract":
        with open(args.schema, encoding="utf-8") as f:
            schema = json.load(f)
        result = extract(_client(args), args.text, schema)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "transcribe":
        asr = ASRClient(endpoint=args.asr_endpoint, token=args.asr_token)
        print(asr.transcribe_file(args.audio))
        return 0

    if args.cmd == "eval":
        report = run_suite(_client(args), load_suite(args.suite))
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else to_markdown(report))
        return 0 if report["passed"] == report["total"] else 2

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
