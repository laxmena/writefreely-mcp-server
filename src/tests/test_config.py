"""
Tests for configuration module.
"""

import pytest
import os
from unittest.mock import patch

from writefreely_mcp_server.config import (
    get_base_url,
    get_access_token,
    BASE_URL,
    WRITEAS_URL,
    READ_WRITEAS_URL,
    REQUEST_TIMEOUT,
    DEFAULT_LANGUAGE,
)


class TestGetBaseUrl:
    """Tests for get_base_url function."""

    def test_get_base_url_default(self):
        """Test getting default base URL."""
        url = get_base_url()
        assert url == BASE_URL
        assert url in [WRITEAS_URL, os.getenv("WRITEFREELY_BASE_URL", WRITEAS_URL)]

    @pytest.mark.parametrize(
        "env_value", ["https://custom.writefreely.com", "http://localhost:8080"]
    )
    def test_get_base_url_from_env(self, env_value):
        """Test getting base URL from environment variable."""
        with patch.dict(os.environ, {"WRITEFREELY_BASE_URL": env_value}):
            # Re-import to get updated value
            from importlib import reload
            from writefreely_mcp_server import config

            reload(config)
            url = config.get_base_url()
            assert url == env_value


class TestGetAccessToken:
    """Tests for get_access_token function."""

    def test_get_access_token_from_parameter(self):
        """Test getting access token from provided parameter."""
        token = get_access_token("provided_token_123")
        assert token == "provided_token_123"

    def test_get_access_token_from_env(self):
        """Test getting access token from environment variable."""
        with patch.dict(os.environ, {"WRITEFREELY_ACCESS_TOKEN": "env_token_456"}):
            token = get_access_token()
            assert token == "env_token_456"

    def test_get_access_token_parameter_overrides_env(self):
        """Test that provided parameter overrides environment variable."""
        with patch.dict(os.environ, {"WRITEFREELY_ACCESS_TOKEN": "env_token"}):
            token = get_access_token("param_token")
            assert token == "param_token"

    def test_get_access_token_none(self):
        """Test getting access token when none is available."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure WRITEFREELY_ACCESS_TOKEN is not set
            if "WRITEFREELY_ACCESS_TOKEN" in os.environ:
                del os.environ["WRITEFREELY_ACCESS_TOKEN"]
            token = get_access_token()
            assert token is None


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_base_url_default(self):
        """Test BASE_URL default value."""
        assert BASE_URL == os.getenv("WRITEFREELY_BASE_URL", WRITEAS_URL)

    def test_writeas_url(self):
        """Test WRITEAS_URL constant."""
        assert WRITEAS_URL == "https://write.as"

    def test_read_writeas_url(self):
        """Test READ_WRITEAS_URL constant."""
        assert READ_WRITEAS_URL == "https://read.write.as"

    def test_request_timeout(self):
        """Test REQUEST_TIMEOUT constant."""
        assert REQUEST_TIMEOUT == 30.0
        assert isinstance(REQUEST_TIMEOUT, float)

    def test_default_language(self):
        """Test DEFAULT_LANGUAGE constant."""
        assert DEFAULT_LANGUAGE == os.getenv("WRITEFREELY_DEFAULT_LANGUAGE", "en")
