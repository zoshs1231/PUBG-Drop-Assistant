"""PUBG official API map image cache. Never contacts the game process.

Assets remain KRAFTON property. GitHub metadata SHA is a repository revision,
not a guarantee that the map reflects the current PUBG patch.
"""
import hashlib
import json
import os
import re
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = 'https://api.github.com/repos/pubg/api-assets/contents/Assets/Maps'
MAP_CODES = {
    'Erangel': ('Baltic_Main', 'Erangel_Main', 'Erangel'),
    'Miramar': ('Desert_Main', 'Miramar'),
    'Taego': ('Tiger_Main', 'Taego'),
    'Vikendi': ('DihorOtok_Main', 'Vikendi'),
    'Deston': ('Kiki_Main', 'Deston'),
    'Rondo': ('Neon_Main', 'Rondo'),
    'Sanhok': ('Savage_Main', 'Sanhok'),
    'Paramo': ('Chimera_Main', 'Paramo'),
    'Karakin': ('Summerland_Main', 'Karakin'),
    'Haven (legacy)': ('Heaven_Main', 'Haven'),
}
MAX_IMAGE_BYTES = 512 * 1024 * 1024  # 512 MiB safety cap for high-resolution LFS maps

def cache_root():
    base = os.environ.get('LOCALAPPDATA')
    if not base:
        base = str(Path.home() / '.local' / 'share')
    return Path(base) / 'PUBGDropAssistant' / 'maps'

def slug(name):
    if name not in MAP_CODES:
        raise ValueError('지원하지 않는 지도입니다.')
    return re.sub('[^a-z0-9]+', '_', name.lower()).strip('_')

def cached_path(name, root=None):
    root = Path(root) if root is not None else cache_root()
    return root / (slug(name) + '.png')

def metadata_path(name, root=None):
    root = Path(root) if root is not None else cache_root()
    return root / (slug(name) + '.json')

def read_metadata(name, root=None):
    p = metadata_path(name, root)
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}

def _https_open(request, timeout=20):
    """Use OS trust roots on Windows; bundled CA roots elsewhere.

    Never disable certificate verification. PyInstaller bundles dependencies.
    """
    if sys.platform == 'win32':
        try:
            import truststore
            context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            return urllib.request.urlopen(request, timeout=timeout, context=context)
        except ImportError:
            pass
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    return urllib.request.urlopen(request, timeout=timeout, context=context)

def request_json(url, opener=None):
    opener = opener or _https_open
    req = urllib.request.Request(url, headers={'User-Agent':'PUBG-Drop-Assistant/0.5', 'Accept':'application/vnd.github+json'})
    with opener(req, timeout=20) as response:
        return json.load(response)

