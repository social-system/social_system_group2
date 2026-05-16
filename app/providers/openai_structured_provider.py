from typing import Any


class OpenAIStructuredProvider:
    async def normalize_receipt(
        self,
        *,
        gemini_result: str,
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "OpenAI structured provider execution is implemented in a later milestone."
        )
