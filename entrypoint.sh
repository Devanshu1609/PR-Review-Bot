#!/bin/sh
set -e

# Arguments (in order provided by action.yml)
GITHUB_TOKEN_ARG="$1"
OPENAI_API_KEY_ARG="$2"
DOCS_TOKEN_ARG="$3"
CONFLUENCE_BASE_URL_ARG="$4"
CONFLUENCE_USERNAME_ARG="$5"
CONFLUENCE_API_TOKEN_ARG="$6"

# Export as environment variables the Python code will read
if [ -n "$GITHUB_TOKEN_ARG" ]; then
  export GITHUB_TOKEN="$GITHUB_TOKEN_ARG"
fi
if [ -n "$OPENAI_API_KEY_ARG" ]; then
  export OPENAI_API_KEY="$OPENAI_API_KEY_ARG"
fi
if [ -n "$DOCS_TOKEN_ARG" ]; then
  export DOCS_TOKEN="$DOCS_TOKEN_ARG"
fi
if [ -n "$CONFLUENCE_BASE_URL_ARG" ]; then
  export CONFLUENCE_BASE_URL="$CONFLUENCE_BASE_URL_ARG"
fi
if [ -n "$CONFLUENCE_USERNAME_ARG" ]; then
  export CONFLUENCE_USERNAME="$CONFLUENCE_USERNAME_ARG"
fi
if [ -n "$CONFLUENCE_API_TOKEN_ARG" ]; then
  export CONFLUENCE_API_TOKEN="$CONFLUENCE_API_TOKEN_ARG"
fi

# The GitHub Actions runtime mounts the event payload to /github/workflow/event.json
# but our action will primarily use the GitHub context and API. Run the python module.
python -m src
