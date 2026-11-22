@echo off
REM Igual que iniciar.bat, pero el backend se recarga solo al cambiar codigo en backend\.
REM Las sesiones se guardan en disco (.sesiones\), asi que una recarga no corta las consultas en curso.
call "%~dp0iniciar.bat" dev
