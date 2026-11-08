import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import traceback

from config import AppConfig, Messages

class DetectionUI:
    def __init__(self, root):
        self.root = root

        # Camera widgets
        self.camera_label = None
        self.mask_label = None
        self.camera_frame = None
        self.mask_frame = None
        self.right_column = None

        # Current preview size. Starts at the nominal size and shrinks when the window is too small
        self.display_width = AppConfig.DISPLAY_WIDTH
        self.display_height = AppConfig.DISPLAY_HEIGHT

        # Control buttons
        self.capture_button = None
        self.arm_button = None
        self.stop_button = None
        self.load_button = None
        self.save_button = None
        self.quit_button = None

        # Zone editor widgets
        self.zone_selector = None
        self.zone_name_entry = None
        self.point_entries = []

        self.delete_button = None
        self.apply_button = None

    def build_ui(self):
        (
            camera_frame,
            mask_frame,
            left_frame,
            center_frame,
            right_frame
        ) = self.create_main_frames()

        self.create_camera_area(camera_frame, mask_frame)
        self.create_buttons_area(left_frame)
        self.create_zone_editor(center_frame)

        # Resize the previews whenever the window size changes
        self.root.bind("<Configure>", self.fit_previews_to_window)

        return right_frame

    def create_main_frames(self):
        main_frame = tk.Frame(self.root)

        main_frame.pack(
            anchor="nw",
            padx=AppConfig.LAYOUT_PADDING,
            pady=AppConfig.LAYOUT_PADDING
        )

        left_column = tk.Frame(main_frame)

        left_column.pack(
            side=tk.LEFT,
            anchor="n",
            padx=(0, AppConfig.LAYOUT_PADDING)
        )

        right_column = tk.Frame(main_frame)
        right_column.pack(side=tk.LEFT,anchor="n")
        self.right_column = right_column
        camera_frame = tk.Frame(left_column)

        camera_frame.pack(
            fill=tk.BOTH,
            expand=True,
            pady=(0, AppConfig.LAYOUT_PADDING)
        )

        mask_frame = tk.Frame(left_column)
        mask_frame.pack(fill=tk.BOTH,expand=True)
        right_top_frame = tk.Frame(right_column)

        right_top_frame.pack(fill=tk.X, pady=(0, 10))
        left_frame = tk.Frame(right_top_frame)

        left_frame.pack(
            side=tk.LEFT,
            anchor="n",
            padx=(0, 15)
        )

        center_frame = tk.Frame(right_top_frame)
        center_frame.pack(side=tk.LEFT, anchor="n")
        right_frame = tk.Frame(right_column)

        right_frame.pack(fill=tk.BOTH, expand=True)

        return (
            camera_frame,
            mask_frame,
            left_frame,
            center_frame,
            right_frame
        )

    def create_camera_area(
        self,
        camera_frame,
        mask_frame):

        self.camera_frame = camera_frame
        self.mask_frame = mask_frame

        camera_frame.pack_propagate(False)
        mask_frame.pack_propagate(False)

        camera_frame.config(
            width=self.display_width,
            height=self.display_height
        )

        mask_frame.config(
            width=self.display_width,
            height=self.display_height
        )

        self.camera_label = tk.Label(camera_frame, bd=0)
        self.camera_label.pack(anchor="w")
        self.mask_label = tk.Label(mask_frame,bd=0)
        self.mask_label.pack(anchor="w")

    def fit_previews_to_window(self, event=None):
        # <Configure> also fires for every child widget, only react to the window itself
        if event is not None and event.widget is not self.root:
            return

        padding = AppConfig.LAYOUT_PADDING
        aspect_ratio = AppConfig.DISPLAY_HEIGHT / AppConfig.DISPLAY_WIDTH

        # Vertical space: top margin, gap between the two previews, bottom margin. Two previews share what is left
        available_height = self.root.winfo_height() - 3 * padding

        # Horizontal space: left margin, gap before the right column, right margin. The right column keeps its size
        available_width = (
            self.root.winfo_width()
            - 3 * padding
            - self.right_column.winfo_reqwidth()
        )

        width = min(
            AppConfig.DISPLAY_WIDTH,
            available_width,
            int(available_height / 2 / aspect_ratio)
        )

        # Never 0 or negative, cv2.resize would fail
        width = max(width, 1)
        height = max(int(width * aspect_ratio), 1)

        if width == self.display_width and height == self.display_height:
            return

        self.display_width = width
        self.display_height = height

        for frame in (self.camera_frame, self.mask_frame):
            frame.config(width=width, height=height)

    def create_buttons_area(self, left_frame):
        self.capture_button = tk.Button(
            left_frame,
            text="Capture Background",
            height=2,
            width=25
        )

        self.capture_button.pack(pady=10)
        self.arm_button = tk.Button(
            left_frame,
            text="Arm Detection",
            height=2,
            width=25,
            state=tk.DISABLED
        )

        self.arm_button.pack(pady=10)
        self.stop_button = tk.Button(
            left_frame,
            text="Stop Preview",
            height=2,
            width=25,
            state=tk.DISABLED
        )

        self.stop_button.pack(pady=10)
        self.load_button = tk.Button(
            left_frame,
            text="Load Layout",
            height=2,
            width=25
        )

        self.load_button.pack(pady=10)
        self.save_button = tk.Button(
            left_frame,
            text="Save Layout",
            height=2,
            width=25
        )

        self.save_button.pack(pady=10)
        self.quit_button = tk.Button(
            left_frame,
            text="Quit",
            height=2,
            width=25
        )

        self.quit_button.pack(pady=10)

    def enable_arm_button(self):
        self.arm_button.config(state=tk.NORMAL)

    def disable_arm_button(self):
        self.arm_button.config(state=tk.DISABLED)

    def enable_stop_button(self):
        self.stop_button.config(state=tk.NORMAL)

    def set_stop_button_label(self, preview_enabled):
        if preview_enabled:
            self.stop_button.config(text="Stop Preview")
        else:
            self.stop_button.config(text="Resume Preview")

    def create_zone_editor(self, center_frame):
        tk.Label(
            center_frame,
            text="Select Zone"
        ).pack()

        self.zone_selector = ttk.Combobox(
            center_frame,
            values=[Messages.ADD_NEW_ZONE_OPTION],
            state="readonly",
            width=25
        )

        self.zone_selector.pack(pady=5)
        self.zone_selector.current(0)

        tk.Label(
            center_frame,
            text="Zone Name"
        ).pack()

        zone_name_frame = tk.Frame(center_frame)
        zone_name_frame.pack(pady=5)

        self.zone_name_entry = tk.Entry(zone_name_frame, width=18)

        self.zone_name_entry.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(
            zone_name_frame,
            text="X",
            width=3,
            fg="red",
            state=tk.DISABLED
        )

        self.delete_button.pack(side=tk.LEFT)
        self.point_entries.clear()

        for i in range(4):
            tk.Label(
                center_frame,
                text=f"Point {i+1} (x,y)"
            ).pack()

            entry = tk.Entry(center_frame, width=20)

            entry.pack(pady=2)
            self.point_entries.append(entry)

        self.apply_button = tk.Button(
            center_frame,
            text="Apply Zone Changes",
            height=2,
            width=25
        )

        self.apply_button.pack(pady=20)

    def get_zone_name(self):
        return self.zone_name_entry.get()

    def get_point_texts(self):
        values = []

        for entry in self.point_entries:
            values.append(entry.get())

        return values

    def clear_editor(self):
        self.set_zone_name("")

        for i in range(4):
            self.clear_point(i)

        self.disable_delete_button()

    def load_zone(self, zone):
        self.enable_delete_button()
        self.set_zone_name(zone.name)

        for i in range(4):
            x = zone.points[i][0]
            y = zone.points[i][1]

            self.set_point_text(
                i,
                f"{x},{y}"
            )

    def set_zone_name(self, text):
        self.zone_name_entry.delete(0, tk.END)
        self.zone_name_entry.insert(0, text)

    def set_point_text(self, index, text):
        entry = self.point_entries[index]
        entry.delete(0, tk.END)
        entry.insert(0, text)

    def clear_point(self, index):
        self.point_entries[index].delete(0, tk.END)

    def enable_delete_button(self):
        self.delete_button.config(state=tk.NORMAL)

    def disable_delete_button(self):
        self.delete_button.config(state=tk.DISABLED)


