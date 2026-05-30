"""Tests for deepseek_client — LLM call wrapper for Scanner v2."""

import json
import os
from unittest.mock import patch, MagicMock

from harness_builder.scanner.deepseek_client import DeepSeekConfig, call_deepseek


class TestDeepSeekConfig:
    """Config dataclass defaults and env-var fallback."""

    def test_config_defaults(self):
        """DeepSeekConfig has sensible defaults for base_url, model, max_tokens, temperature, timeout."""
        cfg = DeepSeekConfig(api_key="test-key")
        assert cfg.api_key == "test-key"
        assert cfg.base_url == "https://api.deepseek.com"
        assert cfg.model == "deepseek-v4-flash"
        assert cfg.max_tokens == 4096
        assert cfg.temperature == 0.0
        assert cfg.timeout == 60

    def test_config_from_env(self):
        """DeepSeekConfig.from_env() reads DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL."""
        env = {
            "DEEPSEEK_API_KEY": "env-key-123",
            "DEEPSEEK_BASE_URL": "https://custom.api.com",
            "DEEPSEEK_MODEL": "deepseek-custom",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = DeepSeekConfig.from_env()
        assert cfg.api_key == "env-key-123"
        assert cfg.base_url == "https://custom.api.com"
        assert cfg.model == "deepseek-custom"


class TestCallDeepseek:
    """call_deepseek request building and error handling."""

    def test_builds_correct_request(self):
        """Sends proper JSON body to /chat/completions with model and messages."""
        cfg = DeepSeekConfig(api_key="key-abc")
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Hello from DeepSeek"}}]
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        captured_req = {}

        def fake_urlopen(req, timeout=None):
            captured_req["req"] = req
            captured_req["timeout"] = timeout
            return mock_response

        with patch("harness_builder.scanner.deepseek_client.urlopen", fake_urlopen):
            result = call_deepseek("What is 1+1?", config=cfg)

        assert result == "Hello from DeepSeek"
        req = captured_req["req"]
        assert req.full_url == "https://api.deepseek.com/chat/completions"
        body = json.loads(req.data.decode())
        assert body["model"] == "deepseek-v4-flash"
        assert body["messages"][-1]["role"] == "user"
        assert body["messages"][-1]["content"] == "What is 1+1?"
        assert captured_req["timeout"] == 60

    def test_with_system_prompt(self):
        """When system_prompt is provided, it appears as the first message."""
        cfg = DeepSeekConfig(api_key="key-sys")
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "System reply"}}]
        }).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        captured_req = {}

        def fake_urlopen(req, timeout=None):
            captured_req["req"] = req
            return mock_response

        with patch("harness_builder.scanner.deepseek_client.urlopen", fake_urlopen):
            result = call_deepseek("Analyze this", system_prompt="You are a code analyst.", config=cfg)

        body = json.loads(captured_req["req"].data.decode())
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][0]["content"] == "You are a code analyst."
        assert body["messages"][1]["role"] == "user"
        assert result == "System reply"

    def test_timeout_returns_none(self):
        """Timeout or other exception returns None, never raises."""
        cfg = DeepSeekConfig(api_key="key-err")
        with patch("harness_builder.scanner.deepseek_client.urlopen", side_effect=TimeoutError("timed out")):
            result = call_deepseek("hello", config=cfg)
        assert result is None

    def test_no_api_key_returns_none(self):
        """Missing API key returns None without making a network call."""
        cfg = DeepSeekConfig(api_key="")
        with patch("harness_builder.scanner.deepseek_client.urlopen", side_effect=AssertionError("should not be called")):
            result = call_deepseek("hello", config=cfg)
        assert result is None
