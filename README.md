# PR Review Bot

> AI-powered GitHub Action for automated Pull Request security and code reviews using Groq.

PR Review Bot automatically analyzes Pull Requests and posts an AI-generated review directly to the PR. It combines deterministic security checks with an LLM-powered review to identify potential security vulnerabilities, bugs, risky patterns, and areas that may require attention.

## ✨ Features

- 🤖 AI-powered PR reviews using Groq
- 🔐 Security analysis of changed code
- 🐛 Bug detection and potential issue identification
- ⚠️ Risky pattern detection
- 💡 Actionable recommendations
- 💬 Automatic PR comments
- 🔄 Tracks findings across PR updates
- ✅ Detects fixed findings
- ⚡ No Docker, Python, or local setup required for users
- 🔑 Secure API key handling via GitHub Secrets

---

## 🚀 Quick start

Add this workflow to your repository at `.github/workflows/pr-review.yml`:

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
```

The Action runs automatically whenever a Pull Request is opened, updated, or reopened.

### Configure the Groq API key

Add your Groq API key as a repository secret (Repository → Settings → Secrets and variables → Actions → New repository secret):

- Name: `GROQ_API_KEY`
- Value: `<your Groq API key>`

Security note: Never hardcode secrets in workflow files, source code, or commit history. Always use GitHub Actions Secrets.

### Required permissions

The workflow requires the following permissions to operate:

```yaml
permissions:
  contents: read
  pull-requests: write
```

These allow the Action to read PR information and changed files, analyze the changes, and post or update the review comment.

---

## 🔎 What it reviews

PR Review Bot inspects the changes introduced by a Pull Request and looks for:

Security
- Potential security vulnerabilities
- Unsafe coding patterns
- Risky operations and vulnerability-prone changes

Code quality & correctness
- Potential bugs and incorrect logic
- Error-prone implementations
- Problematic or suspicious changes

Recommendations
- Suggested improvements and refactorings
- Security recommendations and remediation guidance
- Explanations and actionable next steps for developers

---

## 💬 Example review

When the Action posts a review comment it includes a summary and the detailed findings. Example:

> 🤖 AI PR Review
>
> Found 1 active finding and 0 fixed issues.
>
> Findings
>
> (multiple) — info
>
> Security Review
>
> After analyzing the provided changes, I have identified the following:
>
> File Changes
>
> • Changes were made to README.md
> • The added content does not introduce security risks.
>
> Security Findings
>
> • No security vulnerabilities were found.
> • No bugs were identified.
> • No risky patterns were detected.
>
> Recommendations
>
> • No additional security measures are required.

The review is updated automatically on subsequent PR updates.

---

## 🔄 Finding tracking

The Action tracks findings across PR updates. For example:

1. Initial review: 3 findings detected
2. Developer fixes 2 findings and pushes changes
3. PR updated: 1 active finding, 2 fixed findings

This lets the Action distinguish between active findings (still present) and fixed findings (previously reported and now resolved). The state is stored in the PR review comment.

---

## ⚙️ Configuration

You can optionally provide a `.mifoshawk.yml` configuration file in the repository root. To use a custom path, pass the `config` input to the Action:

```yaml
- name: Run PR Review Bot
  uses: Devanshu1609/PR-Review-Bot@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    groq_api_key: ${{ secrets.GROQ_API_KEY }}
    config: ".mifoshawk.yml"
```

If no path is provided, the Action will look for `.mifoshawk.yml` at the repository root.

---

## 🧠 How it works

Pull Request → GitHub Actions → PR Review Bot

The bot combines deterministic security checks with LLM-powered analysis. It performs security analysis and collects PR contextual information (diffs, surrounding code, metadata), sends the combined context to the Groq LLM for review generation, compares new findings with previously reported ones, and posts or updates a PR comment.

---

## 🏗 Architecture

```
src/
├── features/
│   ├── pr/
│   │   ├── cve_detection.py
│   │   ├── compare_state.py
│   │   ├── git_diff.py
│   │   ├── handler.py
│   │   ├── llm_call.py
│   │   ├── octokit.py
│   │   └── security_engine.py
│   └── push/

├── index.py
└── __main__.py
```

Main flow: GitHub event → PR handler → Diff parsing → Security checks → Groq AI review → Finding comparison → PR comment

---

## 🛠 Local development

The Python application can be tested locally if you want to run or debug the logic outside Actions.

Clone the repo, create a virtual environment, and install dependencies:

```bash
git clone https://github.com/Devanshu1609/PR-Review-Bot.git
cd PR-Review-Bot
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Set the following environment variables for local testing:

- `GITHUB_TOKEN`
- `GROQ_API_KEY`
- `GITHUB_REPOSITORY`
- `GITHUB_EVENT_NAME`
- `GITHUB_EVENT_PATH`

Run the application:

```bash
python -m src
```

---

## 📦 Versions

Use the major-tagged release to receive non-breaking updates:

```yaml
uses: Devanshu1609/PR-Review-Bot@v1
```

Or pin to a specific release for reproducible behavior:

```yaml
uses: Devanshu1609/PR-Review-Bot@v1.0.0
```

---

## 🤝 Contributing

Contributions and bug reports are welcome. To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Open a Pull Request with a clear description of the changes and their purpose

---

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for details.
