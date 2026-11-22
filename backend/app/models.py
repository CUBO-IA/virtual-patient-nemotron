from pydantic import BaseModel, Field


class SessionCreateIn(BaseModel):
    nivel: int | None = None
    caso_id: str | None = None


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class FinishIn(BaseModel):
    diagnostico_estudiante: str = Field(min_length=1, max_length=500)
    diferenciales: list[str] | None = None
