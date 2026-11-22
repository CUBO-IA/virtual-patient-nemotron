# Mejorar la detección de preguntas del estudiante

Instrucciones para un agente (Codex). Lee este archivo completo, además de `AGENTS.md`, antes de tocar código.

- **Problema:** el estudiante pregunta algo y el sistema lo marca como «no preguntado», tanto en la **guía de anamnesis** (Nivel 1, en vivo) como en la **evaluación final** («Lo que faltó»).
- **Causa:** el detector solo reconoce palabras clave por *inicio exacto de palabra*, y a las claves les faltan sinónimos y modismos.
- **Objetivo:** que el sistema reconozca las formas naturales de preguntar cada tema (incluidos los modismos salvadoreños), sin marcar de más, y que esa mejora **se pueda medir** y no se rompa después.
- **Estado:** propuesta aprobada; nada implementado todavía.

---

## 1. Dónde está el problema en el código

Todo pasa por una sola función, así que arreglarla corrige todo a la vez:

| Pieza | Archivo | Qué hace |
|---|---|---|
| `norm(text)` | `backend/app/evaluate.py` | Minúsculas, sin tildes, solo `[a-z0-9]`, con un espacio a cada lado. |
| `_hit(keywords, texto)` | `backend/app/evaluate.py` | `True` si alguna clave, normalizada, aparece como **inicio de palabra** en el texto del estudiante. **Es lo que hay que mejorar.** |
| Evaluación final | `evaluate.evaluar` | Marca cada ítem de `lista_verificacion` y de `banderas_rojas` con `_hit`. |
| Guía de anamnesis en vivo | `niveles.calcular_guia_cubierta` | Usa `_hit` con `data/anamnesis_guia.json`. |
| Pistas | `main.py` (`/pista`) | Usa `_hit` para saber qué tema falta por preguntar. |

Los datos: `data/casos.json` (`lista_verificacion[].keywords`, `banderas_rojas[].keywords`) y `data/anamnesis_guia.json` (`items[].keywords`).

---

## 2. Línea base medida (no la empeores)

Preguntas realistas de un estudiante contra las claves actuales. «Cruces falsos» = preguntas de **otro** tema que marcan este tema por error.

| | Detecta | Cruces falsos |
|---|---|---|
| Gastroenteritis (7 temas, 38 preguntas) | **63 %** | 2,2 % |
| Guía de anamnesis (9 temas, 45 preguntas) | **55 %** | 0,3 % |

Causas observadas:

1. **Flexión de la palabra.** La clave `mejora` no reconoce «¿hay algo que lo **mejore**?»; `familiar` no reconoce «su **familia**»; `operaci` no reconoce «le han **operado**».
2. **Faltan sinónimos y modismos.** `cursera`, `arrojar`, `evacúa`, `popó`, «¿se ha sentido **caliente**?», «boca **reseca**», «¿a qué se **dedica**?», «¿**se tomó algo** para esto?».
3. **Contracciones.** La clave `de 1 a 10` no reconoce «**del 1 al 10**».

Un prototipo mostró que comparar por raíz sube poco (63 → 68 % y 55 → 71 %) y que **los sinónimos y modismos son lo que más mueve el resultado** (≈100 % en esas mismas preguntas, **pero con sobreajuste**: los sinónimos se escribieron mirando esas preguntas). Por eso este plan exige un conjunto de preguntas **reservado** (§5).

---

## 3. Qué hacer, por fases

Termina y verifica cada fase antes de pasar a la siguiente.

### Fase 1 — Motor de detección

Reescribe `_hit` en `evaluate.py` manteniendo **la misma firma** `_hit(keywords: list[str], texto: str) -> bool` (`texto` ya viene normalizado con `norm`), de modo que `niveles.py`, `main.py` y `evaluate.py` no cambien.

**Regla de oro: nunca se pierde una coincidencia que hoy existe.** El comportamiento actual (inicio de palabra) se conserva como base y se **añaden** dos mecanismos. Así el detector solo puede detectar más, nunca menos.

