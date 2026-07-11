@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ============================================================================
:: Rakshastra Agent — Windows Installer
:: ============================================================================
:: Automated setup for the Rakshastra Autonomous Cyber Defense Platform.
:: Checks prerequisites, creates a virtual environment, installs dependencies,
:: configures .env, sets up PATH, and launches the GUI setup wizard.
::
:: Usage:
::   install-rakshastra.bat
::
:: This script:
::   1. Checks/installs Python 3.11+, Git, Node.js 20+, uv
::   2. Creates a Python virtual environment (.venv)
::   3. Installs all dependencies via uv (hash-verified)
::   4. Creates .env from template
::   5. Syncs bundled skills
::   6. Adds rakshastra to user PATH
::   7. Launches the GUI setup wizard for API key configuration
:: ============================================================================

:: ── Colors (ANSI escape sequences) ─────────────────────────────────────────
set "ESC="
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "CYAN=%ESC%[96m"
set "YELLOW=%ESC%[93m"
set "GOLD=%ESC%[33m"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[2m"
set "RESET=%ESC%[0m"

:: ── Resolve script directory ───────────────────────────────────────────────
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

:: ── Log file ───────────────────────────────────────────────────────────────
set "LOG_FILE=%SCRIPT_DIR%\install.log"
echo [%date% %time%] Rakshastra installer started > "%LOG_FILE%"

:: ── Banner ─────────────────────────────────────────────────────────────────
cls
echo.
echo %GOLD%  ╔══════════════════════════════════════════════════════════════╗%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%██████╗  %GOLD%█████╗ %RED%██╗  ██╗%GOLD%███████╗%RED%██╗  ██╗%GOLD% █████╗ %RED%███████╗%RESET%  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%██╔══██╗%GOLD%██╔══██╗%RED%██║ ██╔╝%GOLD%██╔════╝%RED%██║  ██║%GOLD%██╔══██╗%RED%██╔════╝%RESET%  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%██████╔╝%GOLD%███████║%RED%█████╔╝ %GOLD%███████╗%RED%███████║%GOLD%███████║%RED%███████╗%RESET%  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%██╔══██╗%GOLD%██╔══██║%RED%██╔═██╗ %GOLD%╚════██║%RED%██╔══██║%GOLD%██╔══██║%RED%╚════██║%RESET%  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%██║  ██║%GOLD%██║  ██║%RED%██║  ██╗%GOLD%███████║%RED%██║  ██║%GOLD%██║  ██║%RED%███████║%RESET%  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%╚═╝  ╚═╝%GOLD%╚═╝  ╚═╝%RED%╚═╝  ╚═╝%GOLD%╚══════╝%RED%╚═╝  ╚═╝%GOLD%╚═╝  ╚═╝%RED%╚══════╝%RESET%  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%████████╗%GOLD%██████╗  %RED% █████╗ %RESET%                                %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %RED%╚══██╔══╝%GOLD%██╔══██╗%RED%██╔══██╗%RESET%                                %GOLD%║%RESET%
echo %GOLD%  ║%RESET%      %RED%██║   %GOLD%██████╔╝%RED%███████║%RESET%                                %GOLD%║%RESET%
echo %GOLD%  ║%RESET%      %RED%██║   %GOLD%██╔══██╗%RED%██╔══██║%RESET%                                %GOLD%║%RESET%
echo %GOLD%  ║%RESET%      %RED%██║   %GOLD%██║  ██║%RED%██║  ██║%RESET%                                %GOLD%║%RESET%
echo %GOLD%  ║%RESET%      %RED%╚═╝   %GOLD%╚═╝  ╚═╝%RED%╚═╝  ╚═╝%RESET%                                %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %DIM%Autonomous Cyber Defense Platform — Windows Installer%RESET%     %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ╚══════════════════════════════════════════════════════════════╝%RESET%
echo.

:: ============================================================================
:: STEP 1: Check Prerequisites
:: ============================================================================

echo %CYAN%[1/7]%RESET% %BOLD%Checking prerequisites...%RESET%
echo.

set "PREREQ_FAIL=0"

:: ── Python ──────────────────────────────────────────────────────────────────
set "PYTHON_CMD="
set "PYTHON_OK=0"

:: Try python3 first, then python
for %%P in (python3 python) do (
    if "!PYTHON_CMD!"=="" (
        where %%P >nul 2>&1
        if !errorlevel!==0 (
            for /f "tokens=2 delims= " %%V in ('%%P --version 2^>^&1') do (
                for /f "tokens=1,2 delims=." %%A in ("%%V") do (
                    if %%A GEQ 3 if %%B GEQ 11 (
                        set "PYTHON_CMD=%%P"
                        set "PYTHON_VER=%%V"
                        set "PYTHON_OK=1"
                    )
                )
            )
        )
    )
)

if "!PYTHON_OK!"=="1" (
    echo   %GREEN%✓%RESET% Python !PYTHON_VER! found
    echo [OK] Python !PYTHON_VER! >> "%LOG_FILE%"
) else (
    echo   %RED%✗%RESET% Python 3.11+ not found
    echo   %DIM%  Install from: https://www.python.org/downloads/%RESET%
    echo   %DIM%  Or run: winget install Python.Python.3.11%RESET%
    echo [FAIL] Python 3.11+ not found >> "%LOG_FILE%"
    set "PREREQ_FAIL=1"
)

:: ── Git ─────────────────────────────────────────────────────────────────────
where git >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=3 delims= " %%V in ('git --version 2^>^&1') do set "GIT_VER=%%V"
    echo   %GREEN%✓%RESET% Git !GIT_VER! found
    echo [OK] Git !GIT_VER! >> "%LOG_FILE%"
) else (
    echo   %YELLOW%⚠%RESET% Git not found %DIM%(optional — needed for updates)%RESET%
    echo [WARN] Git not found >> "%LOG_FILE%"
)

