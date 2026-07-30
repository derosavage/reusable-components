from services.llm_service.strategies import LLMOrchestrator, OpenRouterStrategy


class TestLLM:
    def test_model_registry(self):
        models = LLMOrchestrator._models
        assert "openai/gpt-4o" in models
        assert "anthropic/claude-3.5-sonnet" in models
        assert "google/gemini-2.0-flash" in models
        assert "deepseek/deepseek-chat" in models

    def test_get_default_model(self):
        assert isinstance(LLMOrchestrator.get(), OpenRouterStrategy)

    def test_get_specific_model(self):
        assert isinstance(LLMOrchestrator.get("anthropic/claude-3.5-sonnet"), OpenRouterStrategy)

    def test_get_fallback(self):
        assert isinstance(LLMOrchestrator.get("nonexistent/model"), OpenRouterStrategy)
