@echo off
rem Same as money.bat: change the money in ETS2 (double-click, the game must be closed).
call "%~dp0money.bat" %*
exit /b %ERRORLEVEL%
