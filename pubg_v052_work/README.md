# PUBG Drop Assistant v0.1 — Offline prototype

**Scope:** Erangel, 8,000 × 8,000 meters. Windows 10/11, designed for recordings captured at 2560×1440. **No live PUBG capture, overlay, input injection, memory access, or automated gameplay.**

## Windows setup and EXE

1. Install Python 3.11 or 3.12 for Windows (check the Python launcher option).
2. Unzip the project to a local directory.
3. Double-click `build_windows.bat`. It creates a virtual environment, installs dependencies, and builds `dist\PUBG_Drop_Assistant.exe`.
4. Run the EXE. You can also use `run_windows.bat` after installation.

**The archive contains source and build scripts, not a precompiled Windows EXE.** Windows build is required. If antivirus flags a self-packed EXE, verify the source and build locally; do not disable security protections.

## Map and calculation

- Optional: load a **square, north-up, full-extent Erangel map image** that you have rights to use. It must cover the complete 8×8 km play map, without borders or UI chrome. If you don't load an image, an 8×8 grid appears.
- Select the plane's route start, end, then target by clicking the map. Coordinates use meters from the map's upper-left corner.
- Set assumed plane speed, descent duration, and horizontal movement speed, then press **추천 이탈 지점 계산**.
- Save/load JSON projects. The map image path is stored as a local absolute path.

### IMPORTANT: calculation limitations

This is a simplified **unvalidated heuristic**, not a verified PUBG parachute model. It samples plane-route exit locations and minimizes elapsed plane travel plus a coarse post-exit travel estimate. It does **not** model actual freefall acceleration, parachute deployment, gliding, changing velocity, terrain altitude, or aircraft path timing. Default parameters (100 m/s, 35 s, 38 m/s) are **illustrative placeholders**, not sourced gameplay measurements. Outputs are only for offline experimentation.

## Recording-based tracker

1. Record a PUBG match (or use a video file) with a visible full map and plane icon. The video must be locally saved; the program never connects to the game.
2. Choose the recording in the app.
3. Click **첫 프레임 미리보기 / 영역 선택**. Drag with **left mouse** to select the plane icon template; drag with **right mouse** to select the search region (ideally the entire map). If the icon is absent in the first frame, trim the recording so it appears in the first frame.
4. Click **녹화 영상 추적 → CSV** to export `time_seconds, pixel_x, pixel_y, confidence`.
5. The tracker uses basic grayscale template matching. It is best suited to clips where the full map is open, camera framing and map scale stay fixed, and the icon remains visually stable. It can fail or match the wrong object when the map closes, the icon rotates, the UI animates, or a similar icon appears. CSV pixel coordinates are **not automatically mapped to world coordinates**. Review the data before using it.

The preview starts from the first video frame. For 2560×1440 footage, the default search rectangle covers the full frame; you can adjust it. Template and search rectangles are in **source video pixels**, not preview pixels.

## Validation

Run `python -m unittest test_engine.py` from the project folder. These tests check only basic mathematical invariants, not gameplay accuracy. The UI and OpenCV tracker require local Windows/GUI/video testing.

## Planned upgrades

- Calibrate a real flight model from measured video data.
- Add world-coordinate calibration for CSV tracks.
- Improve rotating-icon tracking and reject low-confidence detections.
- Consider a live overlay **only if explicitly permitted by PUBG policies**.

## v0.2 experimental community strategy comparison

- Choose **커뮤니티 전략 비교** to compare 600 m, 750 m, 900 m curved, and long-glide hypotheses.
- The optimizer scans the whole plane route; if the route never comes within 600 m of the target, it does NOT force a 600 m exit. It evaluates the remaining feasible candidates.
- **Important:** The numerical comparison score is an **uncalibrated heuristic**, NOT a measured landing time. Approach speeds in strategy names are community references, not verified horizontal speeds. No claim of fastest real landing is made.
- Use **지도 이미지 불러오기** for a saved full-map screenshot, then manually select plane endpoints and target. Automatic recognition of route/marker from a screenshot is not implemented yet.
- The recorded-video tracker remains a pixel-template matcher and does not yet map video coordinates to world coordinates.
- No live capture, in-game overlay, process memory access, or automated input is included. PUBG policy may prohibit unauthorized live gameplay assistance; obtain explicit permission before attempting it.
- Run `python -m unittest discover -v` for six offline engine tests.
