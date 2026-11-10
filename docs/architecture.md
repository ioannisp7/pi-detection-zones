# Architecture – pi-detection-zones

## 1\. High-Level Architecture

The application is organized into four main source files:

- `pi-detection-zones.py` – Application entry point and orchestration.
- `config.py` – Application configuration and user-facing messages.
- `engine.py` – Core detection logic and zone management.
- `ui.py` – Graphical user interface, preview rendering and zone editing.

The main processing flow is:

1. The camera captures an image frame.
1. The detection engine processes the frame.
1. The motion detection pipeline compares the frame against the background reference.
1. The resulting motion mask is evaluated against the configured detection zones.
1. Each zone's occupancy state is updated.
1. Occupancy transitions are identified and returned as events.
1. The graphical interface displays the camera image, detection mask, zone status and event log.

## 2\. Application Components

### 2.1 Application Entry Point – `pi-detection-zones.py`

The entry point contains the `DetectionApp` class, which coordinates the application's components.

Its responsibilities include:

- Initializing the detection engine.
- Creating and configuring the Tkinter application window.
- Initializing the graphical interface and its controllers.
- Initializing and starting the Raspberry Pi camera.
- Capturing frames from the camera.
- Invoking the detection engine for each captured frame.
- Updating the graphical previews.
- Displaying detection events in the system log.
- Handling user actions and application shutdown.

Frame processing is scheduled through Tkinter's `root.after()` mechanism.

The application uses a single main execution loop for camera capture, detection processing and graphical interface updates.

### 2.2 Configuration – `config.py`

The configuration module contains two classes.

**AppConfig**

Defines application-wide settings, including:

- Camera frame resolution.
- Preview dimensions.
- Application window dimensions.
- Graphical layout spacing.
- Detection sensitivity threshold.
- Occupancy percentage threshold.
- Morphological image cleanup settings.
- Preview update delay.
- Log size limit.
- Image rendering parameters and colors.

**Messages**

Contains predefined user-facing messages used by the application for:

- Occupancy transitions.
- Zone management operations.
- Background capture and detection status.
- Layout loading and saving.
- Camera errors.
- Input validation and other application errors.

This centralizes configuration values and messages, avoiding unnecessary duplication throughout the application.

### 2.3 Detection Engine – `engine.py`

The detection engine contains the application's core processing and zone-management functionality.

It consists of five main classes.

#### MotionDetectionPipeline

Responsible for identifying changes between the current camera frame and the captured background reference.

Processing steps:

1. Convert the current frame to grayscale.
1. Calculate the absolute difference between the current frame and the background reference.
1. Apply a binary threshold to identify changed pixels.
1. Optionally apply morphological opening to remove small areas of noise.

The output is a binary motion mask representing detected changes in the image.

#### Zone

Represents an individual detection zone.

Each zone contains:

- A unique name within the application's zone configuration.
- Four coordinate points defining its polygonal area.
- Frame dimensions.
- A NumPy representation of its polygon coordinates.
- A bounding box limiting the area that needs to be processed.
- A polygon mask representing the zone's shape.
- The total number of pixels within the polygon.

The bounding-box and polygon-mask approach reduces unnecessary image processing by limiting occupancy calculations to the relevant area of each zone.

#### OccupancyEvent

Represents a single occupancy transition of a zone.

Each event contains:

- `zone_name` – The name of the zone whose state changed.
- `occupied` – `True` when the zone became occupied, `False` when it became free.

Events are immutable once created. They contain detection data only; converting them into log messages is the responsibility of the application entry point.

#### ZoneRepository

Responsible for managing detection zone definitions.

Its functionality includes:

- Adding zones.
- Updating existing zones.
- Deleting zones.
- Saving zone layouts to JSON files.
- Loading zone layouts from JSON files.
- Reconstructing zone geometry when layouts are loaded.

The repository maintains the collection of configured zones and their associated geometric information.

#### DetectionEngine

Coordinates the detection process and maintains the occupancy state of configured zones.

Its responsibilities include:

- Managing the zone repository.
- Managing the motion detection pipeline.
- Capturing and maintaining the background reference.
- Enabling occupancy detection.
- Processing individual camera frames.
- Evaluating occupancy within each zone.
- Maintaining the current occupancy state of each zone.
- Identifying transitions between occupied and free states.
- Managing zone-related state when zones are added, updated, renamed or deleted.

For every processed frame, the engine returns:

- The original camera frame.
- The generated motion mask, when detection is enabled.
- The occupancy results for the configured zones.
- A list of `OccupancyEvent` objects, one for each zone whose occupancy state changed.

Occupancy is determined by calculating the ratio of changed pixels within a zone relative to its total polygon area.

A zone is considered occupied when its occupancy ratio exceeds the configured `OCCUPANCY_PERCENT` threshold.

### 2.4 Graphical Interface – `ui.py`

The graphical interface is implemented using Tkinter and is divided into four main components.

#### DetectionUI

Responsible for creating and managing the application's graphical interface.

It provides:

- Camera preview.
- Motion-mask preview.
- Detection control buttons.
- Zone selection.
- Zone creation and editing controls.
- Zone deletion.
- Zone layout loading and saving controls.
- Application shutdown controls.

The preview areas automatically resize to fit the available application window space while maintaining their aspect ratio.

#### LogPanel

Provides a graphical system log.

It displays application messages, including:

- Detection events.
- Zone configuration changes.
- Camera-related messages.
- Layout operations.
- Application status information.

The log maintains a configurable maximum number of displayed lines.

