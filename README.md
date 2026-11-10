# pi-detection-zones

A camera-based zone-occupancy detector for Raspberry Pi.

You draw zones over areas of a live camera image, and the application reports whether each zone is **occupied** or **free**. It was built as the first step towards detecting trains on a model railway, using only a camera, without modifying the rolling stock or the track.

This is a personal hobby project for learning and experimentation. Feature requests and ideas are welcome via Issues/Discussions. Implementation is done solely by the project owner.

## Features

- Live camera preview in a desktop window
- Zones with 4 corner points, in any four-sided shape
- Zone editor: create, rename, move and delete zones, by typing coordinates or by clicking on the camera preview
- Occupied / free status per zone, shown in colour with the percentage of changed pixels
- A second preview showing the motion mask (the pixels that changed)
- Log panel with an entry each time something enters or leaves a zone
- Zone layouts saved to and loaded from JSON files
- Previews that scale down to fit smaller windows and screens
- Stop Preview button to lower CPU usage while detection keeps running

## How it works

1. With the scene empty, you capture a **background reference** image.
2. Each new camera frame is converted to grayscale and compared with the background.
3. Pixels that differ by more than a threshold count as changed. Small noise is then removed.
4. For each zone, the application counts the changed pixels inside it. If they exceed a set percentage of the zone, the zone is occupied.

Because every frame is compared with the same reference, an object that stops inside a zone keeps it occupied until it leaves.

## Requirements

**Hardware**

- Raspberry Pi 4 (developed and tested on a Raspberry Pi 4 Model B)
- Raspberry Pi camera module
- Monitor, keyboard and mouse, or a remote desktop session

**Software**

- Raspberry Pi OS with desktop
- Python 3
- Picamera2, OpenCV, NumPy, Pillow (with ImageTk) and Tkinter, installed from the Raspberry Pi OS packages

Tested with Python 3.13, OpenCV 4.10, NumPy 2.2, Pillow 11.1 and Picamera2 0.3.38.

## Installation

Update the system and install the required packages:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install python3-picamera2 python3-opencv python3-pil python3-pil.imagetk python3-tk -y
```

Check that the camera works:

```bash
rpicam-hello
```

A short live camera preview should open.

Get the code:

```bash
git clone https://github.com/ioannisp7/pi-detection-zones.git
cd pi-detection-zones
```

## Running

The application must be started from `src/splitted-files/`:

```bash
cd src/splitted-files
python3 pi-detection-zones.py
```

It needs the Pi camera and a desktop display.

## Usage

**1. Define zones**

1. In **Select Zone**, choose **Add new zone**.
2. Type a **Zone Name**.
3. Fill in the four points. Click into a **Point** field, then click on the camera preview to fill in that position. You can also type the coordinates as `x,y`.
4. Click **Apply Zone Changes**.

To edit a zone, select it in **Select Zone**, change its name or points, and click **Apply Zone Changes**. To delete it, select it and click the red **X**.

**2. Save the layout**

Click **Save Layout** to store the zones in a JSON file. Use **Load Layout** to open it again later.

**3. Capture the background**

Make sure nothing is inside the zones, then click **Capture Background**.

**4. Arm detection**

Click **Arm Detection**. The zones turn red when occupied and green when free. The motion mask appears in the second preview, and the log shows an entry each time an object enters or leaves a zone.

**5. Optional: stop the preview**

Click **Stop Preview** to stop drawing the camera images. Detection and the log keep working, and CPU usage drops. Click **Resume Preview** to show them again.

### Tips

- Keep the camera fixed. If it moves, capture the background again.
- Keep the lighting stable. If the lighting changes, empty the zones and click **Capture Background** again.
- Zone coordinates are in camera pixels (1280x720 by default). If you change the camera resolution, saved layouts no longer match and the zones must be redrawn.

## Configuration

Settings are in `AppConfig` in `src/splitted-files/config.py`. The most useful ones:

| Setting | Default | Meaning |
|---|---|---|
| `FRAME_WIDTH`, `FRAME_HEIGHT` | 1280, 720 | Camera resolution. Lower values use less CPU. |
| `GUI_UPDATE_DELAY` | 30 | Pause in milliseconds after each frame. Higher values use less CPU but react more slowly. |
| `OCCUPANCY_PERCENT` | 0.08 | Share of a zone's pixels that must change to mark it occupied (0.08 = 8%). |
| `DIFF_THRESHOLD` | 25 | How much a single pixel must change to count as changed. Higher values are less sensitive. |
| `USE_CLEANUP` | True | Removes small noise from the motion mask. |
| `KERNEL_SIZE` | 5 | Strength of the noise cleanup. |
| `DISPLAY_WIDTH`, `DISPLAY_HEIGHT` | 800, 450 | Maximum preview size on screen. |
| `WINDOW_WIDTH`, `WINDOW_HEIGHT` | 1250, 950 | Initial window size. |

## Layout file format

Layouts are plain JSON. Each zone has a name and four `[x, y]` points in camera pixels:

```json
{
    "zones": [
        {
            "name": "Zone_A",
            "points": [[500, 250], [700, 250], [700, 340], [500, 340]]
        }
    ]
}
```

`src/layout.json` is an example layout.

## Project structure

```
src/
  splitted-files/            Current application
    pi-detection-zones.py    Entry point: window, camera and frame loop
    config.py                Settings (AppConfig) and log messages (Messages)
    engine.py                Detection logic and zones (no GUI code)
    ui.py                    Window, previews, log panel and zone editor
  single-file/               Earlier single-file version, kept for reference
  layout.json                Example zone layout
test/                        Numbered scripts showing how the project developed
docs/                        Development notes
```

## Status

Early development and experimental. The zone detection works and has been tested on a Raspberry Pi 4 with a camera module.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
