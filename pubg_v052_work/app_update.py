"""Opt-in release updates; no game process interaction."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from build_version import VERSION
REPO = 'zoshs1231/PUBG-Drop-Assistant'
API = 'https://api.github.com/repos/' + REPO + '/releases/latest'
PACKAGE = 'PUBG_Drop_Assistant-Windows.zip'
CHECKSUM = PACKAGE + '.sha256'
MAX_BYTES = 150 * 1024 * 1024


def _get(url, limit=MAX_BYTES):
    from map_assets import _https_open
    req = urllib.request.Request(url, headers={'User-Agent':'PUBG-Drop-Assistant/' + VERSION, 'Accept':'application/vnd.github+json' if url == API else 'application/octet-stream'})
    with _https_open(req, timeout=45) as resp:
        if resp.geturl().split('/')[2] not in ('api.github.com','github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):
            raise ValueError('Unexpected update host')
        result = resp.read(limit + 1)
    if len(result) > limit:
        raise ValueError('Update file too large')
    return result


def parse_version(tag):
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', tag or '')
    return tuple(map(int, match.groups())) if match else None


def check_update():
    data = json.loads(_get(API, 1024 * 1024))
    remote = parse_version(data.get('tag_name'))
    current = parse_version(VERSION)
    if not remote or remote <= current or data.get('draft') or data.get('prerelease'):
        return None
    assets = {a.get('name'):a.get('browser_download_url') for a in data.get('assets', [])}
    if not all(assets.get(n, '').startswith('https://github.com/' + REPO + '/releases/download/') for n in (PACKAGE,CHECKSUM)):
        raise ValueError('Release is missing a valid ZIP or checksum asset')
    return {'version':data['tag_name'], 'notes':data.get('body',''), 'package_url':assets[PACKAGE], 'checksum_url':assets[CHECKSUM]}


def stage_update(info, root=None):
    root = Path(root) if root else Path(tempfile.mkdtemp(prefix='pubg_update_'))
    root.mkdir(parents=True, exist_ok=True)
    archive = _get(info['package_url'])
    expected = _get(info['checksum_url'], 4096).decode('ascii').strip().split()[0].lower()
    if not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Invalid SHA-256 checksum')
    if hashlib.sha256(archive).hexdigest() != expected:
        raise ValueError('Update checksum mismatch')
    with zipfile.ZipFile(__import__('io').BytesIO(archive)) as z:
        names = set(z.namelist())
        required = {'PUBG_Drop_Assistant.exe','PUBG_Drop_Updater.exe'}
        if not required.issubset(names):
            raise ValueError('Update package missing executables')
        for name in required:
            dest = root / name
            with z.open(name) as source, dest.open('wb') as output:
                import shutil
                shutil.copyfileobj(source, output)
    return root / 'PUBG_Drop_Assistant.exe', root / 'PUBG_Drop_Updater.exe'


def start_install(new_exe, updater_exe):
    if not getattr(sys, 'frozen', False) or sys.platform != 'win32':
        raise RuntimeError('Automatic installation is only supported in the Windows EXE build')
    target = Path(sys.executable).resolve()
    subprocess.Popen([str(updater_exe), '--source', str(new_exe), '--destination', str(target), '--pid', str(os.getpid())],
                     cwd=str(target.parent), creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0), close_fds=True)
