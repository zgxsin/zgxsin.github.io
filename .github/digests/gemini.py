"""Send a structured generation request to the Gemini Interactions API."""

from http.client import HTTPException
import json
import sys
from time import sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEFAULT_MODEL = "gemini-4-hydrogen"
API_KEY_ENV = "GEMINI_API_KEY"


def http_error_message(error, model, key):
    message = f"Gemini returned HTTP {error.code} for model {model}"
    try:
        with error:
            payload = json.load(error)
    except (OSError, HTTPException, ValueError):
        return message

    details = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(details, dict):
        return message

    parts = []
    for field in ("code", "message"):
        value = details.get(field)
        if isinstance(value, str):
            parts.append(" ".join(value.replace(key, "[redacted]").split()))
    explanation = ": ".join(filter(None, parts))
    return f"{message}: {explanation}" if explanation else message


def generate_json(*, model, prompt, input_data, schema, key):
    request = Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        data=json.dumps({
            "model": model,
            "system_instruction": prompt,
            "input": json.dumps(input_data, default=str),
            "generation_config": {"thinking_level": "low"},
            "response_format": {
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        }).encode(),
        headers={
            "x-goog-api-key": key,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        },
    )
    for delay in (5, 15, 30, None):
        try:
            with urlopen(request, timeout=120) as response:
                result = json.load(response)
            break
        except HTTPError as error:
            message = http_error_message(error, model, key)
            if error.code not in (500, 502, 503, 504) or delay is None:
                raise SystemExit(message) from None
            print(f"{message} (retrying in {delay} seconds)", file=sys.stderr)
            sleep(delay)
    if result.get("status") != "completed":
        raise SystemExit(f"Gemini did not complete the draft ({result.get('status', 'no status')}).")
    return json.loads("".join(
        part["text"]
        for step in result.get("steps", []) if step["type"] == "model_output"
        for part in step["content"] if part["type"] == "text"
    ))
