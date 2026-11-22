# Pruebas, tratamiento y seguimiento — especificación

Diseño de tres módulos que completan el ciclo clínico de Paciente Virtual: **pedir pruebas**, **indicar un plan de tratamiento** y **ver la evolución del paciente en un control**. Escrito para que una persona o Codex lo implemente con este archivo, `AGENTS.md`, `NIVELES.md` y el código del repo.

- **Estado:** propuesta; nada implementado.
- **Depende de:** el sistema de niveles ya presente en el código (`data/niveles.json`, `backend/app/niveles.py`, puntaje con `desglose`).
- **Requisito clínico:** un médico o docente debe validar todo el contenido médico (§11). Sin eso, los módulos no se activan en ningún caso (§4.5).

---

## 1. Objetivo y principios

**Objetivo:** hoy la app mide solo la entrevista y el diagnóstico. Un estudiante de medicina también tiene que decidir *qué pedir*, *qué indicar* y *qué pasa después*. Estos módulos cierran ese ciclo y enseñan las consecuencias de cada decisión.

**Principios (no negociables):**

1. **El modelo de lenguaje no inventa contenido clínico.** Resultados de pruebas, medicamentos, contraindicaciones y evolución vienen de datos escritos y validados por un médico. El modelo solo redacta la retroalimentación sobre listas ya calculadas y, a lo sumo, narra con la voz de la persona un texto que ya existe.
2. **Elección estructurada, no texto libre.** Pruebas, medicamentos e indicaciones se eligen de catálogos. El texto libre no se puede evaluar de forma fiable y abre la puerta a respuestas absurdas.
3. **Nada de esto puede filtrar el diagnóstico.** El catálogo de pruebas es el mismo para todos los casos y contiene pruebas irrelevantes; los informes describen hallazgos sin nombrar la enfermedad; la pertinencia de cada decisión solo se revela al terminar.
4. **Un caso sin validar no activa estos módulos** (§4.5). La seguridad clínica manda sobre la funcionalidad.
5. **Todo es opcional y configurable por nivel** en `data/niveles.json`. Con los módulos apagados, el puntaje y el comportamiento actuales no cambian (prueba de regresión, §10.1).
6. **No es una guía de prescripción real.** Aviso visible en las pantallas de plan: «Ejercicio educativo. No uses esta aplicación para decidir tratamientos reales».

---

## 2. Estado actual relevante

| Pieza | Dónde | Hoy |
|---|---|---|
| Niveles y pesos | `data/niveles.json`, `backend/app/niveles.py` | Básico, Intermedio y Avanzado con `pesos` (`checklist`, `diagnostico`, `banderas`, `diferenciales`) y pistas. |
| Evaluación con desglose | `backend/app/evaluate.py` | Calcula `desglose`, descuento de pistas y reescala pesos cuando un componente «no aplica» (patrón reutilizable). |
| Cierre de consulta | `POST /api/sessions/{id}/finish` | Recibe `diagnostico_estudiante` y `diferenciales`. |
| Estado de sesión | `backend/app/sessions.py` | `nivel`, `mensajes`, `pistas_usadas`, `preguntas_usadas` (calculado). |
| Casos | `data/casos.json` | 8 casos con `dificultad`, `diferenciales`, `pistas`, `guia_ref`. Sin pruebas, plan ni evolución. |
| Retroalimentación | `prompts.user_feedback` | Recibe listas de cumplidos y faltantes, y citas del RAG. |
| Interfaz | `App.jsx`, `Chat.jsx`, `Results.jsx`, `Progress.jsx` | Fases `inicio → chat → diagnostico → resultados`. |

---

## 3. Visión general

### 3.1 Flujo nuevo

```
Entrevista (chat) ──► Pruebas (opcional) ──► Diagnóstico + Plan ──► Resultados + «Control a los N días»
      ▲                    │
      └────── el estudiante puede volver a la entrevista tras ver resultados ──────┘
```

- **Pruebas:** una pestaña junto al chat, disponible mientras la consulta está abierta. Cada resultado queda visible en una lista y se puede releer.
- **Diagnóstico + plan:** se entregan **juntos** en un único `POST /finish` (menos viajes y sin estados intermedios que sincronizar). La interfaz los presenta en dos pasos, pero el servidor los recibe a la vez.
- **Seguimiento:** se calcula en el servidor dentro de `/finish` y se devuelve en la respuesta. No hay endpoint extra.

### 3.2 Módulos y su riesgo

