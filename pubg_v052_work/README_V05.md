# PUBG Drop Assistant v0.5 — official map image cache

## What changed
- On first launch, the app asks whether to download the selected map image from the official PUBG API assets GitHub repository.
- On subsequent launches and map switches, any locally cached map is loaded automatically.
- The **지도 업데이트 확인** button checks the official repository metadata and downloads a changed asset. Updates are atomic; failed downloads do not replace cached images.
- Manual image selection remains available. Map cache location: `%LOCALAPPDATA%\PUBGDropAssistant\maps` on Windows.
- Each cached image has JSON metadata including GitHub file SHA, SHA256, source URL and retrieval time.
- Internet is used only when the user approves the initial download or presses the update button. No game memory, live capture, or overlay.

## Important limitations
- The official PUBG API assets repository is not necessarily synchronized with the latest live PUBG map patches. Its GitHub SHA identifies the repository asset revision, not the live game patch version.
- The downloader selects high-resolution PNG files by naming conventions from `Assets/Maps`. If PUBG changes directory structure or naming, an informative error is shown; manual image loading still works.
- Image licensing remains subject to KRAFTON's PUBG API Terms of Use and player-created content policy. Images are not bundled in this ZIP.
- All previous physics calibration limitations of v0.4 remain. This release changes map asset management, not drop physics.
- Building a Windows EXE requires Windows and Python; see `build_windows.bat`.

## Sources
- https://github.com/pubg/api-assets
- https://developer.pubg.com/faq
