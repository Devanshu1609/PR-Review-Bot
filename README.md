# PR Review Bot

This repository provides a GitHub Action that runs PR review checks and can post comments/suggestions on pull requests.

## Usage

Example workflow to run the action on pull requests:

```yaml
name: PR Review
on:
  pull_request:

jobs:
  pr-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Run PR Review Bot
        uses: Devanshu1609/PR-Review-Bot@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          config: .prbot.yml
```

## Inputs
- `github_token` (required): Token for GitHub API access, usually `${{ secrets.GITHUB_TOKEN }}`.
- `config` (optional): Path to a config file in the repository.

## Permissions
The workflow should grant the action appropriate permissions, for example `pull-requests: write` and `contents: read`.

## Development
To test locally, build the Docker image and run the entrypoint manually:

```bash
docker build -t pr-review-bot .
docker run --env GITHUB_REPOSITORY=owner/repo -e GITHUB_TOKEN="token" pr-review-bot
```

## License
MIT
