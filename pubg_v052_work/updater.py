"""Separate process for replacing a closed Windows executable.

Only runs after the main app downloaded and verified a release package.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


def install(source, destination, pid, wait_seconds=45):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if source.name.lower() != 'pubg_drop_assistant.exe' or destination.name.lower() != 'pubg_drop_assistant.exe':
        raise ValueError('Unexpected executable name')
    if not source.is_file() or source.stat().st_size < 1024:
        raise ValueError('Update executable missing')
    # Wait for process exit using the Windows process handle.
    if sys.platform == 'win32':
        import ctypes
        kernel = ctypes.windll.kernel32
        SYNCHRONIZE = 0x00100000
        handle = kernel.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            try:
                result = kernel.WaitForSingleObject(handle, wait_seconds * 1000)
                if result != 0:
                    raise TimeoutError('Application did not exit')
            finally:
                kernel.CloseHandle(handle)
    else:
        for _ in range(wait_seconds * 4):
            try:
                os.kill(pid, 0)
            except (OSError, ProcessLookupError):
                break
            time.sleep(.25)
        else:
            raise TimeoutError('Application did not exit')
    backup = destination.with_suffix('.exe.bak')
    if backup.exists():
        backup.unlink()
    if destination.exists():
        destination.replace(backup)
    try:
        import shutil
        shutil.copy2(source, destination)
        subprocess.Popen([str(destination)], cwd=str(destination.parent), close_fds=True)
    except Exception:
        if destination.exists():
            destination.unlink()
        if backup.exists():
            backup.replace(destination)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--pid', type=int, required=True)
    args = parser.parse_args()
    try:
        install(args.source, args.destination, args.pid)
    except Exception as exc:
        Path(os.environ.get('LOCALAPPDATA', str(Path.home()))).joinpath('PUBGDropAssistant','update-error.txt').parent.mkdir(parents=True, exist_ok=True)
        Path(os.environ.get('LOCALAPPDATA', str(Path.home()))).joinpath('PUBGDropAssistant','update-error.txt').write_text(str(exc), encoding='utf-8')
        raise

if __name__ == '__main__':
    main()
