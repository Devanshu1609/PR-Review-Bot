import sys
import os
import json
import requests

# Simple example entrypoint for PR Review Bot
# Replace this with your real implementation.

def main():
    github_token = sys.argv[1] if len(sys.argv) > 1 else None
    config_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"github_token provided: {bool(github_token)}")
    print(f"config_path: {config_path}")

    # Example: read config file
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                cfg = f.read()
            print("Loaded config (truncated):", cfg[:500])
        except Exception as e:
            print("Failed to read config:", e)

    # Example: call GitHub API to list PRs (repository context supplied by GitHub Actions env)
    repo = os.getenv('GITHUB_REPOSITORY')
    if repo and github_token:
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github+json'
        }
        api = f'https://api.github.com/repos/{repo}/pulls'
        resp = requests.get(api, headers=headers)
        print('PRs status code:', resp.status_code)
        try:
            prs = resp.json()
            print('Found PRs (count):', len(prs))
        except Exception as e:
            print('Failed to parse PRs json:', e)
    else:
        print('GITHUB_REPOSITORY or token not set; skipping API call')

if __name__ == '__main__':
    main()