#### PreviewSystem

Responsible for rendering the visual representation of the detection results.

It provides:

- Camera frames with zone boundaries.
- Occupancy indicators for each zone.
- Occupancy percentage labels.
- Motion-mask visualization.
- Preview enable/disable functionality.

Occupied zones are displayed in red, while free zones are displayed in green.

Disabling the preview stops graphical updates but does not stop camera capture or detection processing.

#### ZoneEditorController

Manages user interactions related to zone configuration.

Its responsibilities include:

- Selecting existing zones.
- Creating new zones.
- Editing zone names and coordinates.
- Validating zone names and coordinates.
- Preventing duplicate zone names.
- Deleting zones.
- Mapping mouse clicks on the camera preview to original camera-frame coordinates.
- Refreshing the zone selector after configuration changes.

## 3\. Detection Processing Workflow

The normal detection workflow is as follows:

1. The application captures a frame from the Raspberry Pi camera.
1. The frame is passed to `DetectionEngine.process_detection()`.
1. If detection has not been enabled, the engine returns the original frame and empty zone results.
1. If detection is enabled, the motion detection pipeline generates a binary motion mask.
1. The engine evaluates the motion mask against each configured zone.
1. The occupancy ratio is calculated for every zone.
1. The current occupancy state is updated.
1. State transitions are identified:
   - Free to occupied: object entered the zone.
   - Occupied to free: object exited the zone.
1. The engine returns the detection results and an `OccupancyEvent` for each transition.
1. The application updates the graphical previews and converts each event into a system log message.

The processing loop repeats continuously while the application is running.

## 4\. Occupancy Detection and State Management

Each configured zone maintains an occupancy state containing:

- `occupied` – Boolean occupancy status.
- `occupancy_pixels` – Number of changed pixels within the zone.
- `occupancy_ratio` – Ratio of changed pixels to the total polygon area.

The engine maintains these states in its `zone_states` dictionary, indexed by zone name.

Occupancy events are generated only when the state changes. Repeated frames with the same occupancy state do not generate additional events.

The current implementation identifies occupancy transitions but does not publish them through a dedicated external event interface.

Transitions are returned as `OccupancyEvent` objects containing the zone name and the new occupancy state. The application entry point converts each event into a log message using the `OBJECT_ENTERED` and `OBJECT_EXITED` entries in `Messages`, and displays it in the system log.

## 5\. Camera Management

Camera initialization and frame capture are handled by the application entry point using the Picamera2 library.

The current implementation uses:

- One Raspberry Pi camera.
- A configured resolution of 1280 × 720 pixels.
- RGB888 camera output.
- Continuous frame capture.

Camera initialization and capture errors are handled by the application, with error messages displayed in the system log.

The camera is closed during application shutdown to release the camera resource.

## 6\. Zone Layout Persistence

Zone configurations can be saved and loaded using JSON files.

A layout contains a list of zones, with each zone storing:

- Its name.
- Four coordinate points defining its polygon.

The geometric data required for detection, such as bounding boxes and polygon masks, is reconstructed when a layout is loaded.

This keeps the saved layout independent of internal image-processing data structures.

## 7\. Execution Model and Dependencies

The application currently runs as a single Python process using Tkinter's main event loop.

Camera capture, image processing, preview rendering and graphical interface updates are performed sequentially within the application's scheduled frame loop.

**Main dependencies:**

- Python 3
- Picamera2 – Raspberry Pi camera access.
- OpenCV – Image processing and motion detection.
- NumPy – Image and geometric data processing.
- Pillow – Image conversion for graphical previews.
- Tkinter / ttk – Graphical user interface.
- Python standard library – JSON handling, file dialogs, data structures and error handling.

## 8\. Current Scope and Limitations

The project is a generic camera-based zone occupancy detection application.

Its current scope includes image-based motion detection, zone occupancy evaluation, transition identification and graphical monitoring.

The following capabilities are not currently implemented:

- Train recognition or identification.
- Railway track topology or railway-specific zone relationships.
- Train direction or movement tracking.
- Railway traffic management and route conflict detection.
- Decisions regarding train movement or priority.
- Communication with external applications through a structured event interface.
- Control of turnouts, motors, controllers or other railway hardware.
- Multi-camera coordination.
- Autonomous railway operation without the graphical application.

The detection engine identifies changes in configured image areas. It does not determine what caused those changes or interpret them as railway movements.

## 9\. Architectural Design Principles

The project follows these principles:

- **Separation of responsibilities:** Detection processing, zone management, configuration, graphical presentation and application orchestration are separated into distinct components.
- **Reusable detection logic:** Core image-processing and zone-management functionality is implemented independently of the graphical interface.
- **Configuration centralization:** Application settings and user-facing messages are maintained in a dedicated module.
- **Efficient image processing:** Bounding boxes and polygon masks minimize unnecessary pixel processing.
- **Configurable detection:** Detection thresholds and image-cleanup settings can be adjusted centrally.
- **Simple execution model:** The current application uses a single-process, event-loop-based execution model without unnecessary concurrency.

## 10\. Potential Future Integration

The detection functionality may be reused as a vision component in other applications.

For example, a railway automation application could consume occupancy information from the detection engine and use it as input to a separate railway intelligence component.

Such integration would require a clearly defined interface for communicating occupancy states and transition events.

Railway-specific interpretation, traffic decisions and physical hardware control are outside the scope of `pi-detection-zones` and should remain the responsibility of the consuming application.

The existing project remains a standalone generic detection application.
