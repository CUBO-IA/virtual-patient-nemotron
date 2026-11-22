# Modo Urgencias

Instrucciones para un agente (Codex). Lee este archivo completo, además de `AGENTS.md`, antes de tocar código. Adapta al repo actual la propuesta `modo-urgencias.md`.

- **Qué es:** un modo aparte donde el usuario **reconoce señales de alarma** y **decide la prioridad** (rojo, amarillo o verde) y la **acción** de un paciente, con tiempo y preguntas limitados. Pensado para personas sin formación médica.
- **Qué no es:** no sustituye la consulta clínica (anamnesis, diagnóstico, plan). Es otro flujo, con otro puntaje.
- **Estado:** propuesta; nada implementado todavía.
- **Aviso en todas las pantallas del modo:** *«Esto es una práctica con casos ficticios. En una emergencia real, llama a los servicios de emergencia de tu país.»*

---

## 1. Diferencias con la propuesta original (`modo-urgencias.md`)

La propuesta se escribió para otro diseño (24 enfermedades en `enfermedades_el_salvador.json`, pixel art, el caso «Alberto»). Este repo es distinto; **sigue lo de aquí**:

| Propuesta original | En este repo |
|---|---|
| `signos_de_alarma` por enfermedad en un JSON aparte | Ya existe `banderas_rojas` en cada caso de `data/casos.json` (`{id, texto, keywords[]}`). **Reutilízalas** como signos de alarma. |
| 24 enfermedades | 8 casos: dengue, ERC, DM2, HTA, trauma, gastroenteritis, neumonía, depresión. Solo algunos tienen una versión urgente razonable. |
| Imágenes pixel art | **No.** Se mantiene DiceBear y el paciente animado (`PacienteAnimado.jsx`, estados derivados). Sin sangre ni heridas. |
| Caso de ejemplo «Alberto, 94 años» | Descartado: no existe en este dataset. Las personas se sortean con `assign.py` según las `restricciones` del caso. |
| Asma como caso recomendado | No está en el catálogo de casos. Los 3 casos iniciales son otros (ver §3). |
| Cronómetro solo en el cliente | **También en el servidor** (hora de inicio guardada en la sesión), para que la rapidez y el límite no se puedan saltar. |

---

## 2. Reglas que no se negocian

- **No inventes validación clínica.** Cada prioridad (rojo/amarillo/verde), cada signo y cada acción esperada son decisiones médicas. Todo caso de urgencia nace con `revision_clinica: {"estado": "pendiente", "revisado_por": null, "fecha": null, "fuente": null}` y **solo una persona del área de la salud** lo cambia a `validado` (`AGENTS.md` §11). Mientras tanto el modo se muestra solo con `SEGUIMIENTO_DEMO=true` y con aviso visible de contenido sin validar, igual que pruebas y plan.
- **Nada oculto sale al cliente antes de terminar:** ni `nivel`, ni `signos_activos`, ni `accion_esperada`, ni `datos_ocultos`, ni las explicaciones. Hay que añadir una prueba que lo verifique (`test_no_leak.py` es el modelo).
- **El paciente nunca dice el diagnóstico ni la prioridad.** No aflojes las reglas del prompt del paciente (`AGENTS.md` §6): lo de urgencias **se añade**, no reemplaza.
- **El modelo no decide la prioridad.** La prioridad correcta, los signos y la acción salen del JSON. El modelo solo interpreta al paciente (y, si acaso, redacta una explicación a partir de datos ya calculados).
- Texto de interfaz y prompts en español, lenguaje simple. Sin commit.

---

## 3. Casos

Archivo nuevo `data/urgencias.json` (lista). Cada entrada **tiene el mismo esquema que un caso de `casos.json`** (`id`, `motivo_consulta`, `sintomas`, `antecedentes`, `habitos`, `datos_si_pregunta`, `restricciones`, `diagnostico`, `diagnostico_alias`, `lista_verificacion`, `banderas_rojas`) para reutilizar prompt, sorteo de persona y detección, más:

```json
{
  "id": "u_infarto_01",
  "caso_base": null,
  "urgencia": {
    "nivel": "rojo",
    "signos_activos": ["presion_pecho", "sudor_frio", "dolor_brazo"],
    "accion_esperada": "emergencias",
    "tiempo_limite_seg": 180,
    "max_preguntas": 8,
    "preguntas_minimas_semaforo": 3,
    "acompanante": { "tiene": true, "relacion": "hija" },
    "datos_ocultos": ["empezó hace una hora", "tiene la presión alta desde hace años"],
    "explicacion": "Texto en lenguaje simple de por qué esta es la prioridad correcta."
  },
  "revision_clinica": { "estado": "pendiente", "revisado_por": null, "fecha": null, "fuente": null }
}
```

- `signos_activos`: **ids** de `banderas_rojas` del mismo caso (no texto suelto), para detectarlos con las mismas keywords que el resto del sistema.
- `accion_esperada`: una de `emergencias` · `atencion_inmediata` · `evaluacion_pronto` · `consulta_normal`.
- `caso_base`: id de un caso de `casos.json` cuando la versión urgente es **el mismo caso con las banderas rojas activadas** (p. ej. neumonía con labios morados y confusión). Si es `null`, es un caso nuevo (infarto, derrame).
- Un caso **verde** (estable, sin signos) también debe existir: sin él, elegir «rojo» siempre sería la estrategia ganadora. Incluye al menos un caso verde por cada 3 urgentes.

**Casos iniciales (fase 1):** 3, redactados como borrador pendiente de revisión:

1. **Sospecha de infarto** (rojo) — caso nuevo.
2. **Sospecha de derrame cerebral** (rojo) — caso nuevo.
3. **Neumonía con signos de alarma** (rojo; `caso_base: c_nac_01`) y **uno verde** derivado de un caso existente sin banderas activadas (p. ej. gastroenteritis leve).

Más adelante, de `casos.json`: HTA con dolor de pecho, DM2 con confusión, ERC con falta de aire, gastroenteritis con sangre (amarillo). Las demás filas de la tabla original (asma, zika, varicela…) **no se implementan** porque no hay caso base.

Validador: extiende `scripts/validate_casos.py` (o crea `scripts/validate_urgencias.py`) para comprobar que `signos_activos` ⊆ ids de `banderas_rojas`, que el nivel y la acción son valores válidos, que el diagnóstico no aparece en `motivo_consulta`/`sintomas`/`datos_si_pregunta` y que `explicacion` existe.

---

## 4. Backend

Lee antes: `sessions.py`, `assign.py`, `prompts.py`, `main.py`, `evaluate.py` (`_hit`, `norm`), `niveles.py`, `config.py`.

### 4.1 Sesión
- `POST /api/sessions` acepta `modo: "consulta" | "urgencias"` (por defecto `consulta`; **no cambies el comportamiento actual**) y, opcionalmente, `caso_id`.
- En modo urgencias el caso sale de `data/urgencias.json` y la persona se sortea con `assign.py` como siempre.
- La `Session` guarda `modo`, `iniciada_en` (hora del servidor) y el resultado del triaje. **Todo cambio llama a `sessions.guardar(s)`** (`AGENTS.md` §12) y se restaura desde disco.
- La respuesta pública añade solo: `modo`, `tiempo_limite_seg`, `max_preguntas`, `acompanante` (si tiene y su relación), `preguntas_minimas_semaforo`. **Nada más** de `urgencia`.

### 4.2 Chat
- Rechaza (409) el mensaje número `max_preguntas + 1` y los mensajes tras vencer `tiempo_limite_seg` (mensaje claro: «Se acabó el tiempo; elige la prioridad»). El tiempo se mide con el reloj del servidor.
- Prompt: **añade** el bloque siguiente al prompt normal (no lo reemplaza):