1. **Tokenización por palabras.** Una clave de varias palabras debe coincidir con palabras consecutivas del texto.
2. **Equivalencias de contracción** a nivel de token, en el texto y en las claves: `del → de`, `al → a`. Con esto «del 1 al 10» coincide con la clave `de 1 a 10`.
3. **Coincidencia por raíz** para cada par de tokens (clave, texto), además del inicio de palabra:
   - Se quita el sufijo más largo de una lista (`amientos, imientos, amiento, imiento, aciones, iciones, acion, icion, ando, iendo, ados, idos, adas, idas, ado, ido, ada, ida, ar, er, ir, es, as, os, an, en, a, e, o, s`), dejando una raíz de **al menos 4 letras**.
   - Dos tokens coinciden si ambas raíces miden ≥ 4 y **una es prefijo de la otra** y su diferencia de largo es ≤ 4.
   - Palabras de 4 letras o menos solo coinciden por el comportamiento actual (inicio de palabra), para no multiplicar los falsos positivos.

Implementación de referencia (la usada en el prototipo; ajústala si lo ves necesario):

```python
SUFIJOS = ["amientos", "imientos", "amiento", "imiento", "aciones", "iciones", "acion", "icion",
           "ando", "iendo", "ados", "idos", "adas", "idas", "ado", "ido", "ada", "ida",
           "ar", "er", "ir", "es", "as", "os", "an", "en", "a", "e", "o", "s"]
EQUIV = {"del": "de", "al": "a"}


def _raiz(w: str) -> str:
    if len(w) <= 4:
        return w
    for s in SUFIJOS:
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[: -len(s)]
    return w


def _tok_coincide(k: str, t: str) -> bool:
    if k == t or t.startswith(k):                      # comportamiento actual
        return True
    rk, rt = _raiz(k), _raiz(t)
    return len(rk) >= 4 and len(rt) >= 4 and abs(len(rk) - len(rt)) <= 4 and (rk.startswith(rt) or rt.startswith(rk))


def _hit(keywords, texto):
    palabras = [EQUIV.get(p, p) for p in texto.split()]
    for k in keywords:
        clave = [EQUIV.get(p, p) for p in norm(k).split()]
        if clave and any(
            all(_tok_coincide(clave[j], palabras[i + j]) for j in range(len(clave)))
            for i in range(len(palabras) - len(clave) + 1)
        ):
            return True
    return False
```

**Pruebas de la fase** (en `backend/tests/test_deteccion.py`):

- Todo lo que detectaba antes sigue detectándose (regresión sobre las claves y preguntas actuales).
- `mejore`↔`mejora`, `familia`↔`familiar`, `operado`↔`operaci`, `evacúa`↔`evacuaciones`, `del 1 al 10`↔`de 1 a 10`.
- Palabras cortas (4 letras o menos) siguen coincidiendo solo por inicio de palabra, como hoy: la clave `sed` coincide con «sed» (y, como ya ocurría, también con «sedante»). Documenta ese comportamiento con una prueba y no lo empeores.
- Rendimiento: 1000 llamadas con un texto de 500 palabras en menos de 1 s.

### Fase 2 — Banco de preguntas realistas

Crea `data/preguntas_ejemplo.json`. Es la **fuente de verdad** para medir y para tus pruebas.

```json
{
  "version": 1,
  "guia": {
    "motivo": { "desarrollo": ["¿Qué le trae por aquí?", "…"], "reserva": ["…"] }
  },
  "casos": {
    "c_gea_01": {
      "heces_frecuencia": { "desarrollo": ["…"], "reserva": ["…"] }
    }
  }
}
```

Reglas del banco:

