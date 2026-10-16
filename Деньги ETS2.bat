@echo off
rem Same as money.bat: change the money in ETS2 (double-click, the game must be closed).
rem Go to this folder first and call money.bat by a relative name: "call" expands the
rem percent and caret signs of a full path a second time, so a folder like 100%% or a^b
rem was not found (review 16.10.2026).
cd /d "%~dp0"
call ".\money.bat" %*
exit /b %ERRORLEVEL%