| Módulo | Valor | Riesgo | Esfuerzo | Orden |
|---|---|---|---|---|
| **A. Pruebas** | Alto | Bajo | ~1 día | 1.º |
| **B. Plan de tratamiento** | Alto | **Alto** | ~1,5 días + médico | 2.º |
| **C. Seguimiento (control)** | Muy alto | Medio | ~1 día (narrado) | 3.º |

Recomendación para el hackathon: **solo el módulo A** (§12).

---

## 4. Datos

### 4.1 `data/catalogo_pruebas.json` (nuevo, global)

Un solo catálogo para todos los casos, con **más pruebas de las necesarias** para que su presencia no sugiera el diagnóstico.

```json
{
  "version": 1,
  "categorias": ["Laboratorio", "Imagen", "Rápidas", "Otras"],
  "pruebas": [
    {
      "id": "hemograma",
      "nombre": "Hemograma completo",
      "categoria": "Laboratorio",
      "nivel_atencion": "primer_nivel",
      "costo": 1,
      "nota": "Recuento de glóbulos rojos, blancos y plaquetas."
    },
    {
      "id": "rx_torax",
      "nombre": "Radiografía de tórax",
      "categoria": "Imagen",
      "nivel_atencion": "hospital",
      "costo": 2,
      "nota": "Proyección posteroanterior."
    }
  ]
}
```

Campos: `costo` 1-3 (relativo, usado en niveles con presupuesto); `nivel_atencion` ∈ {`primer_nivel`, `hospital`} (informativo en v1: mostrar «requiere referencia» en el nivel Avanzado).

**Catálogo inicial sugerido (~20):** hemograma, química sanguínea (glucosa, creatinina, urea), glucosa capilar, examen general de orina, perfil lipídico, transaminasas, electrolitos, gasometría, examen de heces, coprocultivo, hemocultivo, radiografía de tórax, ecografía abdominal, electrocardiograma, tomografía de cráneo, prueba rápida de dengue (NS1/IgM), prueba rápida de malaria, prueba de VIH, prueba de embarazo, PCR.

### 4.2 Datos por caso: `pruebas`

Nuevo campo en cada caso. Solo se listan las pruebas con **resultado propio**; el resto usa `resultado_defecto` (§4.2.1).

```json
"pruebas": {
  "resultado_defecto": "Sin hallazgos relevantes para este caso.",
  "resultados": {
    "hemograma": {
      "pertinencia": "esencial",
      "informe": "Leucocitos 3 200/µL (bajos). Plaquetas 85 000/µL (bajas). Hematocrito 48 %.",
      "valores": [
        { "analito": "Leucocitos", "valor": "3 200", "unidad": "/µL", "referencia": "4 500–11 000", "estado": "bajo" },
        { "analito": "Plaquetas",  "valor": "85 000", "unidad": "/µL", "referencia": "150 000–450 000", "estado": "bajo" },
        { "analito": "Hematocrito","valor": "48", "unidad": "%", "referencia": "40–50", "estado": "normal" }
      ]
    },
    "rx_torax": {
      "pertinencia": "innecesaria",
      "informe": "Campos pulmonares sin infiltrados. Silueta cardíaca normal."
    }
  },
  "esenciales": ["hemograma"]
}
```

| Campo | Significado |
|---|---|
| `pertinencia` | `esencial` (confirma o descarta lo importante), `util` (aporta, no imprescindible) o `innecesaria` (sin indicación en este caso). Las no listadas se consideran `innecesaria` salvo que el caso diga lo contrario. |
| `informe` | Texto del resultado. **Describe hallazgos; no nombra la enfermedad** (ni «compatible con…» ni «sugestivo de…»). |
| `valores` | Opcional. Para laboratorio, una tabla con `estado` ∈ {`bajo`, `normal`, `alto`}. |
| `esenciales` | Ids de las pruebas que un buen estudiante debería pedir. |

#### 4.2.1 Resultado por defecto

Una prueba no listada devuelve `resultado_defecto`. Es el punto más delicado: si una prueba omitida *debería* salir alterada para ese caso, el resultado por defecto sería clínicamente falso. Por eso:

- El médico revisa, caso por caso, que **ninguna prueba del catálogo no listada tenga que salir alterada**; esa revisión queda registrada (§4.5).
- El validador exige que `resultado_defecto` exista y que todo id de `resultados` y `esenciales` esté en el catálogo.

#### 4.2.2 Ejemplo de coherencia clínica

Las cifras de arriba son **ilustrativas** de un cuadro viral con consumo de plaquetas. **No son material validado**: cada valor debe confirmarlo un médico antes de usarse.

### 4.3 `data/formulario.json` (nuevo, módulo B)

