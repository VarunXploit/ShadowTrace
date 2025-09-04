import os

# Set this environment variable before running (recommended)
# Windows PowerShell:
# $env:TWITTER_BEARER_TOKEN="your_bearer_token_here"

BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")  # preferred
# fallback: you can paste token here (not recommended for production)
# BEARER_TOKEN = "paste-your-bearer-token-here"
