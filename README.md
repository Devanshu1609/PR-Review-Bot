# PR Review Bot

An AI-powered GitHub Action that automatically reviews Pull Requests for security issues, bugs, and risky code patterns using Groq.

## Features

- Automatically triggered on Pull Requests
- AI-powered security review
- Detects potential bugs and risky patterns
- Provides recommendations
- Posts review results directly to the Pull Request
- Tracks findings between PR updates
- Identifies fixed findings
- Uses Groq for AI inference
- No Docker or local setup required for users

## Usage

Add the following workflow to your repository:

`.github/workflows/pr-review.yml`

```yaml
name: AI PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest

    steps:
      - name: Run PR Review Bot
        uses: Devanshu1609/PR-Review-Bot@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          groq_api_key: ${{ secrets.GROQ_API_KEY }}