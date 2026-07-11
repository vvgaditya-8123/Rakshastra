import os
import sys
import urllib.request
import subprocess
from pathlib import Path

# URL for winCodeSign
URL = "https://github.com/electron-userland/electron-builder-binaries/releases/download/winCodeSign-2.6.0/winCodeSign-2.6.0.7z"
VERSION = "winCodeSign-2.6.0"

def get_cache_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = str(Path.home() / "AppData" / "Local")
    return Path(local_app_data) / "electron-builder" / "Cache" / "winCodeSign"

def main():
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    dest_folder = cache_dir / VERSION
    if dest_folder.is_dir():
        print(f"winCodeSign is already present at: {dest_folder}")
        return

    archive_path = cache_dir / "winCodeSign-2.6.0.7z"
    
    if not archive_path.is_file():
        print(f"Downloading winCodeSign from: {URL}")
        try:
            urllib.request.urlretrieve(URL, archive_path)
            print("Download completed successfully.")
        except Exception as e:
            print(f"ERROR: Failed to download winCodeSign: {e}")
            sys.exit(1)

    # Locate 7za.exe in node_modules
    repo_root = Path(__file__).resolve().parent.parent
    seven_zip = repo_root / "node_modules" / "7zip-bin" / "win" / "x64" / "7za.exe"
    
    if not seven_zip.is_file():
        # Check in workspace
        seven_zip = repo_root / "apps" / "desktop" / "node_modules" / "7zip-bin" / "win" / "x64" / "7za.exe"
        if not seven_zip.is_file():
            print("ERROR: 7za.exe not found in node_modules.")
            sys.exit(1)

    print(f"Using 7za: {seven_zip}")
    print("Extracting winCodeSign (excluding macOS/darwin folder to avoid symlink privilege errors)...")
    
    # Extract, excluding the darwin folder
    dest_folder.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(seven_zip),
        "x",
        "-y",
        "-x!darwin",  # Exclude macOS signing tools (contains symlinks that fail without admin rights)
        str(archive_path),
        f"-o{dest_folder}"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Extraction completed successfully.")
        # Remove the archive to save space
        try:
            archive_path.unlink()
        except:
            pass
    else:
        print("ERROR: Extraction failed.")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