class LogPanel:
    def __init__(self):
        self.log_text = None

    # CREATE LOG AREA
    def create_log_area(self, right_frame):

        tk.Label(
            right_frame,
            text="System Log"
        ).pack()

        # Container frame
        log_frame = tk.Frame(right_frame)

        log_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        # Scrollbar
        scrollbar = tk.Scrollbar(log_frame)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Text widget
        self.log_text = tk.Text(
            log_frame,
            width=45,
            yscrollcommand=scrollbar.set,
            wrap=tk.WORD
        )

        self.log_text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        self.log_text.config(state=tk.DISABLED)

        # Connect scrollbar to text widget
        scrollbar.config(command=self.log_text.yview)

    # LOGGING SYSTEM
    def add_log(self, message: str) -> None:
        self.log_text.config(state=tk.NORMAL)

        self.log_text.insert(tk.END,message + "\n")

        # Limit log size
        max_lines = AppConfig.MAX_LOG_LINES

        current_lines = int(self.log_text.index('end-1c').split('.')[0])

        if current_lines > max_lines:
            lines_to_delete = current_lines - max_lines
            self.log_text.delete("1.0", f"{lines_to_delete}.0")

        # Auto-scroll to latest message
        self.log_text.see(tk.END)

        self.log_text.config(state=tk.DISABLED)


