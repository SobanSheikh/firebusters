from app.core.config import Settings


def test_groq_defaults_to_openai_compatible_endpoint() -> None:
    settings = Settings(_env_file=None, groq_api_key="groq-test-key")

    assert settings.ai_provider == "groq"
    assert settings.ai_model == "llama-3.3-70b-versatile"
    assert settings.ai_api_key == "groq-test-key"
    assert settings.resolved_ai_base_url == "https://api.groq.com/openai/v1"


def test_provider_and_endpoint_can_be_switched_with_configuration() -> None:
    settings = Settings(
        _env_file=None,
        ai_provider="openai",
        ai_model="example-model",
        ai_base_url="https://llm-gateway.example/v1",
        openai_api_key="openai-test-key",
    )

    assert settings.ai_provider == "openai"
    assert settings.ai_model == "example-model"
    assert settings.ai_api_key == "openai-test-key"
    assert settings.resolved_ai_base_url == "https://llm-gateway.example/v1"


def test_gemini_uses_its_openai_compatible_endpoint() -> None:
    settings = Settings(
        _env_file=None,
        ai_provider="gemini",
        ai_model="gemini-3.8-flash",
        gemini_api_key="gemini-test-key",
    )

    assert settings.ai_api_key == "gemini-test-key"
    assert settings.resolved_ai_base_url == (
        "https://generativelanguage.googleapis.com/v1beta/openai/"
    )
