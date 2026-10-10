@echo off
rem ETS2: change the money in the newest save. Double-click; the game must be closed.
rem The questions come from tools\money_menu.py (Russian, UTF-8 console).
rem Python: ETS2_PYTHON if set, else the project's .venv, else py -3, else python.
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PY=%ETS2_PYTHON%"
if not defined PY if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY (
  where py >nul 2>nul && set "PY=py -3"
)
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python не найден. Установите Python 3 с python.org ^(галочка "Add python.exe to PATH"^)
  echo и запустите этот файл ещё раз.
  set "RC=9"
  goto done
)
%PY% tools\money_menu.py %*
set "RC=%ERRORLEVEL%"
if "%RC%"=="3" (
  echo.
  echo Для зашифрованных сохранений нужен пакет pycryptodome:
  echo     %PY% -m pip install pycryptodome
)
:done
echo.
if not defined ETS2_NO_PAUSE pause
exit /b %RC%
