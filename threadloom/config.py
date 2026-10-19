"""Configuration module for Threadloom.

Loads GitHub token and other settings from environment variables.
"""

import os


def get_github_token() -> str | None:
    """Get GitHub token from environment variable.

    Returns the token from GITHUB_TOKEN environment variable,
    or None if not set.
    """
    return os.environ.get('GITHUB_TOKEN')


def get_github_api_url() -> str:
    """Get GitHub API URL from environment variable.

    Returns the URL from GITHUB_API_URL environment variable,
    or defaults to 'https://api.github.com'.
    """
    return os.environ.get('GITHUB_API_URL', 'https://api.github.com')


def get_github_per_page() -> int:
    """Get number of items per page for GitHub API.

    Returns the value from GITHUB_PER_PAGE environment variable,
    or defaults to 100.
    """
    try:
        return int(os.environ.get('GITHUB_PER_PAGE', '100'))
    except ValueError:
        return 100