Catálogo de medicamentos disponibles para recetar, **corto y de uso común en primer nivel**.

```json
{
  "version": 1,
  "medicamentos": [
    {
      "id": "acetaminofen",
      "nombre": "Acetaminofén (paracetamol)",
      "grupo": "Analgésico/antipirético",
      "vias": ["oral"],
      "alias": ["paracetamol", "acetaminofen", "dolex"]
    }
  ],
  "indicaciones": [
    { "id": "hidratacion", "texto": "Hidratación oral abundante" },
    { "id": "reposo", "texto": "Reposo relativo" },
    { "id": "signos_alarma", "texto": "Explicar signos de alarma y cuándo volver" },
    { "id": "control", "texto": "Cita de control" },
    { "id": "dieta", "texto": "Indicaciones de alimentación" },
    { "id": "evitar_ains", "texto": "Evitar antiinflamatorios" }
  ],
  "disposiciones": [
    { "id": "ambulatorio", "texto": "Manejo ambulatorio" },
    { "id": "observacion", "texto": "Observación en la unidad de salud" },
    { "id": "referencia", "texto": "Referir al hospital" },
    { "id": "emergencia", "texto": "Emergencia / ingreso inmediato" }
  ]
}
```

**Dosis:** en la v1 **no se puntúan**. El formulario puede pedir dosis, frecuencia y duración como campos informativos, pero evaluarlas exige rangos validados (§12, fase 7). Mejor no puntuar una dosis que puntuar una incorrecta.

### 4.4 Datos por caso: `plan_esperado` y `evolucion`

```json
"plan_esperado": {
  "disposicion": { "correcta": ["referencia", "emergencia"], "aceptable": ["observacion"] },
  "medicamentos": {
    "adecuados":      [ { "id": "acetaminofen", "nota": "Control de la fiebre." } ],
    "aceptables":     [],
    "contraindicados": [ { "id": "ibuprofeno", "motivo": "Riesgo de sangrado en dengue." },
                         { "id": "aspirina",   "motivo": "Riesgo de sangrado en dengue." } ]
  },
  "indicaciones": { "esenciales": ["hidratacion", "signos_alarma", "control"] },
  "alergias_trampa": []
},
"evolucion": {
  "control_en_dias": 2,
  "ramas": {
    "mejora": {
      "condicion": "disposicion_correcta y sin_contraindicados y indicaciones_esenciales_completas",
      "relato": "Ya me siento más tranquilo, doctor. La fiebre bajó y puedo tomar líquidos."
    },
    "parcial": {
      "condicion": "disposicion_aceptable o faltan_indicaciones_esenciales",
      "relato": "Sigo con malestar y poco apetito, pero no me ha vuelto a sangrar."
    },
    "empeora": {
      "condicion": "hay_contraindicado o disposicion_insuficiente",
      "relato": "Estoy peor, doctor. Me volvió a sangrar la encía y me duele mucho la barriga."
    }
  }
}
```

Reglas:

- `condicion` es una **expresión de una lista cerrada de predicados** (§6.3), no código libre. Se evalúa de arriba abajo; gana la primera que cumpla (`empeora` primero por seguridad).
- `relato` está escrito en lenguaje llano, con el habla salvadoreña del caso; no nombra la enfermedad.
- Si un caso no tiene `evolucion`, el seguimiento se omite (el resto del plan sigue funcionando).
- `alergias_trampa` (opcional): lista de `{ medicamento, dato }` donde el dato de alergia sale solo si el estudiante pregunta («¿es alérgico a algún medicamento?»). Receta un alergénico sin haberlo preguntado → alerta de seguridad. Requiere que el caso tenga ese dato en `datos_si_pregunta` y una keyword de «alergias» en su lista de verificación.

### 4.5 Validación clínica del contenido (puerta de seguridad)

Nuevo campo por caso:

```json
"revision_clinica": {
  "estado": "pendiente",
  "revisado_por": null,
  "fecha": null,
  "fuente": null,
  "observaciones": null
}
```

- `estado` ∈ {`pendiente`, `validado`}. Solo `validado` activa los módulos A, B y C en ese caso.
- Con `pendiente`, la sesión funciona **como hoy**: sin pestaña de pruebas, sin plan, sin seguimiento. El puntaje se reescala (§6.4).
- La interfaz muestra una insignia «Caso validado por [nombre]» cuando corresponde.
- El validador de datos falla si hay `validado` sin `revisado_por`, `fecha` y `fuente`.

---

## 5. Integración con niveles (`data/niveles.json`)

Se añaden dos bloques por nivel, **opcionales**: si faltan, el módulo está apagado y el nivel se comporta como hoy.

