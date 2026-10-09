# Hosting N-ATLaS and pointing natlas-kit at it

N-ATLaS has no public inference API, so you run the weights once and give natlas-kit the
endpoint. You only do this setup once; after that every example, the CLI and your app use
the same `NATLAS_*` env vars.

The model is gated on Hugging Face (`NCAIR1/N-ATLaS`) — log in and accept the license first.
It is a Llama-3 8B model, so plan for a GPU with ~16 GB VRAM (bf16) or use a quantized build
(the model tree lists GGUF/quantized variants for smaller GPUs or CPU).

## Option A — Hugging Face Inference Endpoints (TGI)  →  `NATLAS_BACKEND=tgi`

1. On huggingface.co, open `NCAIR1/N-ATLaS` → **Deploy → Inference Endpoints**.
2. Pick a GPU (e.g. an A10G/L4 for bf16) and the **Text Generation Inference** container.
3. When it is running, copy the endpoint URL and your HF token.

```bash
export NATLAS_BACKEND=tgi
export NATLAS_ENDPOINT=https://xxxx.endpoints.huggingface.cloud
export NATLAS_TOKEN=hf_your_token
natlas ping
```

natlas-kit calls `POST {endpoint}/generate` with the full N-ATLaS prompt it builds for you.

## Option B — vLLM (OpenAI-compatible)  →  `NATLAS_BACKEND=openai`

On any GPU box:

```bash
pip install vllm
vllm serve NCAIR1/N-ATLaS --served-model-name N-ATLaS --dtype bfloat16 --max-model-len 8092
```

```bash
export NATLAS_BACKEND=openai
export NATLAS_ENDPOINT=http://your-host:8000
export NATLAS_MODEL=N-ATLaS
natlas ping
```

natlas-kit calls `POST {endpoint}/v1/chat/completions`.

## Option C — offline mock  →  `NATLAS_BACKEND=mock` (default)

No endpoint. Returns deterministic text so you can develop logic and run the test suite
without a GPU. Great for CI.

## Speech-to-text (ASR)

The N-ATLaS ASR models are separate repos. Deploy one as a Hugging Face Inference Endpoint
(audio pipeline), then:

```bash
export NATLAS_ASR_ENDPOINT=https://your-asr-endpoint
export NATLAS_ASR_TOKEN=hf_your_token
natlas transcribe sale.wav
```
