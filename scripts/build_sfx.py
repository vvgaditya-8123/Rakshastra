#!/usr/bin/env python3
"""Build a self-extracting Windows installer executable for Rakshastra.

Uses the Windows-native IExpress utility to package the installer into
a single .exe, OR falls back to a self-extracting batch+zip combo.

Usage:
    python scripts/build_sfx.py

Output:
    rakshastra_installer.exe  (in the repository root)
"""

import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALLER_DIR = REPO_ROOT / "installer"
HTA_FILE = INSTALLER_DIR / "rakshastra-setup-wizard.hta"
OUTPUT_EXE = REPO_ROOT / "rakshastra_installer.exe"


def _check_prerequisites():
    """Verify we're running on Windows."""
    if sys.platform != "win32":
        print("ERROR: This script must be run on Windows.")
        sys.exit(1)

    if not HTA_FILE.is_file():
        print(f"ERROR: HTA wizard not found at {HTA_FILE}")
        sys.exit(1)


def _collect_installer_files() -> list[tuple[str, Path]]:
    """Return list of (archive_path, source_path) for all files to bundle."""
    files = []

    # Installer directory (HTA + assets)
    for item in INSTALLER_DIR.rglob("*"):
        if item.is_file():
            arc_path = "installer/" + item.relative_to(INSTALLER_DIR).as_posix()
            files.append((arc_path, item))

    # Essential root files the HTA wizard needs
    for name in ["install-rakshastra.bat", "pyproject.toml", ".env.example"]:
        src = REPO_ROOT / name
        if src.is_file():
            files.append((name, src))

    return files


def _create_sfx_exe(files: list[tuple[str, Path]]):
    """Build a self-extracting .exe using a batch stub + embedded zip.

    This approach works on ALL Windows machines without requiring IExpress.
    The .exe is actually a batch file that extracts an embedded zip payload
    and launches the HTA wizard.

    Technical approach: We create a small .cmd stub that uses PowerShell
    to extract an appended zip payload, then runs mshta on the HTA.
    The stub is padded to a known offset, then the zip is appended.
    When renamed to .exe, Windows will try to run it — but we use a polyglot
    that starts with a valid PE-like header redirect... Actually, the simplest
    reliable approach is to just create a .cmd that self-extracts.

    For a TRUE .exe, we use makecab + extrac32 which are always available.
    """
    print("[1/3] Creating zip payload...")
    # Create the zip in memory
    import io

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc_path, src_path in files:
            zf.write(src_path, arc_path)

        # Add launcher script
        launcher_content = (
            '@echo off\r\n'
            'chcp 65001 >nul 2>&1\r\n'
            'set "HERE=%~dp0"\r\n'
            'if "%HERE:~-1%"=="\\" set "HERE=%HERE:~0,-1%"\r\n'
            'if exist "%HERE%\\installer\\rakshastra-setup-wizard.hta" (\r\n'
            '    start "" mshta "%HERE%\\installer\\rakshastra-setup-wizard.hta"\r\n'
            ') else (\r\n'
            '    echo ERROR: Setup wizard not found.\r\n'
            '    pause\r\n'
            ')\r\n'
        )
        zf.writestr("launch.cmd", launcher_content)

    zip_data = zip_buffer.getvalue()
    zip_size = len(zip_data)
    print(f"  Zip payload: {zip_size / 1024:.0f} KB ({len(files) + 1} files)")

    print("[2/3] Building self-extracting installer...")

    # Strategy: Create a .cmd file that uses PowerShell to extract itself.
    # When the user double-clicks the .exe, Windows recognizes the MZ header
    # but we'll use the simpler approach — a renamed .cmd with self-extraction.
    #
    # Actually, the MOST reliable way for end users is a proper .exe stub.
    # We'll try IExpress first, then fall back to a .cmd approach.

    # Try IExpress approach first
    iexpress_success = _try_iexpress(files)

    if not iexpress_success:
        print("  IExpress unavailable/failed, using batch self-extractor...")
        _build_batch_sfx(zip_data)