```json
"modulos": {
  "pruebas":     { "habilitado": true, "max": null, "mostrar_costo": false, "presupuesto": null },
  "plan":        { "habilitado": true, "bloquea_aprobado_si_contraindicado": false },
  "seguimiento": { "habilitado": true }
},
"pesos": { "checklist": 40, "diagnostico": 25, "banderas": 5, "diferenciales": 0, "pruebas": 10, "plan": 20 }
```

**Propuesta de configuración** (cada fila suma 100):

| Nivel | Checklist | Dx | Banderas | Difer. | Pruebas | Plan | Reglas de pruebas | Reglas de plan |
|---|---|---|---|---|---|---|---|---|
| 1 Básico | 40 | 25 | 5 | 0 | 10 | 20 | Sin límite, sin costos | Sin bloqueo |
| 2 Intermedio | 35 | 25 | 5 | 0 | 15 | 20 | Máx. 6, costo visible | Sin bloqueo |
| 3 Avanzado | 25 | 20 | 10 | 5 | 15 | 25 | Máx. 4 o presupuesto de 6 puntos de costo, costo visible | **Contraindicado impide aprobar** |

`pesos.pruebas` y `pesos.plan` ausentes valen 0. El seguimiento **no puntúa**: muestra la *consecuencia* de las decisiones y evita contarlas dos veces.

---

## 6. Backend

### 6.1 Estado de sesión

Añadir a `Session`:

- `pruebas_pedidas: list[str]` (ids, en orden, sin repetir).
- `costo_pruebas: int` (suma de `costo`).
- `modulos_activos: dict` calculado al crear la sesión: nivel × `revision_clinica.estado == "validado"` × presencia de datos (`pruebas`, `plan_esperado`, `evolucion`).

### 6.2 API

Todos los cambios son compatibles hacia atrás.

#### `GET /api/catalogo/pruebas` (nuevo)

Devuelve el catálogo **sin** `pertinencia` ni nada por caso. Incluye `categorias`.

#### `POST /api/sessions` (cambia)

La respuesta añade:

```json
"modulos": {
  "pruebas": { "habilitado": true, "max": 6, "mostrar_costo": true, "presupuesto": null },
  "plan": true,
  "seguimiento": true
},
"revision_clinica": { "estado": "validado", "revisado_por": "Dra. …" }
```

Si un módulo está apagado para esa sesión, su valor es `false` y la interfaz oculta la pestaña.

#### `POST /api/sessions/{id}/pruebas` (nuevo)

Cuerpo: `{ "ids": ["hemograma", "rx_torax"] }` (1 a 5 ids por llamada).

Reglas:

| Situación | Respuesta |
|---|---|
| Módulo apagado | **404** «Este caso no incluye pruebas». |
| Id fuera del catálogo | **422** con el id. |
| Prueba ya pedida | Se devuelve el mismo resultado, **sin** costo adicional ni contar de nuevo. |
| Superaría `max` o el `presupuesto` | **409** «Alcanzaste el límite de pruebas de este nivel». No se pide ninguna de la tanda (todo o nada). |
| Consulta ya terminada | **409**. |

Respuesta:

```json
{
  "resultados": [
    { "id": "hemograma", "nombre": "Hemograma completo", "categoria": "Laboratorio",
      "informe": "Leucocitos 3 200/µL (bajos). …", "valores": [ … ], "costo": 1 }
  ],
  "pruebas_usadas": 2,
  "limite": 6,
  "costo_total": 3,
  "presupuesto_restante": null
}
```

**Nunca** devuelve `pertinencia`, `esenciales` ni el diagnóstico.

#### `POST /api/sessions/{id}/finish` (cambia)

Cuerpo ampliado (todo lo nuevo es opcional; si el módulo está apagado, se ignora):

```json
{
  "diagnostico_estudiante": "…",
  "diferenciales": ["…", "…"],
  "plan": {
    "disposicion": "referencia",
    "medicamentos": [
      { "id": "acetaminofen", "dosis": "500 mg", "frecuencia": "cada 8 h", "duracion": "3 días" }
    ],
    "sin_tratamiento_farmacologico": false,
    "indicaciones": ["hidratacion", "signos_alarma", "control"],
    "control_dias": 2
  }
}
```

Validaciones (**422**): `disposicion` debe estar en el catálogo; `medicamentos[].id` e `indicaciones[]` deben existir; sin medicamentos solo se acepta con `sin_tratamiento_farmacologico: true`; sin repetir medicamentos; módulo de plan activo y plan ausente → 422 «Falta el plan de tratamiento».

