---
inclusion: always
---

# Development Rules

## Project status

This is an existing, working hobby project. It is not a greenfield application.

The project originally started as a computer-vision system specifically intended for train detection on a model railway. During development, the scope was intentionally changed to first build a more generic zone-detection system.

The current application is therefore intentionally generic. Once the generic zone-detection functionality is completed and stable, it will be used as the foundation for train detection and model railway automation, with the required train-specific adjustments.

Preserve working functionality and prefer incremental improvements over large rewrites.

## Architecture

The current application intentionally uses four Python files:

- `config.py`
- `engine.py`
- `ui.py`
- `pi-detection-zones.py`

Keep this four-file architecture unless there is a clear technical reason that adding or restructuring files is necessary.

Do not split classes or functionality into additional modules merely for theoretical architectural cleanliness.

## Code changes

Before making a significant change, understand the existing implementation and how the requested change fits into it.

Prefer the smallest change that solves the requested problem.

Do not refactor unrelated code while implementing a feature or fixing a bug.

Do not rewrite working components simply because another implementation could be considered cleaner or more modern.

Preserve existing behavior unless the requested change explicitly requires changing it.

## Computer vision approach

Computer vision using the Raspberry Pi cameras is the preferred approach for detecting trains and railway activity.

Avoid introducing detection approaches that require modifying the vintage rolling stock or railway infrastructure, such as:

- magnets attached to trains
- resistor wheelsets
- reed switches
- Hall-effect sensors
- RailCom-based detection
- track-current detection

unless there is a specific reason to reconsider this project decision.

## Hardware

The system interacts with physical model railway hardware.

Changes involving cameras, GPIO, motor control, relays, sensors, train movement or physical timing should be treated cautiously.

Clearly identify changes that could affect physical hardware behavior.

Do not change hardware-control behavior as part of an unrelated software change.

## Raspberry Pi environment

The Raspberry Pi is the actual execution environment.

Camera-related and hardware-related behavior should be considered separately from pure Python logic.

Do not claim that hardware or camera functionality has been tested unless it has actually been tested on the Raspberry Pi.

## Future architecture

The project may eventually expand from camera-based detection into railway automation and physical control.

Future concepts documented in `docs/architecture.md` are plans/direction, not necessarily implemented functionality.

Do not treat planned future components as if they already exist in the current application.

## Configuration and messages

Continue following the existing project conventions documented in `tech.md`.

Application tunables should remain in `AppConfig` in `config.py`.

User-facing and log messages should remain in `Messages` in `config.py`.

This includes application log messages, status messages, button labels and other user-visible text.

Do not introduce new hardcoded user-facing strings elsewhere in the application.

Existing user-facing strings that currently sit outside `Messages` should be migrated to `Messages` when intentionally cleaning up the relevant code or when the relevant code is being modified.

## Git

Git is used for version control.

Do not automatically create commits, reset changes, discard changes or restore files unless explicitly requested.

Treat existing uncommitted changes as potentially intentional.

Before modifying a file with significant uncommitted changes, inspect the relevant existing code/diff and preserve the user's work.

## Main entry point

`pi-detection-zones.py` is the current application entry point.

## Development style

Keep solutions practical and understandable.

Avoid unnecessary frameworks, dependencies and abstractions.

When several approaches are possible, prefer the simpler approach unless there is a clear benefit to greater complexity.

Existing working behavior has priority over theoretical architectural perfection.

## Historical files

The following files and directories are historical/reference material and must not be modified as part of normal development:

- `src/single-file/`
- `test/NN_*.py`

These represent earlier versions or experiments from the development history of the project.

Do not edit, refactor, delete, rename or otherwise modify these files unless explicitly requested by the user.

Current application development must be performed against the active four-file implementation in `src/splitted-files/`.