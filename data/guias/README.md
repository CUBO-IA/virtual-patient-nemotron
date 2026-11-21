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
