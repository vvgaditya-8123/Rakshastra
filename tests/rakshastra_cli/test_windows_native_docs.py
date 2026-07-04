from pathlib import Path


def test_windows_native_install_path_docs_match_installer() -> None:
    doc = Path("website/docs/user-guide/windows-native.md").read_text()
    install = Path("scripts/install.ps1").read_text()

    assert "%LOCALAPPDATA%\\rakshastra\\rakshastra-agent\\venv\\Scripts" in doc
    assert "Get-Command rakshastra        # should print C:\\Users\\<you>\\AppData\\Local\\rakshastra\\rakshastra-agent\\venv\\Scripts\\rakshastra.exe" in doc
    assert '$rakshastraBin = "$InstallDir\\venv\\Scripts"' in install