- **Cobertura:** todos los temas de `anamnesis_guia.json` y **todos** los ítems de `lista_verificacion` y `banderas_rojas` de los **8 casos**.
- **Por tema:** ≥ 5 preguntas de **desarrollo** (con las que ajustas las claves) y ≥ 3 de **reserva** (que **no** miras al ajustar; solo sirven para medir). Sin reserva no hay forma de saber si hay sobreajuste.
- **Variedad:** de cada tema, preguntas **directas**, **indirectas**, con **modismos salvadoreños** («cursera», «arrojar», «calentura», «cuerpo cortado», «pastillas», «ir al baño»), con y sin tildes, y en forma de afirmación («Cuénteme cómo van sus evacuaciones»).
- **No copies** el texto de `datos_si_pregunta` ni de las pistas: debe parecerse a lo que diría un estudiante.
- Usa el glosario `data/habla_salvadorena.json` como inspiración para los modismos (es un **borrador sin validar**: úsalo solo para reconocer lo que diga el estudiante).
- **Semilla** (ya medida). Está en un formato simplificado (preguntas por tema, sin separar desarrollo y reserva; el caso `c_gea_01` va aparte). Conviértela al formato de arriba (`guia` y `casos.c_gea_01`), amplíala y repártela en desarrollo y reserva:

```json
{
  "guia": {
    "motivo": ["¿Qué le trae por aquí?", "Cuénteme, ¿qué le pasa?", "¿Cuál es el problema?", "¿En qué le puedo ayudar?", "¿Cómo se ha sentido?"],
    "inicio": ["¿Desde cuándo está así?", "¿Cuándo empezó todo esto?", "¿Hace cuánto le pasa?", "¿Cuántos días lleva con eso?", "¿Cómo fue que empezó?"],
    "intensidad": ["¿Qué tan fuerte es el dolor?", "Del 1 al 10, ¿cuánto le duele?", "¿Cómo es el dolor, punzante o sordo?", "¿Es muy intenso?", "¿Cuántas veces al día le pasa?"],
    "factores": ["¿Hay algo que lo mejore?", "¿Qué le alivia?", "¿Con qué se le calma?", "¿Algo lo empeora?", "¿Se le pasa cuando descansa?"],
    "asociados": ["¿Ha sentido algo más?", "¿Algún otro síntoma?", "¿Y también tiene fiebre o náuseas?", "¿Le acompaña otra molestia?", "¿Se ha sentido de otra manera?"],
    "antecedentes": ["¿Tiene alguna enfermedad crónica?", "¿Le han operado alguna vez?", "¿Es alérgico a algo?", "¿Ha estado hospitalizado?", "¿Padece de presión o azúcar?"],
    "familiares": ["¿Alguien en su familia tiene diabetes?", "¿Su mamá o su papá han tenido algo parecido?", "¿Hay enfermedades en su familia?", "¿Sus papás padecen de algo?", "¿Algún hermano con esto?"],
    "medicinas": ["¿Está tomando algún medicamento?", "¿Se ha tomado alguna pastilla?", "¿Qué medicinas usa?", "¿Toma algo para eso?", "¿Usa algún remedio?"],
    "habitos": ["¿Fuma o toma?", "¿A qué se dedica?", "¿Cómo es su alimentación?", "¿Hace ejercicio?", "¿Con quién vive?"]
  },
  "c_gea_01": {
    "heces_frecuencia": ["¿Cuántas veces ha ido al baño hoy?", "¿Cómo son sus heces, líquidas?", "¿Ha tenido cursera?", "¿Con qué frecuencia evacúa?", "¿Ha estado suelto del estómago?", "¿Cómo es la popó?"],
    "sangre_moco": ["¿Ha visto sangre en las heces?", "¿Le ha salido sangre al ir al baño?", "¿Hay moco cuando evacúa?", "¿Las heces son de color rojo o negro?", "¿Ha notado algo raro en las heces, como moquito o sangre?"],
    "vomitos_tolerancia": ["¿Ha vomitado?", "¿Cuántas veces ha arrojado?", "¿Puede tomar líquidos sin devolverlos?", "¿Le cae mal todo lo que come?", "¿Aguanta el agua o la vomita?"],
    "signos_deshidratacion": ["¿Tiene mucha sed?", "¿Tiene la boca reseca?", "¿Ha orinado poco hoy?", "¿Cómo está de orina, oscura?", "¿Se siente mareado al pararse?"],
    "origen_alimentos": ["¿Qué comió antes de enfermarse?", "¿Comió algo en la calle?", "¿Toma agua de chorro?", "¿Ha comido algo en mal estado?", "¿Alguien más de su familia comió lo mismo y se enfermó?", "¿Qué almorzó ayer?"],
    "fiebre": ["¿Ha tenido fiebre?", "¿Se ha sentido caliente?", "¿Siente escalofríos?", "¿Le ha dado calentura?", "¿Se tomó la temperatura?"],
    "tratamiento_previo": ["¿Se ha tomado algo para esto?", "¿Ha tomado suero?", "¿Ha tomado alguna medicina?", "¿Se automedicó?", "¿Tomó algún antibiótico?", "¿Se ha tomado alguna pastilla?"]
  }
}
```

