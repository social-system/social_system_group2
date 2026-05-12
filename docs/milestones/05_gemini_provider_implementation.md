# Milestone 05: Gemini Provider Implementation

## Goal

Implement the real Gemini provider behind the existing interface.

This milestone must still keep tests mocked and must not require live API keys.

## Scope

Implement:

- Real Gemini provider class
- Prompt construction for receipt image reading
- Configuration key check at provider execution time
- Unit tests using mocks, not real API calls

## Provider responsibility

The provider receives:

- image bytes
- MIME type

It returns:

- intermediate text or JSON-like receipt extraction string

## Required prompt behavior

The Gemini prompt should ask for visible receipt information:

- Store name
- Purchase date
- Total amount
- Item rows
- Quantities and units when visible
- Unit price and line total when visible
- Warnings for unclear lines

Gemini output is not final. It will be normalized by OpenAI Structured Outputs.

## Missing API key rule

If `GEMINI_API_KEY` is missing during real provider execution, raise `ProviderConfigurationError`.

Do not expose key names or environment contents in public route responses.

## Secret rule

Do not print or log `GEMINI_API_KEY`.
Do not run live provider tests in Codex.

## Required tests

Use SDK/client mocks.

- Provider builds a request using image bytes and MIME type
- Provider returns text from mocked Gemini response
- Missing API key raises configuration error
- SDK failure raises provider execution error

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```

## Manual verification

If live verification is needed, provide commands for the human developer only.
Do not run them.
