import time
import uuid
from dataclasses import dataclass, field

MAX_SESSIONS = 200
BUSY_TIMEOUT = 120  # segundos; evita que una conexión caída bloquee la sesión para siempre


@dataclass
class Session:
    id: str
    caso: dict
    persona: dict
    mensajes: list = field(default_factory=list)  # [{"role": "user"|"assistant", "content": str}]
    finished: bool = False
    result: dict | None = None
    busy_at: float | None = None

    @property
    def busy(self) -> bool:
        return self.busy_at is not None and (time.time() - self.busy_at) < BUSY_TIMEOUT

    def lock(self):
        self.busy_at = time.time()

    def unlock(self):
        self.busy_at = None


_store: dict[str, Session] = {}


def create(caso: dict, persona: dict) -> Session:
    if len(_store) >= MAX_SESSIONS:
        _store.pop(next(iter(_store)))  # descarta la más antigua
    s = Session(id=uuid.uuid4().hex, caso=caso, persona=persona)
    _store[s.id] = s
    return s


def get(session_id: str) -> Session | None:
    return _store.get(session_id)