def asset_score(filename, aliases):
    stem = Path(filename).stem.lower()
    if not filename.lower().endswith('.png'):
        return -1
    if not any(alias.lower() in stem for alias in aliases):
        return -1
    # Prefer full maps, high resolution, labeled imagery. Avoid icons/selection thumbnails.
    score = 0
    if 'high' in stem or '8192' in stem: score += 100
    if 'main' in stem: score += 20
    if 'low' in stem: score -= 35
    if 'no_text' in stem or 'notext' in stem: score -= 5
    if 'minimap' in stem: score += 5
    if 'icon' in stem or 'thumb' in stem: score -= 100
    score += max(0, 10 - len(stem)//10)
    return score

def select_asset(entries, name):
    aliases = MAP_CODES[name]
    candidates = [(asset_score(e.get('name',''), aliases), e) for e in entries
                  if e.get('type') == 'file' and e.get('download_url')]
    candidates = [(score, e) for score, e in candidates if score >= 0]
    if not candidates:
        raise FileNotFoundError(f'{name}: 공식 저장소에서 지도 PNG를 찾지 못했습니다.')
    return max(candidates, key=lambda item: (item[0], item[1]['name']))[1]

def check_remote(name, opener=None):
    if name not in MAP_CODES:
        raise ValueError('지원하지 않는 지도입니다.')
    entries = request_json(REPO + '?ref=master', opener)
    if not isinstance(entries, list):
        raise RuntimeError('공식 지도 목록 응답 형식이 변경되었습니다.')
    return select_asset(entries, name)

def update_map(name, root=None, opener=None):
    """Download and atomically replace a cache entry, only when content changes.

    Returns (Path, status) where status is downloaded/updated/current.
    """
    root = Path(root) if root is not None else cache_root()
    root.mkdir(parents=True, exist_ok=True)
    opener = opener or _https_open
    entry = check_remote(name, opener)
    target = cached_path(name, root)
    old = read_metadata(name, root)
    sha = entry.get('sha')
    if target.is_file() and sha and old.get('github_sha') == sha:
        return target, 'current'
    size = entry.get('size') or 0
    if size > MAX_IMAGE_BYTES:
        raise ValueError('지도 이미지가 허용된 다운로드 크기를 초과합니다.')
    url = entry['download_url']
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('raw.githubusercontent.com', 'github.com'):
        raise ValueError('예상하지 못한 지도 다운로드 주소입니다.')

    # Git LFS files may return a text pointer from raw.githubusercontent.com.
    # The media endpoint serves actual LFS image content.
    repo_path = urllib.parse.quote(entry.get('path') or ('Assets/Maps/' + entry['name']), safe='/')
    media_url = 'https://media.githubusercontent.com/media/pubg/api-assets/master/' + repo_path
    urls = [media_url, url] if media_url != url else [url]
    temp_name = None
    failures = []
    try:
        from PIL import Image, UnidentifiedImageError
        for candidate in urls:
            if temp_name and os.path.exists(temp_name):
                os.unlink(temp_name)
                temp_name = None
            try:
                req = urllib.request.Request(candidate, headers={
                    'User-Agent':'PUBG-Drop-Assistant/0.5.2',
                    'Accept':'image/png,application/octet-stream'})
                with opener(req, timeout=60) as response, tempfile.NamedTemporaryFile(
                    dir=root, suffix='.png', delete=False) as temp:
                    temp_name = temp.name
                    content_type = response.headers.get('Content-Type', '')
                    total = 0
                    prefix = b''
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        if len(prefix) < 256:
                            prefix += chunk[:256-len(prefix)]
                        total += len(chunk)
                        if total > MAX_IMAGE_BYTES:
                            raise ValueError('지도 다운로드 용량 제한 초과')
                        temp.write(chunk)
                if prefix.startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError('Git LFS 포인터 텍스트를 수신했습니다 (실제 이미지 아님)')
                if not prefix.startswith(b'\x89PNG\r\n\x1a\n'):
                    raise ValueError(f'PNG가 아닌 서버 응답 (Content-Type: {content_type or "없음"}, 처음 80바이트: {prefix[:80]!r})')
                with Image.open(temp_name) as img:
                    if img.width * img.height > 150_000_000:
                        raise ValueError('지도 이미지 픽셀 제한 초과')
                    img.verify()
                with Image.open(temp_name) as img:
                    if img.width < 512 or img.height < 512 or abs(img.width-img.height) > max(img.width,img.height)*0.1:
                        raise ValueError('지도 이미지 크기/비율이 적절하지 않습니다.')
                break
            except (urllib.error.URLError, OSError, ValueError, UnidentifiedImageError) as exc:
                failures.append(f'{urllib.parse.urlparse(candidate).hostname}: {exc}')
        else:
            raise RuntimeError('공식 지도 이미지 다운로드에 실패했습니다.\n' + '\n'.join(failures))
        hasher = hashlib.sha256()
        with open(temp_name, 'rb') as downloaded:
            for block in iter(lambda: downloaded.read(1024 * 1024), b''):
                hasher.update(block)
        digest = hasher.hexdigest()
        state = 'updated' if target.exists() else 'downloaded'
        os.replace(temp_name, target)
        temp_name = None
        metadata = {'name':name, 'source':'pubg/api-assets', 'github_sha':sha,
                    'filename':entry.get('name'), 'sha256':digest,
                    'checked_at_utc':datetime.now(timezone.utc).isoformat(),
                    'source_url':url,
                    'note':'GitHub SHA does not prove current PUBG patch compatibility.'}
        metadata_path(name, root).write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        return target, state
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