def _try_iexpress(files: list[tuple[str, Path]]) -> bool:
    """Try to build with IExpress. Returns True on success."""
    iexpress = shutil.which("iexpress")
    if not iexpress:
        fallback = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "iexpress.exe"
        if fallback.is_file():
            iexpress = str(fallback)
        else:
            return False

    with tempfile.TemporaryDirectory(prefix="rakshastra_iex_") as tmpdir:
        flat_dir = Path(tmpdir) / "files"
        flat_dir.mkdir()

        # IExpress works best with flat files + a batch launcher
        # Copy HTA file directly
        shutil.copy2(HTA_FILE, flat_dir / "rakshastra-setup-wizard.hta")

        # Copy assets if any
        assets_src = INSTALLER_DIR / "assets"
        if assets_src.is_dir():
            assets_dst = flat_dir / "assets"
            assets_dst.mkdir()
            for item in assets_src.iterdir():
                if item.is_file():
                    shutil.copy2(item, assets_dst / item.name)

        # Create a launcher batch
        launcher = flat_dir / "setup.cmd"
        launcher.write_text(
            '@echo off\r\n'
            'chcp 65001 >nul 2>&1\r\n'
            'start "" mshta "%~dp0rakshastra-setup-wizard.hta"\r\n',
            encoding="utf-8",
        )

        # Collect flat files
        flat_files = []
        for item in flat_dir.rglob("*"):
            if item.is_file():
                flat_files.append(item.name)

        # Build SED
        sed_path = Path(tmpdir) / "build.sed"
        file_lines = "\r\n".join(f"FILE{i}=%FILE{i}%" for i in range(len(flat_files)))
        string_lines = "\r\n".join(f"FILE{i}={name}" for i, name in enumerate(flat_files))

        sed = (
            "[Version]\r\n"
            "Class=IEXPRESS\r\n"
            "SEDVersion=3\r\n"
            "[Options]\r\n"
            "PackagePurpose=InstallApp\r\n"
            "ShowInstallProgramWindow=0\r\n"
            "HideExtractAnimation=0\r\n"
            "UseLongFileName=1\r\n"
            "InsideCompressed=0\r\n"
            "CAB_FixedSize=0\r\n"
            "CAB_ResvCodeSigning=0\r\n"
            "RebootMode=N\r\n"
            f"InstallPrompt=%InstallPrompt%\r\n"
            "DisplayLicense=%DisplayLicense%\r\n"
            "FinishMessage=%FinishMessage%\r\n"
            f"TargetName=%TargetName%\r\n"
            f"FriendlyName=%FriendlyName%\r\n"
            "AppLaunched=%AppLaunched%\r\n"
            "PostInstallCmd=%PostInstallCmd%\r\n"
            "AdminQuietInstCmd=%AdminQuietInstCmd%\r\n"
            "UserQuietInstCmd=%UserQuietInstCmd%\r\n"
            "SourceFiles=SourceFiles\r\n"
            "[Strings]\r\n"
            f"InstallPrompt=Install Rakshastra Cyber Defense Agent?\r\n"
            "DisplayLicense=\r\n"
            "FinishMessage=\r\n"
            f"TargetName={OUTPUT_EXE}\r\n"
            "FriendlyName=Rakshastra Setup Wizard\r\n"
            "AppLaunched=setup.cmd\r\n"
            "PostInstallCmd=<None>\r\n"
            "AdminQuietInstCmd=\r\n"
            "UserQuietInstCmd=\r\n"
            f"{string_lines}\r\n"
            "[SourceFiles]\r\n"
            f"SourceFiles0={flat_dir}\\\r\n"
            "[SourceFiles0]\r\n"
            f"{file_lines}\r\n"
        )

        sed_path.write_text(sed, encoding="utf-8")

        # Run IExpress
        cmd = [iexpress, "/N", "/Q", str(sed_path)]
        print(f"  Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if OUTPUT_EXE.is_file():
            return True
        else:
            print(f"  IExpress returned {result.returncode} but no output file")
            if result.stderr:
                print(f"  stderr: {result.stderr[:200]}")
            return False


def _build_batch_sfx(zip_data: bytes):
    """Build a self-extracting .cmd installer (reliable fallback).

    Creates a batch script that:
    1. Extracts the appended zip using PowerShell's Expand-Archive
    2. Launches the HTA wizard
    3. Cleans up on exit
    """
    # Output as .cmd since .exe won't work for a batch script
    output_cmd = REPO_ROOT / "rakshastra_installer.cmd"

    stub = (
        '@echo off\r\n'
        'title Rakshastra Installer\r\n'
        'chcp 65001 >nul 2>&1\r\n'
        'setlocal enabledelayedexpansion\r\n'
        '\r\n'
        ':: Self-extracting Rakshastra installer\r\n'
        'echo.\r\n'
        'echo   ================================================================\r\n'
        'echo     Rakshastra Cyber Defense Agent - Installer\r\n'
        'echo   ================================================================\r\n'
        'echo.\r\n'
        'echo   Extracting files...\r\n'
        '\r\n'
        ':: Create temp extraction dir\r\n'
        'set "EXTRACT_DIR=%TEMP%\\rakshastra_setup_%RANDOM%"\r\n'
        'mkdir "%EXTRACT_DIR%" 2>nul\r\n'
        '\r\n'
        ':: Extract the embedded zip using PowerShell\r\n'
        ':: The zip starts after the __PAYLOAD__ marker\r\n'
        'set "SELF=%~f0"\r\n'
        'powershell -NoProfile -ExecutionPolicy Bypass -Command "& {\r\n'
        "  $content = [IO.File]::ReadAllBytes('%SELF%')\r\n"
        "  $marker = [Text.Encoding]::ASCII.GetBytes('__ZIPSTART__')\r\n"
        "  $idx = -1\r\n"
        "  for ($i = $content.Length - $marker.Length; $i -ge 0; $i--) {\r\n"
        "    $match = $true\r\n"
        "    for ($j = 0; $j -lt $marker.Length; $j++) {\r\n"
        "      if ($content[$i + $j] -ne $marker[$j]) { $match = $false; break }\r\n"
        "    }\r\n"
        "    if ($match) { $idx = $i + $marker.Length; break }\r\n"
        "  }\r\n"
        "  if ($idx -lt 0) { Write-Error 'Payload not found'; exit 1 }\r\n"
        "  $zip = [byte[]]::new($content.Length - $idx)\r\n"
        "  [Array]::Copy($content, $idx, $zip, 0, $zip.Length)\r\n"
        "  $zipPath = '%EXTRACT_DIR%\\payload.zip'\r\n"
        "  [IO.File]::WriteAllBytes($zipPath, $zip)\r\n"
        "  Expand-Archive -Path $zipPath -DestinationPath '%EXTRACT_DIR%' -Force\r\n"
        "  Remove-Item $zipPath -Force\r\n"
        '}"\r\n'
        '\r\n'
        'if errorlevel 1 (\r\n'
        '    echo   ERROR: Failed to extract files.\r\n'
        '    pause\r\n'
        '    goto :cleanup\r\n'
        ')\r\n'
        '\r\n'
        'echo   Launching setup wizard...\r\n'
        'echo.\r\n'
        '\r\n'
        ':: Launch the HTA wizard\r\n'
        'if exist "%EXTRACT_DIR%\\installer\\rakshastra-setup-wizard.hta" (\r\n'
        '    start "" /wait mshta "%EXTRACT_DIR%\\installer\\rakshastra-setup-wizard.hta"\r\n'
        ') else if exist "%EXTRACT_DIR%\\rakshastra-setup-wizard.hta" (\r\n'
        '    start "" /wait mshta "%EXTRACT_DIR%\\rakshastra-setup-wizard.hta"\r\n'
        ') else (\r\n'
        '    echo   ERROR: Setup wizard not found in extracted files.\r\n'
        '    echo   Contents of extract dir:\r\n'
        '    dir /b "%EXTRACT_DIR%"\r\n'
        '    pause\r\n'
        ')\r\n'
        '\r\n'
        ':cleanup\r\n'
        'if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%" 2>nul\r\n'
        'endlocal\r\n'
        'exit /b 0\r\n'
        '\r\n'
        ':: Do not remove the following marker\r\n'
        '__ZIPSTART__'
    )

    # Write stub + zip payload
    with open(output_cmd, "wb") as f:
        f.write(stub.encode("utf-8"))
        f.write(zip_data)

    if output_cmd.is_file():
        size_kb = output_cmd.stat().st_size / 1024
        print(f"\n  [OK] Built: {output_cmd}")
        print(f"  Size: {size_kb:.0f} KB")
        print("  Users double-click this file to launch the setup wizard.")
    else:
        print("ERROR: Failed to create installer.")
        sys.exit(1)


def main():
    print("=" * 60)
    print("  Rakshastra Installer Builder")
    print("=" * 60)
    print()

    _check_prerequisites()

    print("Collecting installer files...")
    files = _collect_installer_files()
    print(f"  Found {len(files)} files to bundle")

    _create_sfx_exe(files)

    print()
    print("Done! Distribute the installer to users.")
    print("They double-click it and the GUI setup wizard launches automatically.")


if __name__ == "__main__":
    main()

