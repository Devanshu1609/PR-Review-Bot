"""LLM call wrapper using Groq only."""

import os
import re
from typing import List, Dict

import httpx


def redact(text: str) -> str:
    """Mask long alphanumeric sequences that may be API keys/tokens."""
    return re.sub(r"[A-Za-z0-9_]{40,}", "[REDACTED]", text)


def call_llm(
    parsed_diff: List[Dict],
    security_findings: List[Dict],
    deps: List[Dict],
    pr_meta: Dict,
) -> List[Dict]:

    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        return (
            [
                {
                    "file": parsed_diff[0]["path"],
                    "issue": "stubbed-issue",
                    "severity": "low",
                }
            ]
            if parsed_diff
            else []
        )

    prompt = "Analyze the following changes for security issues:\n"

    for f in parsed_diff[:10]:
        prompt += f"File: {f['path']}\n"

        for h in f.get("hunks", [])[:3]:
            for line in h.get("lines", [])[:10]:
                prompt += redact(line) + "\n"

    prompt += "\nAlso consider static findings:\n"

    for s in security_findings[:10]:
        prompt += f"- {s}\n"

    if deps:
        prompt += "\nDependencies:\n"

        for dep in deps[:20]:
            prompt += f"- {dep}\n"

    if pr_meta:
        prompt += "\nPull Request metadata:\n"

        for key, value in pr_meta.items():
            prompt += f"- {key}: {value}\n"


    groq_api_url = os.getenv(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1",
    )

    groq_model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    url = f"{groq_api_url.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": groq_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior software security auditor. "
                    "Review pull request changes carefully and identify "
                    "security vulnerabilities, bugs, risky patterns, "
                    "and recommended fixes."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    try:
        print(f"[LLM] Using Groq model: {groq_model}")
        print(f"[LLM] Groq endpoint: {url}")

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                url,
                headers=headers,
                json=body,
            )

        resp.raise_for_status()

        data = resp.json()

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(
                f"Unexpected Groq response format: {data}"
            ) from e

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code

        try:
            error_body = e.response.json()
        except Exception:
            error_body = e.response.text

        raise RuntimeError(
            f"Groq API returned HTTP {status_code}: {error_body}"
        ) from e

    except httpx.ConnectError as e:
        raise RuntimeError(
            "Could not connect to Groq API. "
            "Check your internet connection, DNS, proxy/VPN, "
            f"and GROQ_API_URL. Current URL: {url}. "
            f"Original error: {e}"
        ) from e

    except httpx.TimeoutException as e:
        raise RuntimeError(
            f"Groq API request timed out: {e}"
        ) from e

    except Exception as e:
        raise RuntimeError(
            f"Groq request failed: {e}"
        ) from e

    return [
        {
            "file": "(multiple)",
            "issue": text,
            "severity": "info",
        }
    ]