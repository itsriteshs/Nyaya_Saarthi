from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class AnswerRequest(Strict):
    revision:int=Field(ge=1)
    questionId:str=Field(min_length=1,max_length=100)
    messageId:str=Field(min_length=1,max_length=100)
    answer:str=Field(min_length=1,max_length=20000)
    referenceDatetime:datetime | None=None
    @field_validator('answer')
    @classmethod
    def nonblank(cls,value):
        if not value.strip():raise ValueError('Answer must not be blank')
        return value

class FactEditRequest(Strict):
    revision:int=Field(ge=1)
    value:str=Field(min_length=1,max_length=10000)
    @field_validator('value')
    @classmethod
    def nonblank(cls,value):
        if not value.strip():raise ValueError('Value must not be blank')
        return value

class RevisionRequest(Strict):
    revision:int=Field(ge=1)

class VerifyRequest(RevisionRequest):
    acknowledgeUnknowns:bool=False
