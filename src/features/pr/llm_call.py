"""LLM call wrapper.

Supports:
- Groq via the OpenAI-compatible REST API using httpx
- OpenAI via the openai package as a fallback
- Offline stub mode when no API key is configured
"""

import os
import re
from typing import List, Dict

import httpx

try:
    import openai
except Exception:
    openai = None


def redact(text: str) -> str:
    """Mask long alphanumeric sequences that may be API keys/tokens."""
    return re.sub(r"[A-Za-z0-9_]{40,}", "[REDACTED]", text)


def call_llm(
    parsed_diff: List[Dict],
    security_findings: List[Dict],
    deps: List[Dict],
    pr_meta: Dict,
) -> List[Dict]:

    # ------------------------------------------------------------------
    # Read configuration
    # ------------------------------------------------------------------

    api_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "").lower()

    # ------------------------------------------------------------------
    # Offline mode
    # ------------------------------------------------------------------

    if not api_key and not groq_key:
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

    # ------------------------------------------------------------------
    # Build prompt
    # ------------------------------------------------------------------

    prompt = "Analyze the following changes for security issues:\n"

    for f in parsed_diff[:10]:
        prompt += f"File: {f['path']}\n"

        for h in f.get("hunks", [])[:3]:
            for line in h.get("lines", [])[:10]:
                prompt += redact(line) + "\n"

    prompt += "\nAlso consider static findings:\n"

    for s in security_findings[:10]:
        prompt += f"- {s}\n"

    # Include dependency information if available
    if deps:
        prompt += "\nDependencies:\n"

        for dep in deps[:20]:
            prompt += f"- {dep}\n"

    # Include PR metadata if available
    if pr_meta:
        prompt += "\nPull Request metadata:\n"

        for key, value in pr_meta.items():
            prompt += f"- {key}: {value}\n"

    # ------------------------------------------------------------------
    # Groq
    # ------------------------------------------------------------------

    # Use Groq when:
    # 1. LLM_PROVIDER=groq
    # OR
    # 2. GROQ_API_KEY exists
    use_groq = (
        provider == "groq"
        or (groq_key is not None and groq_key != "")
    )

    if use_groq:

        if not groq_key:
            raise RuntimeError(
                "LLM_PROVIDER is set to 'groq', but GROQ_API_KEY is missing."
            )

        # Groq's OpenAI-compatible API endpoint
        groq_api_url = os.getenv(
            "GROQ_API_URL",
            "https://api.groq.com/openai/v1",
        )

        # Default Groq model
        groq_model = os.getenv(
            "GROQ_MODEL",
            "llama-3.3-70b-versatile",
        )

        # Chat Completions endpoint
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

            # Raise an exception for HTTP 4xx/5xx responses
            resp.raise_for_status()

            # Parse JSON response
            data = resp.json()

            # Groq's OpenAI-compatible response format:
            #
            # {
            #   "choices": [
            #       {
            #           "message": {
            #               "content": "..."
            #           }
            #       }
            #   ]
            # }
            try:
                text = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                raise RuntimeError(
                    f"Unexpected Groq response format: {data}"
                ) from e

        except httpx.HTTPStatusError as e:
            # Useful errors for:
            # 401 -> invalid API key
            # 404 -> wrong endpoint/model
            # 429 -> rate limit
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

    # ------------------------------------------------------------------
    # OpenAI fallback
    # ------------------------------------------------------------------

    if openai is None:
        raise RuntimeError(
            "openai package is not installed and Groq is not configured."
        )

    if not api_key:
        raise RuntimeError(
            "No OPENAI_API_KEY or GROQ_API_KEY was provided."
        )

    try:
        openai.api_key = api_key

        resp = openai.ChatCompletion.create(
            model=os.getenv(
                "REVIEW_MODEL",
                "gpt-4o-mini",
            ),
            messages=[
                {
                    "role": "system",
                    "content": "You are a security auditor.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=800,
        )

        text = resp["choices"][0]["message"]["content"]

    except Exception as e:
        raise RuntimeError(
            f"OpenAI request failed: {e}"
        ) from e

    return [
        {
            "file": "(multiple)",
            "issue": text,
            "severity": "info",
        }
    ]