from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.matter import Language

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class AnalyzeRequest(Strict):
    text: str=Field(min_length=1,max_length=20000)
    language: Language='auto'
    referenceDatetime: datetime | None=None
    @field_validator('text')
    @classmethod
    def nonblank(cls,value):
        if not value.strip():raise ValueError('Text must not be blank')
        return value

class MatterAnalyzeRequest(Strict):
    revision: int=Field(ge=1)
    referenceDatetime: datetime | None=None

class LanguageResult(Strict):
    requestedLanguage: Language
    detectedLanguage: Literal['english','hindi','hinglish','mixed','uncertain']
    confidenceCategory: Literal['high','medium','low']
    evidence: str
    candidateLanguage: str | None=None

class IntentAlternative(Strict):
    id: str
    name: str
    score: float

class IntentResult(Strict):
    attribution: dict | None = None
    id: str
    name: str
    domain: str
    score: float
    scoreType: str
    marginGap: float
    alternatives: list[IntentAlternative]
    needsClarification: bool
    modelVersion: str

class EntityResult(Strict):
    type: str
    text: str
    value: str
    normalizedValue: str | None=None
    normalizedId: str | None=None
    status: Literal['resolved','ambiguous','unresolved']
    vocabularySource: str | None=None
    alternatives: list[str]=[]
    interpretationNotes: list[str] = Field(default_factory=list)
    unitSource: str | None = None
    unit: str | None=None
    approximate: bool | None=None
    start: int
    end: int
    method: str
    confidence: float | None=None
    uncertainty: str | None=None

class MissingSlot(Strict):
    slot: str
    label: str
    priority: int
    question: str
    reason: str

class UnresolvedSlot(Strict):
    slot: str
    reason: str
    condition: str
    present: bool | None=None

class ReadinessResult(Strict):
    found: int
    total: int
    percentage: int
    status: str

class AnalyzeResponse(Strict):
    extractionMetadata: dict = Field(default_factory=dict)
    inputText: str
    normalizedText: str
    language: LanguageResult
    intent: IntentResult
    entities: list[EntityResult]
    missingSlots: list[MissingSlot]
    unresolvedSlots: list[UnresolvedSlot]
    readiness: ReadinessResult
    warnings: list[str]
    modelVersion: str