Respuesta: todo lo actual **más**:

```json
{
  "pruebas": {
    "solicitadas": [ { "id": "hemograma", "nombre": "…", "pertinencia": "esencial", "costo": 1 } ],
    "esenciales_faltantes": ["Ecografía abdominal"],
    "innecesarias": ["Radiografía de tórax"],
    "costo_total": 3
  },
  "plan": {
    "medicamentos": [ { "id": "acetaminofen", "nombre": "…", "veredicto": "adecuado", "nota": "Control de la fiebre." } ],
    "medicamentos_faltantes": [],
    "disposicion": { "elegida": "referencia", "veredicto": "correcta" },
    "indicaciones": { "cumplidas": ["Hidratación oral abundante"], "faltantes": ["Cita de control"] },
    "alertas_seguridad": []
  },
  "seguimiento": { "dias": 2, "evolucion": "mejora", "relato": "Ya me siento más tranquilo, doctor…" },
  "desglose": { "…": "…", "pruebas": { "obtenido": 12, "maximo": 15 }, "plan": { "obtenido": 18, "maximo": 20 } }
}
```

`veredicto` de medicamento ∈ {`adecuado`, `aceptable`, `innecesario`, `contraindicado`}. `alertas_seguridad` es una lista de textos con el motivo (p. ej. «Ibuprofeno: riesgo de sangrado en dengue»).

#### `GET /api/health` (cambia)

Añade `catalogos: true|false` (pruebas y formulario cargan y validan).

### 6.3 Predicados permitidos en `evolucion.condicion`

Lista **cerrada** (el validador rechaza cualquier otra):

`disposicion_correcta`, `disposicion_aceptable`, `disposicion_insuficiente`, `hay_contraindicado`, `sin_contraindicados`, `medicacion_adecuada_completa`, `faltan_medicamentos_adecuados`, `indicaciones_esenciales_completas`, `faltan_indicaciones_esenciales`, `pidio_pruebas_esenciales`, `no_pidio_pruebas_esenciales`, `alergia_ignorada`.

Se combinan con `y`, `o` y `no`. Se interpretan con un evaluador propio de expresiones booleanas simples (**nunca** con `eval`).

### 6.4 Puntaje

Se generaliza el patrón que ya existe para «diferenciales no aplican»:

1. Construir los pesos del nivel.
2. Marcar cada componente como `aplica` o `no aplica` (módulo apagado, caso sin datos o sin `validado`).
3. Reescalar los pesos de los componentes que aplican a 100.
4. Calcular y redondear como hoy.

**Con todos los módulos apagados el resultado es idéntico al actual** (prueba de regresión).

#### Componente de pruebas

```
frac_esenciales = pedidas_esenciales / total_esenciales          (1 si no hay esenciales)
penalización    = 0,2 × n_innecesarias
obtenido        = W.pruebas × clamp(frac_esenciales − penalización, 0, 1)
```

- Una prueba de pertinencia `util` no suma ni resta.
- Pedir una prueba `esencial` ya pedida no cambia nada.
- Si el nivel tiene `presupuesto` y se excedió, el servidor ya lo impidió (409); no hay doble castigo.

#### Componente de plan

Se reparte el peso en tres: **medicación 50 %**, **disposición 30 %**, **indicaciones 20 %**.

| Sub-componente | Regla |
|---|---|
| Medicación | `adecuados` pedidos / `adecuados` totales. `aceptable` cuenta 0,5. Cada `innecesario` resta 0,15 (mínimo 0). **Cualquier `contraindicado` pone la medicación en 0.** |
| Disposición | `correcta` = 100 %; `aceptable` = 50 %; otra = 0 %. |
| Indicaciones | `cumplidas esenciales` / `esenciales`. Las no esenciales no suman. |

#### Seguridad

- Un `contraindicado` (o una alergia ignorada) genera una entrada en `alertas_seguridad` y un banner rojo en resultados, con el motivo.
- Con `bloquea_aprobado_si_contraindicado: true` (Avanzado), `aprobado = false` y el `puntaje` se recorta a `aprobado_desde − 1` como máximo. El `desglose` muestra el cálculo original para que se entienda el recorte.

### 6.5 Retroalimentación (LLM)

`prompts.user_feedback` recibe además listas ya calculadas: pruebas esenciales faltantes, innecesarias, veredicto de cada medicamento con su `nota`/`motivo`, disposición y alertas. Reglas del prompt:

- Debe basarse **solo** en esas listas; no recomendar medicamentos, dosis ni pruebas que no estén en ellas.
- Si hay `alertas_seguridad`, debe mencionarlas primero y con claridad.
- Con RAG activo, puede citar fragmentos de la guía (`guia_ref`) para justificar.
- Máximo 6 frases.

Si el modelo falla, se conserva el feedback determinista (como hoy), ampliado con las mismas listas.

### 6.6 Seguimiento

`seguimiento.relato` es texto **pregrabado** por rama (§4.4), elegido por reglas. En la v1 no se llama al modelo. Opcionalmente se reproduce con la voz del paciente usando el endpoint de TTS que ya existe.

**Variante futura (fase 6):** continuar la conversación en el control con un prompt que incluya la rama y su relato como estado; el paciente responde solo con esa información.

---

## 7. Frontend

### 7.1 Pestaña «Pruebas» (junto al chat)

- Catálogo agrupado por categoría, con buscador. Cada prueba: nombre, nota corta, costo (si `mostrar_costo`) y botón «Solicitar».
- Contador `2 / 6` (o presupuesto restante). Al llegar al límite, los botones se desactivan con el motivo escrito.
- Lista de **resultados obtenidos**, más reciente arriba, con tabla de valores (marca de estado con texto «bajo/alto», no solo color) o el informe en texto. Se pueden releer durante toda la consulta.
- Términos como «hemograma» reutilizan el glosario con ayuda emergente.
- Anuncio con `aria-live` al llegar un resultado.
- Mensaje en el Básico: «Piensa: ¿qué prueba confirmaría o descartaría lo que sospechas?».

### 7.2 Formulario de cierre en dos pasos

1. **Diagnóstico** (como hoy, con diferenciales en el Avanzado).
2. **Plan de tratamiento** (si el módulo está activo):
   - Disposición: grupo de opciones (radio).
   - Medicamentos: buscador sobre `formulario.json`; cada elegido muestra campos opcionales de dosis, frecuencia y duración; opción excluyente «Sin tratamiento farmacológico».
   - Indicaciones: casillas.
   - Control en N días: selector 1-14.
   - Aviso educativo visible (§1.6).
3. «Volver al diagnóstico» no pierde lo escrito.

### 7.3 Resultados

- Nuevas secciones: **Pruebas** (solicitadas con su pertinencia, esenciales que faltaron, innecesarias), **Plan** (veredicto por medicamento, disposición, indicaciones), **Control a los N días** (relato y, si hay voz, botón de escuchar).
- Banner rojo de seguridad cuando hay `alertas_seguridad`.
- Desglose ampliado con «Pruebas» y «Plan».
- Insignia «Caso validado por …».

### 7.4 Progreso

El historial guarda también `pruebas_puntaje`, `plan_puntaje` y `alertas_seguridad` (número). Subir `version` a 2 en `progress.js` con migración (los registros antiguos reciben `null`). «Mi progreso» puede mostrar una tasa de errores de seguridad.

---

## 8. Casos límite

| Situación | Comportamiento |
|---|---|
| Caso con `revision_clinica.estado = pendiente` | Sin módulos; puntaje reescalado; la sesión funciona como hoy. |
| Nivel con módulo apagado | Pestaña y paso de plan ocultos; el servidor los ignora aunque lleguen. |
| Pedir la misma prueba dos veces | Mismo resultado, sin costo ni conteo extra. |
| Tanda de pruebas que excede el límite | 409, no se pide ninguna. |
| Prueba no listada en el caso | Devuelve `resultado_defecto`; cuenta como `innecesaria`. |
| `plan` con id inexistente | 422 con el id. |
| Sin medicamentos y sin marcar «sin tratamiento» | 422. |
| Medicamento contraindicado + disposición correcta | Medicación en 0; alerta; en Avanzado impide aprobar. |
| Alergia no preguntada y medicamento alergénico | `alerta_seguridad` «Alergia no explorada». |
| Estudiante nunca pidió pruebas en un caso sin esenciales | `frac_esenciales = 1`; sin penalización. |
| Caso sin `evolucion` | Sin sección de control; el resto funciona. |
| `catalogo_pruebas.json` o `formulario.json` inválidos | 503 claro; `/api/health` → `catalogos: false`; los módulos se apagan sin romper la entrevista. |
| Recarga de página durante la consulta | La sesión sigue en memoria; las pruebas pedidas se recuperan del servidor (añadir `GET /api/sessions/{id}/pruebas` que devuelva las ya obtenidas). |
| Backend reiniciado | 404 → volver al selector, como hoy. |

---

## 9. Seguridad y privacidad

