# Más datos del dataset en la tarjeta del paciente (y crédito de la licencia)

Instrucciones para un agente (Codex). Lee este archivo completo, además de `AGENTS.md`, antes de tocar código. Es un cambio **pequeño y seguro**: no toca el prompt del paciente ni la evaluación.

- **Objetivo:** que «Ver paciente» muestre más información real de la persona del dataset (estado civil, escolaridad y tipo de hogar) y que la licencia del dataset quede visible.
- **Por qué:** hoy se usan 8 de las 25 columnas de `nvidia/Nemotron-Personas-El-Salvador`; la tarjeta solo enseña nombre, edad, ocupación y procedencia. Estos tres datos ya existen en el dataset y le dan más carácter a cada paciente en la demostración.
- **Estado:** propuesta; nada implementado.

---

## 1. Qué hay hoy

| Dato | ¿Está en `data/personas.json`? | ¿Llega a la interfaz? |
|---|---|---|
| `estado_civil` (`union_libre`, `soltero`, `casado`, `separado`, `viudo`, `divorciado`) | Sí | No |
| `nivel_educativo` (`ninguno`, `primaria`, `secundaria`, `bachillerato`, `tecnico`, `universitario`, `posgrado`) | Sí | No |
| `household_type` del dataset (`nuclear`, `pareja`, `extendido`, `monoparental`, …) | **No** | No |
| `uuid` del dataset | **No** | No |

La respuesta de `POST /api/sessions` (en `main.py`, en las dos ramas: consulta y urgencias) incluye en `paciente`: `nombre, edad, sexo, ocupacion, departamento, municipio, avatar_url, habla`. `PatientCard.jsx` pinta Nombre, Edad, Ocupación y Procedencia.

---

## 2. Qué hacer, por fases

Termina y verifica cada fase antes de pasar a la siguiente.

### Fase 1 — Añadir `hogar` y `uuid` a las personas existentes (sin cambiar a nadie)

`personas.json` se generó leyendo el dataset en streaming con `shuffle(seed=42, buffer_size=2000)` y los filtros de `scripts/build_personas.py`. **Ese orden es reproducible** (se comprobó: las 6 primeras personas salen idénticas). Aprovéchalo:

1. Crea `scripts/enriquecer_personas.py`. Debe leer el dataset **con exactamente el mismo shuffle y los mismos filtros** que `build_personas.py` (importa y reutiliza `SEED`, `extract_name`, el filtro de edad ≥ 18 y de sexo; no copies la lógica).
2. Para cada persona aceptada, en orden, comprueba contra `personas.json` que **coinciden `nombre`, `edad` y `municipio`**. Si alguna no coincide, **aborta sin escribir nada** y explica cuál falló.
3. Si todas coinciden, añade a cada persona `uuid` y `hogar` (valor de `household_type`, en minúsculas; `null` si no viene). **No cambies ningún otro campo, ni el orden, ni los `id`.**
4. Escribe de forma atómica (archivo temporal y reemplazo). Imprime cuántas personas se actualizaron y la distribución de `hogar`.
5. Necesita internet; si falla la descarga, termina con un mensaje claro y deja `personas.json` intacto.
6. Actualiza `build_personas.py` para que **también** guarde `uuid` y `hogar` cuando se regenere (así un clon nuevo queda igual).

No toques `personas.json` a mano (`AGENTS.md` §9): solo mediante el script.

### Fase 2 — Exponer los datos (contrato de la API)

En `POST /api/sessions`, en **ambas ramas**, añade a `paciente`: `estado_civil`, `nivel_educativo` y `hogar`. Son datos de la persona, no del caso: **no revelan nada oculto**. Usa `persona.get(...)` (el `hogar` puede faltar en una instalación antigua) y devuelve `null` cuando no exista.

Actualiza `AGENTS.md` §5 (tabla de API) en el mismo cambio: «`paciente` incluye `estado_civil`, `nivel_educativo`, `hogar`».

### Fase 3 — Mostrarlos en la tarjeta

En `PatientCard.jsx`, añade tres filas debajo de «Ocupación»: **Estado civil**, **Escolaridad**, **Hogar**. Reglas:

