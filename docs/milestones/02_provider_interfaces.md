# Milestone 02: Provider Interfaces

## 目的

Gemini provider と OpenAI Structured Outputs provider のインターフェースを定義する。

この段階では、実 API 呼び出しは最小実装または未実装でもよい。重要なのは、service から provider を差し替えられる設計にすることである。

## 実装対象

- `app/providers/gemini_provider.py`
- `app/providers/openai_structured_provider.py`
- provider 用例外
- fake provider を使った service テストの土台

## GeminiProvider

インターフェース例:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class GeminiExtractionResult:
    text: str

class GeminiProvider:
    async def extract_receipt_text(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
    ) -> GeminiExtractionResult:
        ...
```

## OpenAIStructuredProvider

インターフェース例:

```python
class OpenAIStructuredProvider:
    async def structure_receipt(
        self,
        *,
        gemini_text: str,
    ) -> dict:
        ...
```

## 例外

次の例外を定義する。

```python
class ExternalProviderError(Exception):
    pass

class GeminiProviderError(ExternalProviderError):
    pass

class OpenAIProviderError(ExternalProviderError):
    pass

class StructuredOutputError(Exception):
    pass
```

## 実装ルール

- provider は API キーを settings から受け取る。
- provider の import 時に外部 API 接続をしない。
- provider は FastAPI の `HTTPException` を投げない。
- provider の失敗は app 内例外として投げる。
- テストで fake provider に差し替えられるようにする。

## テスト

このマイルストーンでは、外部 API 実接続テストは不要。

追加するテスト:

- fake Gemini provider が期待値を返す
- fake OpenAI provider が期待 dict を返す
- provider の例外を service で扱える準備がある

## 完了条件

```bash
uv run python -m compileall app
uv run pytest
```

## 非対象

- 本物の Gemini API 呼び出し
- 本物の OpenAI API 呼び出し
- route の完成
