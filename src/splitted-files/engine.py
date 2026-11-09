import cv2
import json
import numpy as np
from dataclasses import dataclass
from config import AppConfig, Messages

class MotionDetectionPipeline:
    def process(
        self,
        frame: np.ndarray,
        background_frame: np.ndarray | None):

        if background_frame is None:
            return None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(background_frame, gray)

        _, motion_mask = cv2.threshold(
            diff,
            AppConfig.DIFF_THRESHOLD,
            255,
            cv2.THRESH_BINARY)

        if AppConfig.USE_CLEANUP:
            motion_mask = cv2.morphologyEx(
                motion_mask,
                cv2.MORPH_OPEN,
                AppConfig.MORPH_KERNEL)

        return motion_mask


@dataclass
class Zone:
    name: str
    points: list[list[int]]
    frame_width: int
    frame_height: int

    def __post_init__(self):
        self.rebuild_geometry()

    def update_points(
        self,
        new_points: list[list[int]]) -> None:

        self.points = new_points
        self.rebuild_geometry()

    def rebuild_geometry(self) -> None:
        points_np = np.array(self.points, dtype=np.int32)

        # Bounding box of the zone, clipped to the frame. Only pixels inside it can belong to the zone,
        # so detection only needs to look at this part of the frame
        x, y, width, height = cv2.boundingRect(points_np)

        left = max(x, 0)
        top = max(y, 0)
        right = min(x + width, self.frame_width)
        bottom = min(y + height, self.frame_height)

        # Zone completely outside the frame: use a 1x1 empty mask, so it is never occupied
        if right <= left or bottom <= top:
            left, top, right, bottom = 0, 0, 1, 1

        # Polygon mask the size of the bounding box. Points are shifted so the box starts at (0, 0)
        polygon_mask = np.zeros(
            (
                bottom - top,
                right - left
            ),
            dtype=np.uint8
        )

        cv2.fillPoly(
            polygon_mask,
            [points_np - np.array([left, top], dtype=np.int32)],
            255
        )

        total_pixels = cv2.countNonZero(polygon_mask)

        self.points_np = points_np
        self.bounding_box = (left, top, right, bottom)
        self.polygon_mask = polygon_mask
        self.total_pixels = total_pixels


class ZoneRepository:
    def __init__(
        self,
        frame_width,
        frame_height):

        self.frame_width = frame_width
        self.frame_height = frame_height

        self.zones: list[Zone] = []

    def add_zone(
        self,
        name: str,
        points: list[list[int]]) -> None:

        zone = Zone(
            name,
            points,
            self.frame_width,
            self.frame_height)
        self.zones.append(zone)

    def update_zone(
        self,
        index: int,
        name: str,
        points: list[list[int]]) -> None:

        zone = self.zones[index]

        zone.name = name

        zone.update_points(points)

    def delete_zone(self, index: int) -> None:
        del self.zones[index]

    def save_layout(self, file_path: str) -> None:

        zones_to_save = []

        for zone in self.zones:
            zones_to_save.append({
                "name": zone.name,
                "points": zone.points})

        layout_data = {"zones": zones_to_save}

        with open(file_path, "w") as file:
            json.dump(
                layout_data,
                file,
                indent=4)

    def load_layout(self, file_path: str) -> None:
        with open(file_path, "r") as file:
            layout_data = json.load(file)

        if not isinstance(layout_data, dict):
            raise ValueError(Messages.LAYOUT_NOT_OBJECT)

        if "zones" not in layout_data:
            raise ValueError(Messages.INVALID_LAYOUT_FILE)

        if not isinstance(layout_data["zones"], list):
            raise ValueError(Messages.ZONES_AS_LIST)

        zones = []
        zone_names = set()

        for zone_data in layout_data["zones"]:
            if not isinstance(zone_data, dict):
                raise ValueError(Messages.INVALID_ZONE_FORMAT)

            if "name" not in zone_data or "points" not in zone_data:
                raise ValueError(Messages.INVALID_ZONE_FORMAT)

            # Zone name: same rules as the zone editor (not empty, unique)
            name = zone_data["name"]

            if not isinstance(name, str):
                raise ValueError(Messages.LAYOUT_ZONE_NAME_NOT_TEXT)

            if name.strip() == "":
                raise ValueError(Messages.LAYOUT_EMPTY_ZONE_NAME)

            if name in zone_names:
                raise ValueError(Messages.LAYOUT_DUPLICATE_ZONE_NAME.format(zone_name=name))

            zone_names.add(name)

            points = zone_data["points"]

            if not isinstance(points, list):
                raise ValueError(Messages.POINTS_AS_LIST)

            if len(points) != 4:
                raise ValueError(Messages.ZONE_CONTAIN_4_POINTS)

            for point in points:
                if not isinstance(point, list):
                    raise ValueError(Messages.POINT_AS_LIST)

                if len(point) != 2:
                    raise ValueError(Messages.ZONE_CONTAIN_XY)

                for value in point:
                    # bool is a subclass of int in Python, so true/false would otherwise pass as 1/0
                    if isinstance(value, bool) or not isinstance(value, int):
                        raise ValueError(Messages.POINTS_AS_INTEGERS)

                # Same bounds as the zone editor: inside the camera frame
                x, y = point

                if not (0 <= x < self.frame_width and 0 <= y < self.frame_height):
                    raise ValueError(
                        Messages.LAYOUT_POINT_OUT_OF_BOUNDS.format(
                            zone_name=name,
                            width=self.frame_width,
                            height=self.frame_height
                        )
                    )

            zone = Zone(
                name,
                points,
                self.frame_width,
                self.frame_height
            )

            zones.append(zone)

        self.zones = zones


