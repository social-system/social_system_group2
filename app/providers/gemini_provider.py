class GeminiProvider:
    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        filename: str | None = None,
    ) -> str:
        raise NotImplementedError(
            "Gemini provider execution is implemented in a later milestone."
        )
