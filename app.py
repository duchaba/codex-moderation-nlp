import os
from functools import lru_cache
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

DEFAULT_MODEL = "omni-moderation-latest"
DEFAULT_SAFER_THRESHOLD = 0.0005


class ModerationRequest(BaseModel):
    message: str = Field(..., min_length=1)
    safer: float = Field(DEFAULT_SAFER_THRESHOLD, ge=0)


class ModerationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    is_safer_flagged: bool
    is_flagged: bool
    max_key: str
    max_value: float
    sum_value: float
    safer_value: float
    message: str


app = FastAPI(title="Moderation NLP Server", version="1.0.0")


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Create and cache the OpenAI API client.

    Input parameters:
        None. The function reads the API key from the `OPENAI_API_KEY`
        environment variable. It also supports the legacy `openai_key`
        environment variable used by the original notebook code.

    Output:
        OpenAI: A configured OpenAI client instance. The result is cached so
        repeated moderation requests reuse the same client object.

    Raises:
        RuntimeError: Raised when no OpenAI API key is available in the
        environment.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("openai_key")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    return OpenAI(api_key=api_key)


def moderate_text(message: str, safer: float = DEFAULT_SAFER_THRESHOLD) -> Dict[str, object]:
    """
    Moderate a text message using the configured OpenAI moderation model.

    Input parameters:
        message: The text string to send to the moderation model.
        safer: The custom threshold used for `is_safer_flagged`. If the
            highest moderation category score is greater than or equal to this
            value, `is_safer_flagged` is set to `True`.

    Output:
        Dict[str, object]: A JSON-serializable dictionary containing all
        moderation category scores returned by OpenAI plus these summary
        fields:
            - `is_safer_flagged`: Custom threshold flag based on `safer`.
            - `is_flagged`: OpenAI's built-in moderation flag.
            - `max_key`: Category with the highest score.
            - `max_value`: Highest category score.
            - `sum_value`: Sum of all category scores.
            - `safer_value`: Threshold used for `is_safer_flagged`.
            - `message`: Original input message.

    Raises:
        RuntimeError: Raised by `get_openai_client` when no API key is set.
        Exception: Any OpenAI client or network error is allowed to bubble up
        so the API endpoint can convert it into a JSON HTTP error response.
    """
    client = get_openai_client()
    response = client.moderations.create(input=message, model=DEFAULT_MODEL)
    response_dict = response.model_dump()

    result = response_dict["results"][0]
    # Replace missing category scores with 0 so downstream math is consistent.
    category_scores = {
        key: value if value is not None else 0
        for key, value in result["category_scores"].items()
    }

    # Keep the original category scores and add custom threshold metadata.
    max_key = max(category_scores, key=category_scores.get)
    max_value = category_scores[max_key]
    sum_value = sum(category_scores.values())

    moderation_output = dict(category_scores)
    moderation_output["is_safer_flagged"] = max_value >= safer
    moderation_output["is_flagged"] = result["flagged"]
    moderation_output["max_key"] = max_key
    moderation_output["max_value"] = max_value
    moderation_output["sum_value"] = sum_value
    moderation_output["safer_value"] = safer
    moderation_output["message"] = message
    return moderation_output


@app.get("/health")
def health() -> Dict[str, str]:
    """
    Return a simple health check response for server monitoring.

    Input parameters:
        None.

    Output:
        Dict[str, str]: A JSON response with `status` set to `ok`.
    """
    return {"status": "ok"}


@app.post("/moderate", response_model=ModerationResponse)
def moderate(request: ModerationRequest) -> Dict[str, object]:
    """
    Handle JSON moderation requests from API clients.

    Input parameters:
        request: A `ModerationRequest` object parsed from the JSON request
            body. It contains:
            - `message`: Required text to moderate.
            - `safer`: Optional custom threshold for `is_safer_flagged`.

    Output:
        Dict[str, object]: A JSON-serializable moderation result from
        `moderate_text`. The response includes category scores and summary
        fields defined by `ModerationResponse`.

    Raises:
        HTTPException: Returns HTTP 500 when the API key is missing and HTTP
        502 when the OpenAI moderation request fails.
    """
    try:
        return moderate_text(request.message, request.safer)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Moderation request failed: {exc}") from exc
