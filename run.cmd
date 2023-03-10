@echo off
IF NOT EXIST src/config.py GOTO errorNoConfigFile
python --version 2>NUL
IF errorlevel 1 GOTO errorNoPython

GOTO noError

:noError
pip install -r ./requirments.txt
python ./src/__main__.py
PAUSE
exit

:errorNoPython
ECHO.
ECHO Error^: Python not installed
exit

:errorNoConfigFile
ECHO.
ECHO Error^: no file config.py
exit