```
Estás en urgencias y te sientes mal. Reglas:
- Responde en frases cortas (máximo 12 palabras).
- Se nota tu malestar: pausas, quejidos, poca paciencia.
- {si hay acompañante} Tu {relacion} te acompaña y a veces responde por ti.
- Muestra sin que te lo pidan: {textos de los signos_activos}
- Solo dices esto si te lo preguntan directamente: {datos_ocultos}
- Nunca digas qué enfermedad crees tener ni qué tan grave es.
```

  Si el caso es de falta de aire, añade «habla entrecortado». Con 7B, **mide** el resultado (§7.2) antes de darlo por bueno.

### 4.3 Triaje (cierre)
`POST /api/sessions/{id}/triaje` con `{prioridad: "rojo"|"amarillo"|"verde", accion: "<una de las 4>"}`.
- 409 si hay menos de `preguntas_minimas_semaforo` preguntas (evita elegir por color sin pensar), 409 si ya se envió (no se puede cambiar), 422 si los valores no son válidos.
- Devuelve y guarda el resultado:

```json
{
  "prioridad_correcta": "rojo", "accion_correcta": "emergencias",
  "prioridad_elegida": "amarillo", "accion_elegida": "evaluacion_pronto",
  "signos": {"encontrados": ["…"], "faltantes": ["…"]},
  "preguntas_esenciales": {"hechas": ["…"], "faltantes": ["…"]},
  "puntaje": 55, "desglose": {"prioridad": 0, "signos": 30, "esenciales": 10, "rapidez": 5, "pistas": -5},
  "alerta_seguridad": "Elegiste menos urgencia de la necesaria…",
  "explicacion": "…"
}
```

### 4.4 Puntaje
| Criterio | Puntos |
|---|---|
| Prioridad | 50 exacta · 25 más urgente de lo necesario · **0 menos urgente** |
| Signos de alarma encontrados | 30 × fracción |
| Preguntas esenciales hechas (`lista_verificacion`) | 10 × fracción |
| Rapidez | 10, lineal según el tiempo usado frente al límite (reloj del servidor) |
| Cada pista usada (máx. 2) | −5 |

- **Seguridad:** si la prioridad elegida es menos urgente que la correcta, o la acción es menos urgente que la esperada, el resultado lleva `alerta_seguridad` visible y no se considera aprobado, aunque el puntaje numérico supere el umbral.
- Un signo cuenta como **encontrado** si alguna pregunta del usuario lo cubre según las keywords de su bandera roja, usando `evaluate._hit` (la única lógica de detección, `AGENTS.md` §13). Lo mismo para las preguntas esenciales.
- El modelo **no** interviene en el puntaje.

### 4.5 Pistas
Reutiliza `/pista` con un máximo de 2 en este modo; cada una resta 5. La pista orienta hacia un signo no preguntado, sin revelar la prioridad.

---

## 5. Frontend (React)

Modo nuevo accesible desde la pantalla de inicio (por ejemplo, un botón «Urgencias» junto a la selección de nivel). Reutiliza `Chat.jsx`, `PatientCard.jsx` y `PacienteAnimado.jsx`.

| Elemento | Detalle |
|---|---|
| Cronómetro | Cuenta regresiva; se pone rojo en los últimos 30 s. La fuente de verdad es el servidor: sincroniza con la hora de inicio de la sesión. |
| Contador | «5 de 8 preguntas». |
| Paciente | Estado `dolor`/malestar en `PacienteAnimado` (temblor suave, respiración rápida). Sin sangre ni heridas. |
| Semáforo | Tres botones (rojo, amarillo, verde) **deshabilitados** hasta `preguntas_minimas_semaforo` preguntas. |
| Acción | Selector con las 4 acciones. El envío es definitivo. |
| Resultados | Prioridad correcta frente a la elegida, signos encontrados y faltantes, preguntas esenciales, puntaje con desglose, explicación en lenguaje simple y la alerta de seguridad si corresponde. |
| Avisos | Aviso de «práctica, no es una emergencia real» en todas las pantallas del modo; aviso de contenido sin validar si aplica. |

