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
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("openai_key")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    return OpenAI(api_key=api_key)


def moderate_text(message: str, safer: float = DEFAULT_SAFER_THRESHOLD) -> Dict[str, object]:
    client = get_openai_client()
    response = client.moderations.create(input=message, model=DEFAULT_MODEL)
    response_dict = response.model_dump()

    result = response_dict["results"][0]
    category_scores = {
        key: value if value is not None else 0
        for key, value in result["category_scores"].items()
    }

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
    return {"status": "ok"}


@app.post("/moderate", response_model=ModerationResponse)
def moderate(request: ModerationRequest) -> Dict[str, object]:
    try:
        return moderate_text(request.message, request.safer)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Moderation request failed: {exc}") from exc
