# Milestone 06: OpenAI Structured Outputs Implementation

## Goal

Implement the real OpenAI Structured Outputs provider behind the existing interface.

Tests must mock the OpenAI client.
Do not require live API keys.

## Scope

Implement:

- Real OpenAI provider class
- Strict JSON schema generation or inline schema
- Configuration key check at provider execution time
- Unit tests using mocks

## Provider responsibility

The provider receives Gemini's intermediate extraction.
It returns strict JSON matching `ReceiptOcrResponse`.

## Structured Outputs rules

The schema must follow `docs/STRUCTURED_OUTPUT_SCHEMA.md`.

Required constraints:

- Strict structured output behavior
- All fields required
- Optional values represented with `null`
- `additionalProperties: false` for every object
- No unknown keys

## Missing API key rule

If `OPENAI_API_KEY` is missing during real provider execution, raise `ProviderConfigurationError`.

Do not expose key values.

## Required tests

Use OpenAI client mocks.

- Provider sends schema-constrained request
- Provider returns dict matching expected shape
- Missing API key raises configuration error
- SDK failure raises provider execution error
- Invalid provider output raises invalid response error or validation error

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```

## Manual verification

If live verification is needed, provide commands for the human developer only.
Do not run them.
