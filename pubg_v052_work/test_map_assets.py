import tempfile
import unittest
from pathlib import Path
from map_assets import asset_score, select_asset, cached_path, read_metadata

class MapAssetTests(unittest.TestCase):
    def test_selection(self):
        entries = [
            {'name':'Baltic_Main_Low_Res.png','type':'file','download_url':'https://raw.githubusercontent.com/x'},
            {'name':'Baltic_Main_High_Res.png','type':'file','download_url':'https://raw.githubusercontent.com/y'},
            {'name':'Miramar_Main_High_Res.png','type':'file','download_url':'https://raw.githubusercontent.com/z'},
        ]
        self.assertEqual(select_asset(entries, 'Erangel')['name'], 'Baltic_Main_High_Res.png')
    def test_no_map(self):
        with self.assertRaises(FileNotFoundError):
            select_asset([], 'Taego')
    def test_cache_paths(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(cached_path('Haven (legacy)',td).name, 'haven_legacy.png')
            self.assertEqual(read_metadata('Erangel',td), {})

if __name__ == '__main__': unittest.main()
