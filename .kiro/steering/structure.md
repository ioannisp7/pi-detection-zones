# Structure

```
src/
  splitted-files/        # Current, modular version (work here)
    pi-detection-zones.py  # Entry point: DetectionApp (wiring, camera, frame loop, event binding)
    config.py              # AppConfig (constants) and Messages (strings)
    engine.py              # Logic, no GUI: MotionDetectionPipeline, Zone, ZoneRepository, DetectionEngine
    ui.py                  # Tkinter: DetectionUI, LogPanel, PreviewSystem, ZoneEditorController
  single-file/           # Older monolithic version, kept for reference
test/                    # Numbered experiment scripts 01-12 showing project evolution
docs/                    # Step-by-step dev notes (1-4) and architecture.md (5-layer vision)
layout.json              # Example saved zone layout
```

## Architecture

- Dependency direction: `pi-detection-zones.py` → `ui.py` / `engine.py` → `config.py`. `engine.py` must not import GUI code.
- `DetectionEngine` owns detection state and the `ZoneRepository`. Each frame, `process_detection(frame)` returns a dict with `raw_frame`, `motion_mask`, `zone_results` and `events`.
- `DetectionApp.run_frame_loop` runs via `root.after(GUI_UPDATE_DELAY)`. It captures a frame, runs the engine, updates `PreviewSystem`, and logs events.
- `ZoneEditorController` handles zone create, edit and delete, and clicks on the camera preview. Zone validation errors use `Messages` codes.
- Keep new features in the matching layer: detection logic in `engine.py`, widgets in `ui.py`, constants in `config.py`.
