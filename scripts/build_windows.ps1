param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found at .venv\Scripts\python.exe"
}

Push-Location $ProjectRoot
try {
    & $VenvPython -m pip install --upgrade pip pyinstaller

    $args = @("-m", "PyInstaller", "--noconfirm", "SikhaAssistant.spec")
    if ($OneFile) {
        $args += "--onefile"
    }

    & $VenvPython @args
    Write-Host "Build complete. Check dist\\SikhaAssistant\\ or dist\\SikhaAssistant.exe"
}
finally {
    Pop-Location
}