Crea también `scripts/medir_deteccion.py`, que imprime, para la guía y cada caso: detección sobre **desarrollo**, detección sobre **reserva** y **cruces falsos**, y lista las preguntas no detectadas. Es la herramienta con la que ajustas y con la que reportas al final.

### Fase 3 — Sinónimos y modismos en los datos

Amplía `keywords` en `data/anamnesis_guia.json` y en `lista_verificacion` y `banderas_rojas` de **los 8 casos** de `data/casos.json`, **ajustando solo con las preguntas de desarrollo**.

Cómo escribir claves:

- Prefiere **raíces** (`mejor`, `famili`, `operad`, `arroj`, `evacu`) en lugar de una sola forma de la palabra.
- Añade **sinónimos y modismos**: `cursera`, `suelto del estomago`, `popo`, `al bano`, `arroj`, `caliente`, `reseca`, `se dedica`, `se tomo algo`, `automedic`…
- Añade variantes de **frase** cuando la palabra sola sería ambigua («le cae mal», «se le pasa», «en mal estado»).
- Evita claves **muy genéricas** que marquen temas ajenos (`algo`, `tambien`, `mas`, `cuando`): si hace falta, úsalas dentro de una frase.
- Cada tema debe seguir **sin nombrar el diagnóstico** (el validador ya revisa los textos; no metas el nombre de la enfermedad en una clave).
- **No elimines** claves existentes.

Punto de partida sugerido (afinado con la semilla; verifícalo con la reserva y recórtalo si produce cruces falsos):

```text
heces_frecuencia   + cursera, evacu, suelto del estomago, popo, al bano
sangre_moco        + rojo, negro, moquito
vomitos_tolerancia + arroj, le cae mal, aguanta, nausea
signos_deshidrat.  + reseca, mareo, mareado, orin
origen_alimentos   + mal estado, almorz, cen, desayun, que comio
fiebre             + caliente, escalofri, termometro
tratamiento_previo + se ha tomado algo, automedic, toma algo, se tomo algo
guía.motivo        + cual es el problema, en que le puedo ayudar, como se ha sentido, que molestia, que tiene
guía.inicio        + como fue que empezo, empez, cuantos dias, hace cuanto, desde cuando
guía.intensidad    + del 1 al 10, 1 al 10, muy fuerte, intens, cuantas veces al dia, con que frecuencia, punzante
guía.factores      + mejor, alivi, empeor, calma, se le pasa, descans
guía.asociados     + algo mas, otra molestia, otro sintoma, de otra manera, alguna otra
guía.antecedentes  + cronic, operad, alergic, hospitaliz, padece
guía.familiares    + famili, hermano, papas, abuel, heredit, mama, papa
guía.medicinas     + toma algo, remedio, medicament, pastilla, tratamiento
guía.habitos       + se dedica, alimentacion, trabaj, vive, ejercicio, fuma, alcohol
```

Para los otros 7 casos no hay sinónimos hechos: escríbelos tú siguiendo estas reglas y el banco que armaste.

