# Guías Clínicas de Referencia (Fase 2 - RAG)

Este directorio aloja las guías clínicas oficiales para el módulo RAG de evaluación médica.

## Instrucciones

1. **Formatos soportados:** Archivos de texto o markdown (`.md`, `.txt`) o documentos PDF (`.pdf`).
2. **Nomenclatura obligatoria:** El nombre del archivo (sin la extensión) debe coincidir exactamente con el campo `guia_ref` del caso clínico correspondiente en `data/casos.json`.
   - Ejemplo: `dengue.md`, `erc.txt`, `dm2.pdf`, `hipertension.md`, `trauma.txt`, `gastroenteritis.md`, `neumonia.pdf`, `depresion.txt`.
3. **Licencia y procedencia:** Deben ser exclusivamente documentos públicos o de licencia abierta provenientes de fuentes oficiales de salud (por ejemplo, Ministerio de Salud de El Salvador - MINSAL, Organización Panamericana de la Salud - OPS/OMS). **No colocar material protegido por derechos de autor sin autorización.**
4. **Ingesta:** Para procesar e indexar los documentos en Chroma, ejecuta:
   ```powershell
   .\.venv\Scripts\python.exe scripts\ingest_guias.py
   ```
   Si no hay documentos en esta carpeta, el script de ingesta finalizará con un mensaje informativo claro sin arrojar errores.

## Fuentes usadas (los PDF no se suben a git; descárgalos de estos enlaces)

| `guia_ref` | Documento | Fuente |
|---|---|---|
| `erc` | Guía de manejo de enfermedad renal crónica estadios 1 al 3a, versión completa 2020 | MINSAL El Salvador, con INS y OPS: <https://docs.bvsalud.org/biblioref/2021/02/1147722/guia-erc-el-salvador-version-larga-27-01-21.pdf> |
| `gastroenteritis` | Nuevas recomendaciones para el tratamiento clínico de la diarrea (2006) | OPS: <https://paho.org/sites/default/files/si-diarrea.pdf> (enfoque pediátrico) |
| `depresion` | Guía de intervención mhGAP v2.0 | OPS/OMS: <https://www.paho.org/es/documentos/guia-intervencion-mhgap-para-trastornos-mentales-neurologicos-por-consumo-sustancias> |

| `neumonia` | Guías clínicas de Medicina Interna 2018, capítulo «Neumonía adquirida en la comunidad» (págs. 134-140 del PDF) | MINSAL El Salvador: <https://asp.salud.gob.sv/regulacion/pdf/guia/guia_clinica_medicina_interna_v1.pdf> |
| `hipertension` | Ídem, capítulo «Hipertensión arterial» (págs. 12-24 del PDF) | MINSAL El Salvador (mismo documento) |
| `dm2` | Ídem, capítulo «Diabetes mellitus» (págs. 181-188 del PDF) | MINSAL El Salvador (mismo documento) |

El libro completo se guarda en `data/guias_fuente/` (fuera de git y de la ingesta) y cada capítulo se extrae a su propio PDF (`neumonia.pdf`, `hipertension.pdf`, `dm2.pdf`) para que quede ligado a su caso. La vigencia de esta edición 2018 no está confirmada: el sitio del MINSAL también tiene una copia en su carpeta de documentos derogados.

Pendientes (si los consigues, guárdalos con el nombre indicado y vuelve a ejecutar la ingesta):

- `dengue.pdf`: Directrices para el diagnóstico clínico y el tratamiento del dengue, el chikunguña y el zika (OPS, 2022, CC BY-NC-SA 3.0 IGO): <https://iris.paho.org/handle/10665.2/55867>
- `trauma`: sin documento localizado.
