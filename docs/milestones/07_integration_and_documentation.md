# Milestone 07: Integration and Documentation

## Goal

Finalize integration wiring, documentation, and manual verification instructions.

Do not run live provider calls in Codex.

## Scope

Implement or update:

- Provider dependency wiring
- README
- Error handling documentation alignment
- Manual live verification section
- Final integration tests with mocked providers

## Required behavior

The app must:

- Start without API keys
- Pass tests without API keys
- Use fake providers in tests
- Return stable errors
- Use OS environment variables only for configuration

## README requirements

README must include:

- Project overview
- Explicit statement that DB registration is not performed
- Setup command
- Development server command
- Health check example
- Receipt extraction curl example
- Test command
- Environment variable policy
- Human-only live provider verification instructions

## Environment variable policy text

Include this idea clearly:

```text
For live manual testing, pass API keys through OS environment variables for the current shell or current command only.
Do not commit API keys or store them in project files.
```

## Final tests

- All tests pass
- No test requires API keys
- No test uses real provider calls
- Compileall passes

## Completion commands

```bash
uv run python -m compileall app
uv run pytest
```

## Completion report

Report:

- Changed files
- Added APIs
- Provider integration status
- Commands executed
- Test results
- Manual verification steps
- Remaining TODOs
