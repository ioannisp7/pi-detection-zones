# Tech Stack

- Language: Python 3 (no build system, package manifest, or requirements file)
- Hardware target: Raspberry Pi with a camera module
- Libraries: `picamera2` (camera capture, Pi only), `opencv-python` (cv2), `numpy`, `Pillow` (PIL.ImageTk), `tkinter`/`ttk` (GUI), stdlib `json`, `dataclasses`, `traceback`
- No test framework or linter is configured.

## Commands

Run from `src/splitted-files/` because modules use flat imports (`from config import ...`):

```bash
cd src/splitted-files
python3 pi-detection-zones.py
```

- The app needs a Pi camera and a display. It cannot run headless or off-Pi without mocking `picamera2`.
- `src/single-file/pi-detection-zones.py` is the older monolithic version.
- `test/NN_*.py` are numbered, incremental experiment scripts (history of the project), not a test suite. `docs/` has matching write-ups.

## Conventions

- Class-based design. Classes use PascalCase, methods and variables use snake_case.
- All tunables (resolution, thresholds, kernel size, colors, delays) go in `AppConfig` in `config.py`. Colors are BGR for OpenCV.
- All user-facing and log strings go in `Messages` in `config.py`. Do not hardcode them elsewhere.
- Type hints are used in places but not consistently. Match the surrounding code.
- Errors are logged to the GUI log panel (`LogPanel.add_log`), often with `traceback.format_exc()`. Do not crash the frame loop.
- Layout JSON format: `{"zones": [{"name": str, "points": [[x, y] x4]}]}` with integer coordinates inside the frame bounds.
