import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
import app_update

class UpdateTests(unittest.TestCase):
    def test_versions(self):
        self.assertEqual(app_update.parse_version('v0.6.0'), (0,6,0))
        self.assertIsNone(app_update.parse_version('pubg'))
        self.assertIsNone(app_update.parse_version('v0.6.0-beta'))
    def test_check_update(self):
        import json
        release = {'tag_name':'v0.7.0','assets':[
            {'name':app_update.PACKAGE,'browser_download_url':'https://github.com/'+app_update.REPO+'/releases/download/v0.7.0/'+app_update.PACKAGE},
            {'name':app_update.CHECKSUM,'browser_download_url':'https://github.com/'+app_update.REPO+'/releases/download/v0.7.0/'+app_update.CHECKSUM}]}
        with patch.object(app_update,'_get',return_value=json.dumps(release).encode()):
            self.assertEqual(app_update.check_update()['version'],'v0.7.0')
    def test_stage_update(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('PUBG_Drop_Assistant.exe',b'A'*2048)
            z.writestr('PUBG_Drop_Updater.exe',b'B'*2048)
        data=b.getvalue()
        info={'package_url':'zip','checksum_url':'hash'}
        def get(url, limit=app_update.MAX_BYTES):
            return data if url=='zip' else hashlib.sha256(data).hexdigest().encode()
        with tempfile.TemporaryDirectory() as td,patch.object(app_update,'_get',side_effect=get):
            app, updater=app_update.stage_update(info,td)
            self.assertEqual(app.read_bytes(),b'A'*2048)
            self.assertTrue(updater.exists())
    def test_bad_checksum(self):
        with tempfile.TemporaryDirectory() as td,patch.object(app_update,'_get',side_effect=[b'zip',b'0'*64]):
            with self.assertRaises(ValueError):
                app_update.stage_update({'package_url':'zip','checksum_url':'hash'},td)

if __name__=='__main__': unittest.main()