### Fase 4 — Pruebas de calidad

En `backend/tests/test_deteccion.py`, que leen `data/preguntas_ejemplo.json`:

- **Detección en desarrollo ≥ 95 %** para la guía y para cada caso.
- **Detección en reserva ≥ 80 %** para la guía y para cada caso (si no llega, amplía sinónimos con criterio, **no** copies las preguntas de reserva a las claves).
- **Cruces falsos ≤ 5 %** (una pregunta de otro tema no debe marcar este tema), por caso y para la guía.
- **Regresión:** cada clave que existía antes sigue en la lista; nada de lo detectado antes deja de detectarse.
- La suite actual (`pytest backend\tests -q`) sigue pasando completa, y `scripts\validate_casos.py` sigue en verde.

### Fase 5 (opcional) — Transparencia

Solo si las anteriores están terminadas:

- En la respuesta de `/finish`, añade `cumplidos_detalle: [{"texto": "…", "pregunta": "«¿Ha tenido fiebre?»"}]` con la pregunta del estudiante que cubrió cada tema (aditivo; no quites `cumplidos`).
- En `Results.jsx`, muestra bajo cada tema cubierto la pregunta que lo cubrió, y en «Lo que faltó» un texto discreto: «No detecté ninguna pregunta sobre este tema».
- Endpoint `POST /api/sessions/{id}/reporte-deteccion` con `{item_id, mensaje}` que añade una línea JSON a `informes/falsos_negativos.jsonl` (carpeta local, no se sube). Sirve para que tu compañero o un docente reporten preguntas que el sistema no reconoció y se agreguen al banco.

### Fuera de alcance (no lo hagas ahora)

- Una capa con el modelo (el 7B revisando los temas no detectados). Se evaluará después con datos del banco; no funciona en modo vista previa y puede marcar de más.
- Cambiar la forma en que se calcula el puntaje.

---

## 4. Reglas

- **Conserva la firma** de `_hit` y el contrato de la API. Si añades campos a `/finish`, que sean opcionales y se documenten en `AGENTS.md`.
- **No cambies** las reglas del prompt del paciente ni el puntaje.
- **No toques** `data/personas.json`, `.env` ni `data/habla_salvadorena.json`.
- **No pongas el diagnóstico** (ni sus alias) dentro de una clave, y no copies el texto de las respuestas del paciente a las claves.
- **No inventes contenido clínico.** Las claves reconocen preguntas; no añaden hechos médicos.
- Todo el texto en español.
- Haz cambios pequeños y verifica cada uno; no hagas commit.

---

## 5. Criterios de aceptación

- [ ] `_hit` cumple la fase 1 y es la única lógica de detección (guía, evaluación y pistas la comparten).
- [ ] `data/preguntas_ejemplo.json` cubre la guía y los 8 casos, con ≥ 5 de desarrollo y ≥ 3 de reserva por tema.
- [ ] `python scripts\medir_deteccion.py` imprime los números y las preguntas no detectadas.
- [ ] Desarrollo ≥ 95 %, **reserva ≥ 80 %**, cruces falsos ≤ 5 %, en la guía y en cada caso.
- [ ] Ninguna clave existente fue eliminada; ninguna contiene el diagnóstico.
- [ ] `pytest backend\tests -q` (todas), `scripts\validate_casos.py` y `npm run build` pasan.
- [ ] `AGENTS.md` actualizado con una nota breve sobre el detector por raíz, el banco y cómo medir.

---

## 6. Qué entregar

Un resumen corto con:

1. Qué cambiaste por fase y en qué archivos.
2. La **tabla antes/después** de `medir_deteccion.py` (desarrollo, **reserva**, cruces falsos) para la guía y cada caso.
3. Los temas donde la **reserva** quedó por debajo de 80 % y por qué.
4. Cualquier clave que hayas tenido que **recortar** por producir cruces falsos.
5. Qué no pudiste verificar.

Si algo de este documento contradice `AGENTS.md`, sigue `AGENTS.md` y avísalo.
