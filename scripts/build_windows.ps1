param(
    [switch]$OneFile,
    [switch]$Installer
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
    Write-Host "App build complete. Check dist\\SikhaAssistant.exe"

    if ($Installer) {
        $iscc = Get-Command iscc -ErrorAction SilentlyContinue
        if (-not $iscc) {
            throw "Inno Setup Compiler (iscc) is not installed. Install Inno Setup, then rerun with -Installer."
        }

        & $iscc.Source "installer\\SikhaAssistant.iss"
        Write-Host "Installer build complete. Check dist\\installer\\SikhaAssistantSetup.exe"
    }
}
finally {
    Pop-Location
}
