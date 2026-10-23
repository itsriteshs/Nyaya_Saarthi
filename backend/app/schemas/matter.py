from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Language = Literal["auto", "english", "hindi", "hinglish"]
Stage = Literal["DRAFT", "UNDERSTANDING", "NEEDS_CLARIFICATION", "READY_FOR_REVIEW", "USER_VERIFIED", "GUIDANCE_GENERATED", "COMPLETED"]
Provenance = Literal["USER_PROVIDED", "USER_CONFIRMED", "SYSTEM_INFERRED", "UNKNOWN"]

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Intent(StrictModel):
    label: str = ""
    descriptor: str = ""

class Fact(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=200)
    value: str = Field(max_length=10000)
    state: Literal["provided", "confirmed", "inferred", "unknown"]
    provenance: Provenance
    confirmed: bool
    requiresConfirmation: bool | None = None
    normalizedValue: str | None = None
    normalizedId: str | None = None
    sourceMessageId: str | None = None
    extractionMethod: str | None = None
    sourceText: str | None = None
    interpretationNotes: list[str] = Field(default_factory=list)
    unitSource: str | None = None
    unit: str | None = None
    approximate: bool | None = None
    uncertainty: str | None = None
    resolutionStatus: Literal["resolved", "ambiguous", "unresolved"] | None = None
    updatedAt: datetime | None = None

class Readiness(StrictModel):
    found: int = Field(ge=0)
    total: int = Field(ge=0)

    @model_validator(mode="after")
    def valid_count(self):
        if self.found > self.total:
            raise ValueError("found cannot exceed total")
        return self

class Message(StrictModel):
    id: str = Field(min_length=1, max_length=100)
    speaker: Literal["user", "assistant"]
    text: str = Field(max_length=20000)

class QuestionOption(StrictModel):
    label: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=200)

class Question(StrictModel):
    id: str | None = None
    slot: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=2000)
    type: Literal["options", "text"]
    options: list[QuestionOption] | None = None
    why: str = Field(max_length=2000)

class LegalSource(StrictModel):
    id: str
    title: str
    authority: str
    provision: str | None = None
    relevantPoint: str
    sourceType: Literal["Act", "Rules", "Notification", "Guidance"]
    sourceUrl: str | None = None
    evidenceId: str | None = None
    reviewStatus: str | None = None
    admissibility: str | None = None

class Mapping(StrictModel):
    id: str
    fact: str
    sourceId: str
    sourceTitle: str
    explanation: str
    evidenceId: str | None = None

class NextStep(StrictModel):
    id: str
    tag: Literal["Verify", "Check", "Keep", "Respond"]
    title: str
    description: str
    evidenceId: str | None = None

class Guidance(StrictModel):
    generatedAt: str
    directAnswer: str
    qualification: str
    sources: list[LegalSource]
    mappings: list[Mapping]
    uncertainties: list[str]
    nextSteps: list[NextStep]
    suggestedQuestions: list[str]
    metadata: dict[str, Any] | None = None

class MatterCreate(StrictModel):
    originalText: str = Field(min_length=1, max_length=20000)
    language: Language

    @field_validator("originalText")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("originalText must not be blank")
        return value.strip()

class MatterPatch(StrictModel):
    revision: int = Field(ge=1)
    intent: Intent | None = None
    facts: list[Fact] | None = None
    missingSlots: list[str] | None = None
    contextReadiness: Readiness | None = None
    stage: Stage | None = None
    verifiedAt: datetime | None = None
    guidance: Guidance | None = None
    answers: dict[str, str] | None = None
    currentQuestion: Question | None = None
    messages: list[Message] | None = None

    @model_validator(mode="after")
    def has_update(self):
        if not (self.model_fields_set - {"revision"}):
            raise ValueError("At least one field must be updated")
        for field in ("intent", "facts", "missingSlots", "contextReadiness", "stage", "answers", "messages"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self

class MatterResponse(StrictModel):
    id: str
    originalText: str
    language: Language
    intent: Intent
    facts: list[Fact]
    missingSlots: list[str]
    contextReadiness: Readiness
    stage: Stage
    createdAt: datetime
    updatedAt: datetime
    verifiedAt: datetime | None = None
    guidance: Guidance | None = None
    generationHistory: list[dict[str, Any]] = []
    answers: dict[str, str]
    currentQuestion: Question | None = None
    messages: list[Message]
    nlpAnalysis: dict[str, Any] | None = None
    conversation: dict[str, Any] | None = None
    schemaVersion: int
    revision: int