- **Sin fugas:** el catálogo no marca nada por caso; los informes no nombran la enfermedad; `pertinencia`, `esenciales`, `plan_esperado` y `evolucion` solo se usan en el servidor y aparecen en la respuesta únicamente tras `/finish`.
- **Sin ejecución de código:** las condiciones de `evolucion` usan un evaluador de lista cerrada.
- **Sin datos personales nuevos.** El plan del estudiante vive en la sesión y, a lo sumo, en su historial local (sin nombres).
- **Contenido clínico:** nunca lo genera el modelo. Un cambio en datos clínicos pasa por revisión médica (§11).

---

## 10. Pruebas y criterios de aceptación

### 10.1 Backend (`pytest`, sin Ollama)

1. **Regresión:** con los módulos apagados, `/finish` devuelve el mismo `puntaje` que antes para las mismas entradas; las pruebas actuales siguen pasando.
2. **Catálogos:** cargan y validan; ids únicos; `costo` 1-3.
3. **Sesión:** módulos activos solo si nivel lo permite **y** el caso está `validado` y trae datos.
4. **`/pruebas`:** resultado correcto; idempotente; 409 al exceder `max`/`presupuesto` y la tanda no se aplica a medias; 422 id inválido; 404 módulo apagado; no devuelve `pertinencia`.
5. **Puntaje de pruebas:** esenciales pedidas, esenciales faltantes, innecesarias con penalización, clamp en 0 y 1, caso sin esenciales.
6. **Puntaje de plan:** adecuado, aceptable, innecesario, contraindicado (medicación 0), disposición correcta/aceptable/errónea, indicaciones.
7. **Seguridad:** alergia ignorada genera alerta; Avanzado con contraindicado → `aprobado = false` y puntaje ≤ `aprobado_desde − 1`.
8. **Evolución:** una prueba por rama; `empeora` gana ante `mejora`; predicado desconocido → error de validación, no de ejecución.
9. **Reescalado:** con módulos parciales, los pesos suman 100.
10. **No-fuga (críticas):**
    - `POST /api/sessions` y `GET /api/catalogo/pruebas` no contienen `pertinencia`, `esenciales`, `plan_esperado`, `evolucion` ni diagnósticos.
    - Ningún `informe` ni `relato` contiene el diagnóstico, sus alias ni los de los diferenciales.
    - Ningún `texto` del catálogo o del formulario está especialmente asociado a un caso.

### 10.2 Validador de datos (`scripts/validate_casos.py` o nuevo)

Falla si: un id de `pruebas.resultados`/`esenciales`/`plan_esperado` no existe en su catálogo; falta `resultado_defecto`; hay predicados fuera de la lista; `validado` sin `revisado_por`, `fecha` y `fuente`; un `informe` o `relato` nombra el diagnóstico o sus alias; un medicamento figura a la vez como `adecuado` y `contraindicado`; los pesos de un nivel no suman 100 con los módulos nuevos.

### 10.3 Interfaz (manual)

- [ ] Con caso `pendiente`, no hay pestaña «Pruebas» ni paso de plan.
- [ ] Con caso `validado`, aparece la pestaña, el contador y la insignia.
- [ ] Pedir dos veces la misma prueba no consume cupo.
- [ ] Al llegar al límite, los botones se desactivan y se explica por qué.
- [ ] El formulario de plan conserva los datos al volver atrás.
- [ ] Un medicamento contraindicado muestra el banner rojo con el motivo.
- [ ] El relato del control se lee y, si hay voz, se escucha.
- [ ] Modo oscuro/claro legibles; estados «bajo/alto» con texto; lector de pantalla anuncia resultados.
- [ ] El aviso «Casos ficticios…» y el aviso del plan siguen visibles.

### 10.4 Calidad de la retroalimentación (manual, con Ollama)

20 consultas por caso: el feedback **no** menciona medicamentos, dosis ni pruebas que no estén en las listas calculadas, y cita primero las alertas de seguridad cuando existen. Si falla, usar el feedback determinista sin narración.

---

## 11. Validación clínica: el requisito que lo bloquea todo

Este es el único punto que **no se puede resolver con código**. Sin un profesional que revise, los módulos B y C no deben activarse.

**Ficha de validación por caso** (se adjunta al campo `revision_clinica`):

1. ¿Los resultados de cada prueba listada son clínicamente coherentes con el caso?
2. ¿Hay alguna prueba del catálogo, no listada, que debería salir alterada? (Lo que cubre el `resultado_defecto`.)
3. ¿Las pruebas `esenciales`, `utiles` e `innecesarias` son las correctas para el primer nivel de atención?
4. ¿Los medicamentos `adecuados`, `aceptables` y `contraindicados` son correctos y su motivo está bien expresado?
5. ¿La disposición correcta y la aceptable son las adecuadas?
6. ¿Las tres ramas de evolución son verosímiles?
7. ¿Qué guía o fuente respalda el plan? (Registrarla en `fuente`.)