:: ── Node.js ─────────────────────────────────────────────────────────────────
set "NODE_OK=0"
where node >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=1 delims=v" %%V in ('node --version 2^>^&1') do (
        for /f "tokens=1 delims=." %%M in ("%%V") do (
            if %%M GEQ 20 set "NODE_OK=1"
        )
    )
    if "!NODE_OK!"=="1" (
        for /f %%V in ('node --version 2^>^&1') do set "NODE_VER=%%V"
        echo   %GREEN%✓%RESET% Node.js !NODE_VER! found
        echo [OK] Node.js !NODE_VER! >> "%LOG_FILE%"
    ) else (
        echo   %YELLOW%⚠%RESET% Node.js 20+ recommended %DIM%(found older version)%RESET%
        echo [WARN] Node.js older than 20 >> "%LOG_FILE%"
    )
) else (
    echo   %YELLOW%⚠%RESET% Node.js not found %DIM%(optional — needed for TUI/dashboard)%RESET%
    echo [WARN] Node.js not found >> "%LOG_FILE%"
)

:: ── uv ──────────────────────────────────────────────────────────────────────
set "UV_CMD="
where uv >nul 2>&1
if %errorlevel%==0 (
    set "UV_CMD=uv"
) else (
    if exist "%USERPROFILE%\.local\bin\uv.exe" (
        set "UV_CMD=%USERPROFILE%\.local\bin\uv.exe"
    ) else if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
        set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
    )
)

if defined UV_CMD (
    for /f %%V in ('!UV_CMD! --version 2^>^&1') do set "UV_VER=%%V"
    echo   %GREEN%✓%RESET% uv !UV_VER! found
    echo [OK] uv !UV_VER! >> "%LOG_FILE%"
) else (
    echo   %CYAN%→%RESET% uv not found — installing...
    echo [INFO] Installing uv >> "%LOG_FILE%"

    :: Try PowerShell install
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >> "%LOG_FILE%" 2>&1
    
    :: Check again
    where uv >nul 2>&1
    if !errorlevel!==0 (
        set "UV_CMD=uv"
    ) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
        set "UV_CMD=%USERPROFILE%\.local\bin\uv.exe"
    ) else if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
        set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
    )

    if defined UV_CMD (
        echo   %GREEN%✓%RESET% uv installed successfully
        echo [OK] uv installed >> "%LOG_FILE%"
    ) else (
        echo   %RED%✗%RESET% Failed to install uv
        echo   %DIM%  Install manually: https://docs.astral.sh/uv/%RESET%
        echo [FAIL] uv install failed >> "%LOG_FILE%"
        set "PREREQ_FAIL=1"
    )
)

echo.

:: ── Abort if critical prerequisites missing ─────────────────────────────────
if "!PREREQ_FAIL!"=="1" (
    echo %RED%✗ Critical prerequisites missing. Please install them and retry.%RESET%
    echo.
    echo   Press any key to exit...
    pause >nul
    exit /b 1
)

:: ============================================================================
:: STEP 2: Create Virtual Environment
:: ============================================================================

echo %CYAN%[2/7]%RESET% %BOLD%Setting up virtual environment...%RESET%

if exist ".venv" (
    echo   %CYAN%→%RESET% Removing old .venv...
    rmdir /s /q ".venv" >nul 2>&1
)

