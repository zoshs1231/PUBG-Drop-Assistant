import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from map_assets import update_map

class FakeResponse:
    def __init__(self, data, ctype):
        self.buffer = io.BytesIO(data)
        self.headers = {'Content-Type': ctype}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n=-1): return self.buffer.read(n)

class MapDownloadTests(unittest.TestCase):
    def test_lfs_pointer_fallback_to_valid_png(self):
        b = io.BytesIO()
        Image.new('RGB', (512,512)).save(b, format='PNG')
        png = b.getvalue()
        pointer = b'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 123\n'
        urls=[]
        def opener(req, timeout=20):
            urls.append(req.full_url)
            if 'media.githubusercontent.com' in req.full_url:
                return FakeResponse(pointer, 'text/plain')
            return FakeResponse(png, 'image/png')
        entry = {'name':'Baltic_Main.png', 'path':'Assets/Maps/Baltic_Main.png',
                 'download_url':'https://raw.githubusercontent.com/pubg/api-assets/master/Assets/Maps/Baltic_Main.png',
                 'sha':'123', 'size':len(png)}
        with tempfile.TemporaryDirectory() as td, patch('map_assets.check_remote',return_value=entry):
            path, status = update_map('Erangel',td,opener)
            self.assertEqual(status,'downloaded')
            self.assertEqual(path.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(len(urls),2)

    def test_non_image_never_replaces_cached_map(self):
        entry = {'name':'Baltic_Main.png', 'path':'Assets/Maps/Baltic_Main.png',
                 'download_url':'https://raw.githubusercontent.com/pubg/api-assets/master/Assets/Maps/Baltic_Main.png',
                 'sha':'456', 'size':100}
        def opener(req, timeout=20): return FakeResponse(b'<html>not found</html>','text/html')
        with tempfile.TemporaryDirectory() as td, patch('map_assets.check_remote',return_value=entry):
            from map_assets import cached_path
            cache = cached_path('Erangel',td)
            cache.write_bytes(b'old good cache')
            with self.assertRaises(RuntimeError): update_map('Erangel',td,opener)
            self.assertEqual(cache.read_bytes(),b'old good cache')
            self.assertFalse(list(Path(td).glob('tmp*.png')))

if __name__ == '__main__': unittest.main()
