@echo off
setlocal

rem Folder where this script lives
set "SCRIPT_DIR=%~dp0"

rem Always run from the project root so relative paths work
cd /d "%SCRIPT_DIR%"

rem Ensure backend package (app.main) is importable
set "PYTHONPATH=%SCRIPT_DIR%backend;%PYTHONPATH%"

set "PYTHON_EXE="

rem Prefer the local virtual environment if it exists
if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
  set "PYTHON_EXE=%SCRIPT_DIR%\.venv\Scripts\python.exe"
) else (
  rem Fall back to the Windows Python launcher if available
  where py >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PYTHON_EXE=py"
  ) else (
    rem Finally, try plain python on PATH
    where python >nul 2>&1
    if %ERRORLEVEL%==0 (
      set "PYTHON_EXE=python"
    ) else (
      echo.
      echo Sikha could not find Python.
      echo Please install Python 3.10+ or create a .venv and try again.
      echo.
      pause
      exit /b 1
    )
  )
)

"%PYTHON_EXE%" "%SCRIPT_DIR%sikha_desktop.py"

endlocal