El nombre de la enfermedad **no** aparece en ninguna pantalla del modo antes de terminar (y, si se muestra al final, junto a la explicación).

---

## 6. Pruebas

En `backend/tests/test_urgencias.py` (sin Ollama: usa los mismos mocks que `test_sesiones_persistentes.py`):

- No filtra `nivel`, `signos_activos`, `accion_esperada`, `datos_ocultos` ni `explicacion` ni en `/api/sessions` ni en `/chat` ni antes de `/triaje`.
- Límite de preguntas y de tiempo (con reloj simulado) → 409.
- Triaje: 409 con menos de 3 preguntas, 409 al repetirlo, 422 con valores inválidos.
- Puntaje: tabla completa de prioridad (exacta / más urgente / menos urgente) para los 3 niveles; rapidez; pistas; alerta de seguridad.
- Los signos y las preguntas esenciales se detectan con `_hit`.
- La sesión sobrevive a un reinicio (guardar y restaurar `modo`, `iniciada_en`, triaje).
- El modo `consulta` no cambia: toda la suite actual (`pytest backend\tests -q`) sigue pasando.
- Validador de `urgencias.json` (§3).

---

## 7. Verificación real (con Ollama)

1. `npm run build` y `pytest` en verde.
2. **Diálogos reales con `qwen2.5:7b`:** 10 conversaciones por caso inicial (script en la carpeta de scratchpad, no en el repo). Reporta cuántas respuestas superan 12 palabras, cuántas **dicen la enfermedad o la prioridad** (debe ser 0) y si el acompañante responde cuando corresponde.
3. Recorre el flujo en el navegador: inicio → chat con cronómetro → semáforo → resultados.

---

## 8. Fases

1. **Datos y validador:** `data/urgencias.json` con los 3 casos + 1 verde (todos pendientes de revisión) y `validate_urgencias.py`.
2. **Backend:** modo en la sesión, límites, prompt, `/triaje`, puntaje, persistencia y pruebas.
3. **Verificación con Ollama** (§7.2) y ajuste del prompt si el 7B no cumple.
4. **Frontend** del modo.
5. **Documentación:** sección nueva en `AGENTS.md` (contrato de `/triaje`, esquema de `urgencias.json`, reglas) y nota breve en `README.md`.

Termina y verifica cada fase antes de pasar a la siguiente.

---

## 9. Revisión obligatoria (la hace una persona del área de la salud)

- [ ] Cada prioridad (rojo/amarillo/verde) y cada acción esperada.
- [ ] Cada signo de alarma y su pertinencia para el caso.
- [ ] Las explicaciones finales están en lenguaje simple y son correctas.
- [ ] El caso verde es realmente estable.
- [ ] Ningún caso nombra la enfermedad en la interfaz antes del cierre.
- [ ] El aviso de práctica aparece en todas las pantallas del modo.
- [ ] Las imágenes no muestran sangre ni heridas.

---

## 10. Fuera de alcance (no lo hagas ahora)

- Las enfermedades de la tabla original que no tienen caso base (asma, zika, varicela, COVID-19, etc.).
- Imágenes pixel art o escenas gráficas.
- Una capa con el modelo para decidir o explicar la prioridad.
- Cambiar el puntaje, los niveles o el flujo del modo consulta.

---

## 11. Qué entregar

Un resumen corto con: qué cambiaste por fase y en qué archivos; los resultados de los diálogos reales (§7.2); qué no pudiste verificar; y los casos que quedan pendientes de revisión médica. Si algo de este documento contradice `AGENTS.md`, sigue `AGENTS.md` y avísalo.
