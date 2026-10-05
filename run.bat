@echo off
setlocal
cd /d "%~dp0"
if not defined PYTHON set "PYTHON=.venv\Scripts\python.exe"
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
"%PYTHON%" -m practice23 %*