- Traducciones a texto natural **en un solo lugar** (un objeto en el componente o en un archivo `frontend/src/etiquetas.js`):
  - Estado civil (según el sexo del paciente, `paciente.sexo`): `soltero` → Soltero/Soltera · `casado` → Casado/Casada · `union_libre` → Unión libre · `separado` → Separado/Separada · `viudo` → Viudo/Viuda · `divorciado` → Divorciado/Divorciada.
  - Escolaridad: `ninguno` → Sin estudios · `primaria` → Primaria · `secundaria` → Secundaria · `bachillerato` → Bachillerato · `tecnico` → Técnico · `universitario` → Universitario · `posgrado` → Posgrado.
  - Hogar: `nuclear` → Con pareja e hijos · `pareja` → Con su pareja · `extendido` → Con familia extendida · `monoparental` → Con hijos, sin pareja. Para **cualquier valor que no esté en el mapa**, muestra el texto original con la primera letra en mayúscula (el dataset puede traer valores que no se vieron en la muestra).
- Si un dato es `null` o vacío, **no pintes esa fila** (nada de «null» ni «undefined»).
- No muestres `estilo`, `habla` ni nada del caso.
- Mantén el estilo del `<dl>` actual; que se lea bien en pantallas estrechas (la tarjeta ya es angosta: etiquetas cortas).

### Fase 4 — Crédito de la licencia

El dataset es **CC BY 4.0** y exige atribución. Hoy la diapositiva solo dice «NVIDIA Nemotron-Personas-El-Salvador».

- En `frontend/src/intro/Diapositivas.jsx`, en la segunda diapositiva (debajo de la nota existente), añade una línea discreta: «Personas basadas en NVIDIA Nemotron‑Personas‑El‑Salvador (licencia CC BY 4.0). Los casos clínicos son ficticios.» con enlace a `https://huggingface.co/datasets/nvidia/Nemotron-Personas-El-Salvador` (`target="_blank"` y `rel="noopener noreferrer"`).
- El README ya tiene «Créditos y licencias»; solo verifica que dice CC BY 4.0 y enlaza el dataset.

### Fase 5 — Pruebas

En `backend/tests/` (sin red):

- `POST /api/sessions` (consulta **y** urgencias) devuelve `paciente.estado_civil`, `nivel_educativo` y `hogar` (este puede ser `null`), y **sigue sin** devolver `diagnostico`, `lista_verificacion`, `datos_si_pregunta`, `banderas_rojas` ni nada de `urgencia` (la prueba existente `test_no_leak.py` debe seguir pasando).
- `enriquecer_personas`: con un dataset simulado, (a) añade `uuid` y `hogar` sin cambiar los demás campos; (b) **aborta y no escribe** si una persona no coincide. Extrae la lógica a una función pura para poder probarla sin descargar nada.
- La suite completa (`pytest backend\tests -q`) y `npm run build` siguen pasando.

**Manual** (en el navegador): «Ver paciente» muestra las tres filas nuevas, sin «null», con el género correcto (p. ej. «Casada» para una mujer); la diapositiva 2 muestra el crédito y el enlace abre el dataset.

---

## 3. Reglas

- No cambies el prompt del paciente, la evaluación ni el puntaje.
- Contrato de API: solo se **añaden** campos; actualiza `AGENTS.md` en el mismo cambio.
- Sin dependencias nuevas. Texto de interfaz en español. No toques `.env`. Sin commit.
- `personas.json` solo se modifica con el script (y sin cambiar `id`, nombres ni orden).
- Si algo de este documento contradice `AGENTS.md`, sigue `AGENTS.md` y avísalo.

## 4. Criterios de aceptación

- [ ] `personas.json` tiene `uuid` y `hogar` en las 150 personas, y todo lo demás está idéntico.
- [ ] `POST /api/sessions` incluye `estado_civil`, `nivel_educativo` y `hogar` en ambas ramas.
- [ ] La tarjeta muestra Estado civil, Escolaridad y Hogar, sin filas vacías ni «null».
- [ ] La diapositiva 2 incluye la atribución CC BY 4.0 con enlace.
- [ ] `pytest backend\tests -q` y `npm run build` pasan; `AGENTS.md` actualizado.

## 5. Qué entregar

Resumen corto: qué cambiaste por fase y en qué archivos, la distribución de `hogar` que imprimió el script, y qué no pudiste verificar (por ejemplo, si no hubo internet para correr el script).