class DetectionEngine:

    def __init__(
        self,
        frame_width,
        frame_height):

        self.zone_repository = ZoneRepository(frame_width, frame_height)
        self.pipeline = MotionDetectionPipeline()
        self.zone_states = {}
        self.background_frame = None
        self.detection_enabled = False

    def create_empty_state(self):
        return {
            "occupied": False,
            "occupancy_pixels": 0,
            "occupancy_ratio": 0
        }

    def ensure_zone_exists(self, zone_name):
        self.zone_states.setdefault(zone_name, self.create_empty_state())

    def remove_zone(self, zone_name):
        if zone_name in self.zone_states:
            del self.zone_states[zone_name]

    def rename_zone(
        self,
        old_name,
        new_name):

        state = self.zone_states.pop(
            old_name,
            self.create_empty_state()
        )

        self.zone_states[new_name] = state

    def rebuild_zone_states(self):
        self.zone_states.clear()
        for zone in self.zone_repository.zones:
            self.ensure_zone_exists(zone.name)

    def update_zone_state(
        self,
        zone_name,
        occupancy_result):

        self.ensure_zone_exists(zone_name)
        state = self.zone_states[zone_name]
        previous = state["occupied"]

        state["occupied"] = occupancy_result["occupied"]
        state["occupancy_pixels"] = occupancy_result["occupancy_pixels"]
        state["occupancy_ratio"] = occupancy_result["occupancy_ratio"]

        return previous

    def enable_detection(self):
        self.detection_enabled = True

    def capture_background_reference(self, frame) -> bool:
        if frame is None:
            return False

        self.background_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        return True

    def process_detection(self, frame):
        if not self.detection_enabled:
            empty_results = self.build_empty_results()
            return {
                "raw_frame": frame,
                "motion_mask": None,
                "zone_results": empty_results,
                "events": []
            }

        motion_mask = self.pipeline.process(
            frame,
            self.background_frame
        )

        zone_results, events = self.process_all_zones(motion_mask)

        return {
            "raw_frame": frame,
            "motion_mask": motion_mask,
            "zone_results": zone_results,
            "events": events
        }

    def analyze_zone(
        self,
        zone_mask: np.ndarray,
        total_zone_pixels: int):

        occupancy_pixels = cv2.countNonZero(zone_mask)

        if total_zone_pixels == 0:
            return {
                "occupied": False,
                "occupancy_pixels": occupancy_pixels,
                "occupancy_ratio": 0
            }

        occupancy_ratio = occupancy_pixels / total_zone_pixels

        occupied = (
            occupancy_ratio >
            AppConfig.OCCUPANCY_PERCENT
        )

        return {
            "occupied": occupied,
            "occupancy_pixels": occupancy_pixels,
            "occupancy_ratio": occupancy_ratio
        }

    def process_all_zones(self, motion_frame):
        results = []
        events = []

        for zone in self.zone_repository.zones:
            # Only compare the part of the motion mask inside the zone's bounding box
            left, top, right, bottom = zone.bounding_box

            zone_mask = cv2.bitwise_and(
                motion_frame[top:bottom, left:right],
                zone.polygon_mask
            )

            occupancy_result = self.analyze_zone(
                zone_mask,
                zone.total_pixels
            )

            previous = self.update_zone_state(
                zone.name,
                occupancy_result
            )

            current = occupancy_result["occupied"]

            if not previous and current:
                events.append(Messages.OBJECT_ENTERED.format(zone_name=zone.name))

            elif previous and not current:
                events.append(Messages.OBJECT_EXITED.format(zone_name=zone.name))

            results.append({
                "zone_name": zone.name,
                "occupied": current,
                "occupancy_pixels": occupancy_result["occupancy_pixels"],
                "occupancy_ratio": occupancy_result["occupancy_ratio"]
            })

        return results, events

    def add_zone(
        self,
        name,
        points):

        self.zone_repository.add_zone(name, points)
        self.ensure_zone_exists(name)

    def build_empty_results(self):
        results = []

        for zone in self.zone_repository.zones:
            result = self.create_empty_state()
            result["zone_name"] = zone.name
            results.append(result)

        return results

    def update_zone(
        self,
        index,
        name,
        points):

        old_name = self.zone_repository.zones[index].name

        self.zone_repository.update_zone(
            index,
            name,
            points
        )

        if old_name != name:
            self.rename_zone(old_name, name)

    def delete_zone(self, index):
        zone_name = self.zone_repository.zones[index].name

        self.zone_repository.delete_zone(index)
        self.remove_zone(zone_name)

    def load_layout(self, file_path):
        self.zone_repository.load_layout(file_path)
        self.rebuild_zone_states()
