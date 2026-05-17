from app.config import Settings


def test_default_openai_model_is_current_responses_structured_outputs_model() -> None:
    assert Settings.model_fields["openai_model"].default == "gpt-5.4-mini"
