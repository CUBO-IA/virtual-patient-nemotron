from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class FinishIn(BaseModel):
    diagnostico_estudiante: str = Field(min_length=1, max_length=500)