**Fuentes candidatas** (verificar licencia y vigencia antes de usarlas): guías clínicas del MINSAL, lista oficial de medicamentos del MINSAL y publicaciones de OPS/OMS. No copiar material con derechos de autor al repositorio: se resume y se cita.

---

## 12. Plan por fases

| Fase | Entrega | Esfuerzo | Depende de |
|---|---|---|---|
| **0. Contenido** | Catálogo de pruebas y resultados de los 8 casos; ficha de validación | ~1 día de redacción + revisión médica | — |
| **1. Backend de pruebas** | Catálogos, sesión, `/pruebas`, `revision_clinica`, validador | ~3 h | 0 |
| **2. Interfaz de pruebas** | Pestaña, contador, resultados, glosario | ~3 h | 1 |
| **3. Puntaje y resultados de pruebas** | Componente de pruebas, desglose, sección en resultados, retroalimentación | ~2 h | 1, 2 |
| **4. Plan** | `formulario.json`, `plan_esperado`, formulario de cierre, veredictos, alertas | ~1,5 días + médico | 3 |
| **5. Seguimiento narrado** | `evolucion`, evaluador de predicados, sección «Control», voz | ~3 h + redacción | 4 |
| **6. Control conversacional** | Continuar el chat con el paciente en la fecha de control | ~4 h | 5 |
| **7. Dosis** | Rangos validados en `formulario.json` y puntuación de dosis | A definir con médico | 4 |

### MVP recomendado para el hackathon: fases 0-3

Solo **pruebas**: catálogo de unas 12-16 pruebas, resultados validados para los casos que el médico alcance a revisar (los demás siguen sin módulo), puntaje y resultados. Es determinista, no depende del modelo y se ve muy bien en una demostración. Las fases 4-7 quedan como hoja de ruta.

---

## 13. Riesgos y mitigaciones

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Contenido clínico sin validar (resultados, planes). | Alta | **Alto** | Puerta `revision_clinica` (§4.5); sin `validado` no hay módulos. |
| `resultado_defecto` falso para una prueba omitida. | Media | Alto | Revisión explícita en la ficha; validador que impide listados incompletos. |
| La app se percibe como guía de prescripción real. | Media | Alto | Aviso educativo, sin puntuar dosis en la v1, catálogo corto. |
| El catálogo delata el diagnóstico. | Media | Alto | Catálogo único, amplio y con distractores; informes sin nombrar la enfermedad. |
| El modelo recomienda tratamiento en el feedback. | Media | Alto | Prompt acotado a listas calculadas; feedback determinista como respaldo. |
| El alcance crece y no se termina. | Alta | Alto | MVP = fases 0-3; el resto, hoja de ruta. |
| Mantenimiento: cada caso nuevo exige datos clínicos nuevos. | Alta | Medio | Plantilla y ficha de validación; validador estricto. |
| Cambiar los pesos descuadra el puntaje histórico. | Media | Medio | Reescalado y prueba de regresión; `version` del historial. |

---

## 14. Decisiones abiertas

1. **Alcance para el hackathon:** ¿solo pruebas (fases 0-3) o también plan?
2. **Quién valida:** ¿tienes un médico o docente que revise antes de activar los módulos?
3. **Contraindicado en Avanzado:** ¿impide aprobar (propuesta) o solo penaliza?
4. **Costos y presupuesto:** ¿visibles en Intermedio y Avanzado, o ocultos?
5. **Imágenes:** ¿informe en texto (propuesta) o radiografías reales? Las imágenes exigen una fuente con licencia abierta.
6. **Seguimiento:** ¿relato narrado (propuesta) o conversación con el paciente?
7. **Nivel de atención:** ¿escenario único de primer nivel o variar entre unidad de salud y hospital?
8. **Dosis:** ¿se puntúan en una versión futura o se dejan informativas?

---

## 15. Cómo hacer que lo implemente Codex

Convertir este documento en un prompt por fases, igual que `PROMPT_CODEX.md`. Recomendación: una fase por sesión, empezando por la **fase 1**, con la prueba de regresión del puntaje **antes** de tocar la interfaz. Al terminar cada fase, actualizar `AGENTS.md` (contratos de API y esquema de `casos.json`), `NIVELES.md` (nuevos bloques `modulos` y pesos) y el `README.md`.