!UV_CMD! venv .venv --python 3.11 >> "%LOG_FILE%" 2>&1
if %errorlevel%==0 (
    echo   %GREEN%✓%RESET% Virtual environment created (.venv)
    echo [OK] venv created >> "%LOG_FILE%"
) else (
    :: Fallback: try without specifying python version
    !UV_CMD! venv .venv >> "%LOG_FILE%" 2>&1
    if !errorlevel!==0 (
        echo   %GREEN%✓%RESET% Virtual environment created (.venv)
        echo [OK] venv created (fallback) >> "%LOG_FILE%"
    ) else (
        echo   %RED%✗%RESET% Failed to create virtual environment
        echo [FAIL] venv creation failed >> "%LOG_FILE%"
        echo   Press any key to exit...
        pause >nul
        exit /b 1
    )
)
echo.

:: ============================================================================
:: STEP 3: Install Dependencies
:: ============================================================================

echo %CYAN%[3/7]%RESET% %BOLD%Installing dependencies...%RESET%
echo   %DIM%This may take 2-10 minutes on first run.%RESET%
echo.

:: Prefer uv sync with lockfile (hash-verified)
if exist "uv.lock" (
    echo   %CYAN%→%RESET% Using uv.lock for hash-verified installation...
    set "UV_PROJECT_ENVIRONMENT=%SCRIPT_DIR%\.venv"
    !UV_CMD! sync --extra all --locked >> "%LOG_FILE%" 2>&1
    if !errorlevel!==0 (
        echo   %GREEN%✓%RESET% Dependencies installed %DIM%(hash-verified via uv.lock)%RESET%
        echo [OK] deps installed (locked) >> "%LOG_FILE%"
    ) else (
        echo   %YELLOW%⚠%RESET% Lockfile sync failed — falling back to PyPI resolve...
        echo [WARN] lockfile sync failed, falling back >> "%LOG_FILE%"
        !UV_CMD! pip install -e ".[all]" >> "%LOG_FILE%" 2>&1
        if !errorlevel!==0 (
            echo   %GREEN%✓%RESET% Dependencies installed %DIM%(PyPI resolve)%RESET%
        ) else (
            !UV_CMD! pip install -e "." >> "%LOG_FILE%" 2>&1
            if !errorlevel!==0 (
                echo   %GREEN%✓%RESET% Core dependencies installed
            ) else (
                echo   %RED%✗%RESET% Dependency installation failed. Check install.log for details.
                echo [FAIL] all dep install paths failed >> "%LOG_FILE%"
            )
        )
    )
) else (
    echo   %YELLOW%⚠%RESET% uv.lock not found — installing without hash verification
    !UV_CMD! pip install -e ".[all]" >> "%LOG_FILE%" 2>&1
    if !errorlevel!==0 (
        echo   %GREEN%✓%RESET% Dependencies installed
    ) else (
        !UV_CMD! pip install -e "." >> "%LOG_FILE%" 2>&1
        if !errorlevel!==0 (
            echo   %GREEN%✓%RESET% Core dependencies installed
        ) else (
            echo   %RED%✗%RESET% Dependency installation failed
            echo [FAIL] dep install failed >> "%LOG_FILE%"
        )
    )
)
echo.

:: ============================================================================
:: STEP 4: Environment File
:: ============================================================================

echo %CYAN%[4/7]%RESET% %BOLD%Setting up environment file...%RESET%

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul 2>&1
        echo   %GREEN%✓%RESET% Created .env from template
        echo [OK] .env created >> "%LOG_FILE%"
    ) else (
        echo   %YELLOW%⚠%RESET% .env.example not found — skipping
        echo [WARN] .env.example not found >> "%LOG_FILE%"
    )
) else (
    echo   %GREEN%✓%RESET% .env already exists
    echo [OK] .env exists >> "%LOG_FILE%"
)
echo.

:: ============================================================================
:: STEP 5: Sync Bundled Skills
:: ============================================================================

echo %CYAN%[5/7]%RESET% %BOLD%Syncing bundled skills...%RESET%

set "RAKSHASTRA_HOME=%USERPROFILE%\.rakshastra"
if not exist "%RAKSHASTRA_HOME%\skills" mkdir "%RAKSHASTRA_HOME%\skills" >nul 2>&1

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "tools\skills_sync.py" >> "%LOG_FILE%" 2>&1
    if !errorlevel!==0 (
        echo   %GREEN%✓%RESET% Skills synced to %DIM%~\.rakshastra\skills\%RESET%
        echo [OK] skills synced >> "%LOG_FILE%"
    ) else (
        :: Fallback: copy skills directory
        if exist "skills" (
            xcopy "skills\*" "%RAKSHASTRA_HOME%\skills\" /s /e /y /q >nul 2>&1
            echo   %GREEN%✓%RESET% Skills copied to %DIM%~\.rakshastra\skills\%RESET%
            echo [OK] skills copied (fallback) >> "%LOG_FILE%"
        ) else (
            echo   %YELLOW%⚠%RESET% Skills sync failed — run 'rakshastra setup' later
            echo [WARN] skills sync failed >> "%LOG_FILE%"
        )
    )
) else (
    echo   %YELLOW%⚠%RESET% Python venv not found — skipping skill sync
    echo [WARN] venv python not found for skill sync >> "%LOG_FILE%"
)
echo.

