from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modelId: Literal["llama3.2-3b", "mistral-7b", "deterministic"]
    language: Literal["english", "hindi", "hinglish"]
    expectedRevision: int = Field(ge=1)
    regenerate: bool = False


class LegalClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=1000)
    evidenceIds: list[str] = Field(min_length=1)


class Explanation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=3000)
    explanation: str = Field(min_length=1, max_length=4000)
    legalClaims: list[LegalClaim]
    uncertainties: list[str]
    recommendedActions: list[str]
    language: Literal["english", "hindi", "hinglish"]
    requiresHumanHelp: bool
