# Product

pi-detection-zones (part of the "pi-railvision-ai" hobby project) is a DIY Raspberry Pi computer-vision system for model railway detection and automation. A Pi camera feed is shown in a Tkinter GUI. The user defines 4-point polygon "zones" over track blocks. The app uses background subtraction to flag each zone as occupied or free.

- Workflow: capture an empty-track background reference, arm detection, then monitor zone occupancy and event logs.
- Zone layouts are saved to and loaded from JSON (see `layout.json`).
- Status: early, experimental, personal learning project. Single developer.
- Long-term vision (see `docs/architecture.md`): camera → image processing → track state model → automation logic → physical control (DCC-EX, turnouts, GPIO). The current code covers layers 1-2 only.
