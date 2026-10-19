"""Tests for threadloom.config."""

import os

import threadloom.config as config


def test_get_github_token() -> None:
    # Ensure we start with a clean environment
    old_val = os.environ.pop('GITHUB_TOKEN', None)
    try:
        # Should return None when not set
        assert config.get_github_token() is None
        # Set a value and check it's returned
        token = 'test-token-123'
        os.environ['GITHUB_TOKEN'] = token
        assert config.get_github_token() == token
    finally:
        # Restore environment
        if old_val is not None:
            os.environ['GITHUB_TOKEN'] = old_val
        else:
            os.environ.pop('GITHUB_TOKEN', None)


def test_get_github_api_url() -> None:
    old_val = os.environ.pop('GITHUB_API_URL', None)
    try:
        # Default value
        assert config.get_github_api_url() == 'https://api.github.com'
        # Custom value
        custom_url = 'https://example.com/api'
        os.environ['GITHUB_API_URL'] = custom_url
        assert config.get_github_api_url() == custom_url
    finally:
        if old_val is not None:
            os.environ['GITHUB_API_URL'] = old_val
        else:
            os.environ.pop('GITHUB_API_URL', None)


def test_get_github_per_page() -> None:
    old_val = os.environ.pop('GITHUB_PER_PAGE', None)
    try:
        # Default value
        assert config.get_github_per_page() == 100
        # Valid integer
        os.environ['GITHUB_PER_PAGE'] = '50'
        assert config.get_github_per_page() == 50
        # Invalid integer falls back to default
        os.environ['GITHUB_PER_PAGE'] = 'not-a-number'
        assert config.get_github_per_page() == 100
    finally:
        if old_val is not None:
            os.environ['GITHUB_PER_PAGE'] = old_val
        else:
            os.environ.pop('GITHUB_PER_PAGE', None)