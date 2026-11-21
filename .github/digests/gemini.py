"""Send a structured generation request to the Gemini Interactions API."""

from http.client import HTTPException
import json
import sys
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL = "gemini-4-hydrogen"
FALLBACK_MODELS = ("gemini-3.8-flash", "gemini-3.1-flash-lite")
API_KEY_ENV = "GEMINI_API_KEY"
RETRYABLE_HTTP_CODES = (500, 502, 503, 504)
REQUEST_TIMEOUT = 120


class GeminiRequestError(Exception):
    def __init__(self, message, *, can_fallback):
        super().__init__(message)
        self.can_fallback = can_fallback


class GeminiClient:
    def __init__(self, model, key):
        self.model = model
        self.models = tuple(dict.fromkeys((model, *FALLBACK_MODELS)))
        self.key = key

    def generate_json(self, *, prompt, input_data, schema):
        models = self.models[self.models.index(self.model):]
        for index, model in enumerate(models):
            try:
                result = _generate_json(model=model, prompt=prompt, input_data=input_data, schema=schema, key=self.key)
            except GeminiRequestError as error:
                if not error.can_fallback or index == len(models) - 1:
                    raise SystemExit(str(error)) from None
                print(f"{error} (trying backup model {models[index + 1]})", file=sys.stderr)
                continue
            self.model = model
            return result


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


def _generate_json(*, model, prompt, input_data, schema, key):
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
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                result = json.load(response)
            break
        except HTTPError as error:
            message = http_error_message(error, model, key)
            if error.code not in RETRYABLE_HTTP_CODES or delay is None:
                raise GeminiRequestError(
                    message, can_fallback=error.code in (*RETRYABLE_HTTP_CODES, 429),
                ) from None
            print(f"{message} (retrying in {delay} seconds)", file=sys.stderr)
            sleep(delay)
        except (TimeoutError, URLError) as error:
            if isinstance(error, URLError) and not isinstance(error.reason, TimeoutError):
                raise
            raise GeminiRequestError(
                f"Gemini request timed out for model {model} (socket timeout: {REQUEST_TIMEOUT} seconds)",
                can_fallback=True,
            ) from None
    if result.get("status") != "completed":
        raise SystemExit(f"Gemini did not complete the draft ({result.get('status', 'no status')}).")
    return json.loads("".join(
        part["text"]
        for step in result.get("steps", []) if step["type"] == "model_output"
        for part in step["content"] if part["type"] == "text"
    ))
