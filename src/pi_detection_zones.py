import json
import traceback
from picamera2 import Picamera2
import tkinter as tk
from tkinter import filedialog
from config import AppConfig, Messages
from engine import DetectionEngine
from ui import DetectionUI, LogPanel, PreviewSystem, ZoneEditorController

class DetectionApp:

    def __init__(self, zones_intelligence=None):
        self.running = True
        self.zones_intelligence = zones_intelligence
        self.camera_failure_logged = False
        self.latest_frame = None
        self.engine = DetectionEngine(
            AppConfig.FRAME_WIDTH,
            AppConfig.FRAME_HEIGHT
        )
        self.log_panel = LogPanel()
        self.ui = None
        self.root = self.create_tkinter_gui()
        self.zone_editor_controller = ZoneEditorController(
            self.engine,
            self.ui,
            self.log_panel,
            AppConfig.FRAME_WIDTH,
            AppConfig.FRAME_HEIGHT,
            zones_changed=self.synchronize_detection_zones
        )
        self.preview_controller = PreviewSystem(
            self.ui,
            self.engine
        )
        self.start_camera()
        self.bind_events()

    def create_tkinter_gui(self):
        root = tk.Tk()
        root.title("Zone Detector")

        root.geometry(f"{AppConfig.WINDOW_WIDTH}x{AppConfig.WINDOW_HEIGHT}")

        self.ui = DetectionUI(root)
        right_frame = self.ui.build_ui()

        self.log_panel.create_log_area(right_frame)

        return root

    def bind_events(self):
        # Control buttons
        self.ui.capture_button.config(command=self.capture_background)
        self.ui.arm_button.config(command=self.arm_detection)
        self.ui.save_button.config(command=self.save_layout_gui)
        self.ui.load_button.config(command=self.load_layout_gui)
        self.ui.quit_button.config(command=self.quit_program)
        self.ui.stop_button.config(command=self.toggle_preview)

        # Zone editor
        self.ui.apply_button.config(command=self.zone_editor_controller.apply_zone_changes)
        self.ui.delete_button.config(command=self.zone_editor_controller.delete_selected_zone)

        self.ui.zone_selector.bind("<<ComboboxSelected>>", self.zone_editor_controller.load_zone_into_editor)

        # Point entry focus
        for index, entry in enumerate(self.ui.point_entries):
            entry.bind(
                "<FocusIn>",
                lambda event, i=index:
                self.zone_editor_controller.select_point_entry(i)
            )

        # Camera click
        self.ui.camera_label.bind("<Button-1>", self.zone_editor_controller.on_camera_click)

    def save_layout_gui(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )

        if not file_path:
            return

        try:
            self.engine.zone_repository.save_layout(file_path)

        except Exception as error:
            self.log_panel.add_log(Messages.LAYOUT_SAVE_FAILED.format(error=error))

            return

        self.log_panel.add_log(Messages.LAYOUT_SAVED)

    def load_layout_gui(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )

        if not file_path:
            return

        try:
            self.engine.load_layout(file_path)

        # UnicodeDecodeError: the selected file is not a text file (for example an image)
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.log_panel.add_log(Messages.INVALID_JSON_FILE)

            return

        except ValueError as error:
            self.log_panel.add_log(str(error))

            return

        except Exception:
            self.log_panel.add_log(traceback.format_exc())

            return

        self.zone_editor_controller.refresh_zone_selector()
        self.synchronize_detection_zones()
        self.log_panel.add_log(Messages.LAYOUT_LOADED)

    # When application is used as module, def synchronize_detection_zones syncs
    # zones list with another zones intelligence application
    def synchronize_detection_zones(self):
        if self.zones_intelligence is None:
            return

        zone_names = []

        for zone in self.engine.zone_repository.zones:
            zone_names.append(zone.name)

        self.zones_intelligence.synchronize_zones(zone_names)

    def run_frame_loop(self):
        if not self.running:
            return

        frame = self.capture_frame()

        if frame is not None:
            result = self.engine.process_detection(frame)

            self.preview_controller.update(
                result["raw_frame"],
                result["motion_mask"],
                result["zone_results"]
            )

            for event in result["events"]:
                if self.zones_intelligence is not None:
                    self.zones_intelligence.process_occupancy_event(event)

                self.log_panel.add_log(self.format_occupancy_event(event))

            self.latest_frame = frame

        self.root.after(AppConfig.GUI_UPDATE_DELAY, self.run_frame_loop)

    def format_occupancy_event(self, event):
        message = Messages.OBJECT_ENTERED if event.occupied else Messages.OBJECT_EXITED

        return message.format(zone_name=event.zone_name)

    def quit_program(self):
        self.running = False
        self.log_panel.add_log(Messages.EXITING)

        self.stop_camera()

        self.root.quit()
        self.root.destroy()

    def capture_background(self):
        success = self.engine.capture_background_reference(self.latest_frame)

        if not success:
            self.log_panel.add_log(Messages.NO_CAMERA_FRAME)
            return

        if not self.engine.detection_enabled:
            self.ui.enable_arm_button()

        self.log_panel.add_log(Messages.BACKGROUND_CAPTURED)

    def arm_detection(self):
        self.engine.enable_detection()
        self.ui.disable_arm_button()
        self.ui.enable_stop_button()
        self.log_panel.add_log(Messages.DETECTION_ARMED)

    def toggle_preview(self):
        preview = self.preview_controller
        preview.enabled = not preview.enabled

        if preview.enabled:
            self.log_panel.add_log(Messages.PREVIEW_RESUMED)

        else:
            preview.stop_preview()
            self.log_panel.add_log(Messages.PREVIEW_STOPPED)

        self.ui.set_stop_button_label(preview.enabled)

    def start_camera(self):
        try:
            self.picam2 = Picamera2()
            self.picam2.configure(
                self.picam2.create_preview_configuration(
                    main={
                        "size": (
                            AppConfig.FRAME_WIDTH,
                            AppConfig.FRAME_HEIGHT
                        ),
                        # "RGB888" in Picamera2 gives 3-channel frames in BGR order, which is what OpenCV
                        # expects. The default ("XBGR8888") gives RGBX order and swaps red and blue
                        "format": "RGB888"
                    }
                )
            )

            self.picam2.start()

        except Exception as error:
            self.picam2 = None
            self.log_panel.add_log(Messages.CAMERA_START_FAILED.format(error=error))

    def capture_frame(self):
        if self.picam2 is None:
            return None

        try:
            return self.picam2.capture_array()

        except Exception:
            if not self.camera_failure_logged:
                self.log_panel.add_log(Messages.CAMERA_CAPTURE_FAILED)
                self.camera_failure_logged = True

            return None

    def stop_camera(self):
        if self.picam2 is None:
            return

        try:
            # close() stops the camera and releases it, so the next start can open it straight away
            self.picam2.close()
        except Exception:
            self.log_panel.add_log(traceback.format_exc())


if __name__ == "__main__":
    app = DetectionApp()
    app.run_frame_loop()
    app.root.mainloop()
