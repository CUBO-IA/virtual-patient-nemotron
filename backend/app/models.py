from pydantic import BaseModel, Field


class SessionCreateIn(BaseModel):
    nivel: int | None = None
    caso_id: str | None = None
    modo: str = "consulta"


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class PruebasRequestIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=5)


class MedicamentoPlanIn(BaseModel):
    id: str
    dosis: str | None = None
    frecuencia: str | None = None
    duracion: str | None = None


class PlanTratamientoIn(BaseModel):
    disposicion: str
    medicamentos: list[MedicamentoPlanIn] = Field(default_factory=list)
    sin_tratamiento_farmacologico: bool = False
    indicaciones: list[str] = Field(default_factory=list)
    control_dias: int | None = Field(default=None, ge=1, le=14)


class ExplicarIn(BaseModel):
    tipo: str = Field(min_length=1, max_length=20)
    id: str = Field(min_length=1, max_length=80)


class FinishIn(BaseModel):
    diagnostico_estudiante: str = Field(min_length=1, max_length=500)
    diferenciales: list[str] | None = None
    plan: PlanTratamientoIn | None = None


class TriajeIn(BaseModel):
    prioridad: str
    accion: str
