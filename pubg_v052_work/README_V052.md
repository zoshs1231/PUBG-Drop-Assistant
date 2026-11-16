# v0.5.2 map image download repair

- Git LFS-aware download: try GitHub media endpoint first, then raw download URL.
- Reject Git LFS pointer text, HTML error pages, and non-PNG content before Pillow opens it.
- Validate PNG dimensions and preserve existing cached map on failed updates.
- Report diagnostic response type and source hostname if all sources fail.
- HTTPS certificate verification remains enabled (truststore/certifi).
- Tests: `python -m unittest discover -p 'test_*.py'`.

Run `build_windows.bat` to create the new EXE. Do not reuse the old executable.
The official PUBG API map repository may not reflect the latest game patch.
