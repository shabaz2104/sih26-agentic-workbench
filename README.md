# Model Access Controller

This repository contains the Model Access Controller for the SIH 2026
workbench: a small, provider-independent gateway for model generation.

The controller currently supports two task types:

- `coding`
- `general`

It validates a request, classifies it with deterministic keyword rules when no
task type is supplied, selects a configured model route, invokes a provider
abstraction, and returns a normalized response.

## OpenAI-compatible provider

`OpenAICompatibleProvider` sends JSON over HTTP to a chat-completions endpoint
that follows the OpenAI API shape. The controller only sees the `ModelProvider`
abstraction; it does not know about HTTP or the server implementation. A
configured base endpoint receives `/v1/chat/completions`, while a full
`/chat/completions` endpoint is used as supplied.

The route's `ModelConfig` supplies the endpoint, model name, and timeout. An
optional API key can be passed to the provider or supplied through the
`OPENAI_API_KEY` environment variable. Local servers that do not require
authentication work without a key. This adapter can later connect to vLLM or
other local inference servers that expose a compatible endpoint.

## Install

```text
python -m pip install -e ".[test]"
```

## Run tests

```text
python -m pytest
```

The package deliberately has no runtime dependencies and does not yet include
RAG, agents, an API server, authentication, or deployment infrastructure. The
automated tests use mocked HTTP transport and do not require a model server.