class PreviewSystem:

    def __init__(
        self,
        ui,
        engine,
        app,
        zone_repository):

        self.ui = ui
        self.engine = engine
        self.app = app
        self.zone_repository = zone_repository

    def build_zone_display_data(self, zone_results):

        detection_map = {
            result["zone_name"]: result
            for result in zone_results
        }

        zones = []

        for zone in self.zone_repository.zones:
            result = detection_map.get(zone.name,
                {
                    "occupied": False,
                    "occupancy_ratio": 0
                }
            )

            occupied = result["occupied"]
            ratio = result["occupancy_ratio"]

            zones.append({
                "name": zone.name,
                "points_np": zone.points_np,
                "occupied": occupied,
                "occupancy_ratio": ratio
            })

        return zones

    def update(
        self,
        raw_frame,
        motion_mask,
        zone_results):

        if not self.app.preview_enabled:
            return

        zones = self.build_zone_display_data(zone_results)

        overlay = self.render_camera_overlay(raw_frame, zones)

        display_size = (
            self.ui.display_width,
            self.ui.display_height
        )

        overlay = cv2.resize(
            overlay,
            display_size
        )

        photo = self.to_photo(overlay)

        if self.ui.camera_label is not None:
            self.ui.camera_label.config(image=photo)

            self.ui.camera_label.image = photo

        if (self.engine.detection_enabled
            and motion_mask is not None):

            mask_frame = self.render_motion_overlay(
                motion_mask,
                zones
            )

            mask_frame = cv2.resize(mask_frame, display_size)

            mask_photo = self.to_photo(mask_frame)
            self.ui.mask_label.config(image=mask_photo)
            self.ui.mask_label.image = mask_photo

    def stop_preview(self):
        if self.ui.camera_label is not None:

            self.ui.camera_label.config(image="")
            self.ui.camera_label.image = None

        if self.ui.mask_label is not None:
            self.ui.mask_label.config(image="")
            self.ui.mask_label.image = None

    def render_camera_overlay(self, frame, zones):
        overlay_frame = frame.copy()

        for zone in zones:
            color = (
                AppConfig.COLOR_RED
                if zone["occupied"]
                else AppConfig.COLOR_GREEN
            )

            cv2.polylines(
                overlay_frame,
                [zone["points_np"]],
                True,
                color,
                2
            )

            x = zone["points_np"][0][0]
            y = zone["points_np"][0][1] - 10

            label = (
                f"{zone['name']} "
                f"{zone['occupancy_ratio'] * 100:.1f}%"
            )

            cv2.putText(
                overlay_frame,
                label,
                (x, y),
                AppConfig.FONT,
                AppConfig.FONT_SCALE,
                color,
                AppConfig.FONT_THICKNESS
            )

        return overlay_frame

    def render_motion_overlay(self, mask, zones):
        mask_color = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        mask_color[mask > 0] = AppConfig.COLOR_WHITE

        for zone in zones:
            color = (
                AppConfig.COLOR_RED
                if zone["occupied"]
                else AppConfig.COLOR_GREEN
            )

            cv2.polylines(
                mask_color,
                [zone["points_np"]],
                True,
                color,
                2
            )

            x = zone["points_np"][0][0]
            y = zone["points_np"][0][1] - 10

            label = (
                f"{zone['name']} "
                f"{zone['occupancy_ratio'] * 100:.1f}%"
            )

            cv2.putText(
                mask_color,
                label,
                (x, y),
                AppConfig.FONT,
                AppConfig.MASK_FONT_SCALE,
                color,
                AppConfig.FONT_THICKNESS
            )

        return mask_color

    def to_photo(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        return ImageTk.PhotoImage(image=image)


class ZoneEditorController:
    def __init__(
        self,
        engine,
        ui,
        log_panel,
        app,
        frame_width,
        frame_height):

        self.engine = engine
        self.zone_repository = engine.zone_repository
        self.ui = ui
        self.log_panel = log_panel
        self.app = app

        self.frame_width = frame_width
        self.frame_height = frame_height

    def parse_point(self, text_value: str) -> list[int]:

        split_values = text_value.split(",")

        if len(split_values) != 2:
            raise ValueError( Messages.INVALID_COORDINATE_FORMAT)

        try:
            x = int(split_values[0])
            y = int(split_values[1])

        except ValueError:
            raise ValueError(Messages.INVALID_COORDINATE_FORMAT)

        if (x < 0 or x >= self.frame_width):
            raise ValueError(Messages.COORDINATE_OUT_OF_BOUNDS)

        if (y < 0 or y >= self.frame_height):
            raise ValueError(Messages.COORDINATE_OUT_OF_BOUNDS)

        return [x, y]

    def select_point_entry(self, index: int) -> None:
        self.app.active_point_index = index

    def on_camera_click(self, event: tk.Event) -> None:
        if self.ui.camera_label is None:
            return

        x = int(
            event.x
            * AppConfig.FRAME_WIDTH
            / self.ui.display_width
        )

        y = int(
            event.y
            * AppConfig.FRAME_HEIGHT
            / self.ui.display_height
        )

        self.log_panel.add_log(Messages.MOUSE_CLICK.format(x=x, y=y))

        active_index = (self.app.active_point_index)

        if active_index is not None:
            self.ui.set_point_text(
                active_index,
                f"{x},{y}")

    def load_zone_into_editor(
        self,
        event: tk.Event | None = None):

        selected_index = (self.ui.zone_selector.current())

        if selected_index >= len(self.zone_repository.zones):
            self.app.active_point_index = None
            self.ui.clear_editor()
            return

        zone = (self.zone_repository.zones[selected_index])
        self.ui.load_zone(zone)
        self.app.active_point_index = None

    def delete_selected_zone(self):
        selected_index = (self.ui.zone_selector.current())

        if selected_index >= len(self.zone_repository.zones):
            return

        deleted_name = self.zone_repository.zones[selected_index].name
        self.engine.delete_zone(selected_index)
        self.refresh_zone_selector()
        self.log_panel.add_log(f"{deleted_name} {Messages.ZONE_DELETED_SUFFIX}")

    def refresh_zone_selector(self, select_index=0):
        zone_names = [
            zone.name
            for zone in self.zone_repository.zones
        ] + [Messages.ADD_NEW_ZONE_OPTION]

        self.ui.zone_selector["values"] = (zone_names)

        max_index = len(zone_names) - 1

        select_index = max(
            0,
            min(select_index, max_index))

        self.ui.zone_selector.current(select_index)

        self.load_zone_into_editor()

    def get_points_from_editor(self):
        point_texts = (self.ui.get_point_texts())

        if len(point_texts) != 4:
            raise ValueError(Messages.INVALID_ZONE_POINTS)

        new_points = []

        for text_value in point_texts:
            if text_value.strip() == "":
                raise ValueError(Messages.INVALID_ZONE_POINTS)

            point = self.parse_point(text_value)
            new_points.append(point)

        return new_points

    def validate_zone_name(
        self,
        zone_name: str) -> None:

        if zone_name.strip() == "":
            raise ValueError(Messages.EMPTY_ZONE_NAME)

    def validate_zone_name_unique(
        self,
        zone_name: str,
        selected_index: int) -> None:

        for i, zone in enumerate(self.zone_repository.zones):
            if zone.name == zone_name and i != selected_index:
                raise ValueError(Messages.DUPLICATE_ZONE_NAME)

    def apply_zone_changes(self):
        selected_index = (
            self.ui.zone_selector.current())

        new_zone_name = (
            self.ui.get_zone_name())

        is_new_zone = (
            selected_index >= len(
                self.zone_repository.zones
            )
        )

        try:
            new_points = (self.get_points_from_editor())

            self.validate_zone_name(new_zone_name)

            self.validate_zone_name_unique(new_zone_name, selected_index)

        except ValueError as error:
            self.log_panel.add_log(self.get_validation_message(error))
            return

        try:
            if is_new_zone:
                self.engine.add_zone(new_zone_name, new_points)

                self.log_panel.add_log(
                    f"{new_zone_name} {Messages.ZONE_ADDED_SUFFIX}"
                )

            else:
                self.engine.update_zone(
                    selected_index,
                    new_zone_name,
                    new_points
                )

                self.log_panel.add_log(f"{new_zone_name} {Messages.ZONE_UPDATED_SUFFIX}")

        except Exception:
            self.log_panel.add_log(traceback.format_exc())
            return

        new_selection = (
            len(self.zone_repository.zones) - 1
            if is_new_zone
            else selected_index
        )

        self.refresh_zone_selector(new_selection)

    def get_validation_message(self,error: ValueError):

        messages = {
            Messages.INVALID_COORDINATE_FORMAT:
                Messages.INVALID_COORDINATE_FORMAT,

            Messages.COORDINATE_OUT_OF_BOUNDS:
                Messages.COORDINATE_OUT_OF_BOUNDS,

            Messages.EMPTY_ZONE_NAME:
                Messages.EMPTY_ZONE_NAME,

            Messages.INVALID_ZONE_POINTS:
                Messages.INVALID_ZONE_POINTS,

            Messages.DUPLICATE_ZONE_NAME:
                Messages.DUPLICATE_ZONE_NAME
        }

        return messages.get(str(error), Messages.VALIDATION_ERROR)