:: ============================================================================
:: STEP 6: PATH Setup
:: ============================================================================

echo %CYAN%[6/7]%RESET% %BOLD%Configuring PATH...%RESET%

set "VENV_SCRIPTS=%SCRIPT_DIR%\.venv\Scripts"

:: Check if already on PATH
echo %PATH% | findstr /i "%VENV_SCRIPTS%" >nul 2>&1
if %errorlevel%==0 (
    echo   %GREEN%✓%RESET% .venv\Scripts already on PATH
    echo [OK] PATH already configured >> "%LOG_FILE%"
) else (
    :: Add to user PATH via PowerShell (persistent)
    powershell -NoProfile -Command ^
        "$userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); " ^
        "if ($userPath -notlike '*%VENV_SCRIPTS%*') { " ^
        "  [Environment]::SetEnvironmentVariable('Path', '%VENV_SCRIPTS%;' + $userPath, 'User'); " ^
        "  Write-Host 'PATH updated' " ^
        "}" >> "%LOG_FILE%" 2>&1
    
    :: Also add to current session
    set "PATH=%VENV_SCRIPTS%;%PATH%"
    echo   %GREEN%✓%RESET% Added .venv\Scripts to user PATH
    echo   %DIM%  Restart your terminal for PATH changes to take effect%RESET%
    echo [OK] PATH updated >> "%LOG_FILE%"
)
echo.

:: ============================================================================
:: STEP 7: Build & Launch Desktop Application
:: ============================================================================

echo %CYAN%[7/7]%RESET% %BOLD%Building & Launching Desktop App...%RESET%
echo.

echo   %CYAN%→%RESET% Building React Web Dashboard...
cd /d "%SCRIPT_DIR%\web"
call npm run build >> "%LOG_FILE%" 2>&1
if !errorlevel! neq 0 (
    echo   %YELLOW%⚠%RESET% Web dashboard build failed - check install.log
)

echo   %CYAN%→%RESET% Building Desktop Application...
cd /d "%SCRIPT_DIR%\apps\desktop"
call npm run pack >> "%LOG_FILE%" 2>&1
if !errorlevel! neq 0 (
    echo   %YELLOW%⚠%RESET% Desktop application build failed - check install.log
)

set "APP_EXE=%SCRIPT_DIR%\apps\desktop\release\win-unpacked\Rakshastra.exe"
if exist "%APP_EXE%" (
    echo   %CYAN%→%RESET% Launching Rakshastra Desktop Application...
    start "" "%APP_EXE%"
    echo   %GREEN%✓%RESET% Desktop app launched successfully
    echo [OK] Desktop app launched >> "%LOG_FILE%"
) else (
    echo   %RED%✗%RESET% Desktop app executable not found
    echo [ERROR] Desktop app executable not found >> "%LOG_FILE%"
)
cd /d "%SCRIPT_DIR%"

:: ============================================================================
:: Done
:: ============================================================================

echo.
echo %GOLD%  ╔══════════════════════════════════════════════════════════════╗%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %GREEN%✓ Installation Complete!%RESET%                                    %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %BOLD%Next steps:%RESET%                                                 %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   1. Configure API keys in the setup wizard                  %GOLD%║%RESET%
echo %GOLD%  ║%RESET%      %DIM%(or edit .env manually)%RESET%                                   %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   2. Open a %BOLD%new%RESET% terminal and run:                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%      %CYAN%rakshastra%RESET%                                                 %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ║%RESET%   %DIM%Other commands:%RESET%                                               %GOLD%║%RESET%
echo %GOLD%  ║%RESET%     %CYAN%rakshastra setup%RESET%    — Re-run setup wizard                   %GOLD%║%RESET%
echo %GOLD%  ║%RESET%     %CYAN%rakshastra status%RESET%   — Check configuration                   %GOLD%║%RESET%
echo %GOLD%  ║%RESET%     %CYAN%rakshastra doctor%RESET%   — Diagnose issues                       %GOLD%║%RESET%
echo %GOLD%  ║%RESET%                                                              %GOLD%║%RESET%
echo %GOLD%  ╚══════════════════════════════════════════════════════════════╝%RESET%
echo.
echo   %DIM%Log file: %LOG_FILE%%RESET%
echo.

echo [%date% %time%] Installation completed >> "%LOG_FILE%"

echo   Press any key to exit...
pause >nul
exit /b 0
