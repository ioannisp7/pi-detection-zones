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

        polygon_mask = np.zeros(
            (
                self.frame_height,
                self.frame_width
            ),
            dtype=np.uint8
        )

        cv2.fillPoly(
            polygon_mask,
            [points_np],
            255
        )

        total_pixels = cv2.countNonZero(polygon_mask)

        self.points_np = points_np
        self.polygon_mask = polygon_mask
        self.total_pixels = total_pixels


class ZoneRepository:
    def __init__(
        self,
        frame_width,
        frame_height):

        self.frame_width = frame_width
        self.frame_height = frame_height

        self.zones: list["Zone"] = []

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

        zone = self.zones[index]
        deleted_name = zone.name
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

        if "zones" not in layout_data:
            raise ValueError(Messages.INVALID_LAYOUT_FILE)

        if not isinstance(layout_data["zones"], list):

            raise ValueError(Messages.ZONES_AS_LIST)

        zones = []

        for zone_data in layout_data["zones"]:
            if not isinstance(zone_data, dict):

                raise ValueError(Messages.INVALID_ZONE_FORMAT)

            if ("name" not in zone_data or "points" not in zone_data):
                raise ValueError(Messages.INVALID_ZONE_FORMAT)

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

                if (not isinstance(point[0], int) or not isinstance(point[1], int)):
                    raise ValueError(Messages.POINTS_AS_INTEGERS)

            zone = Zone(
                zone_data["name"],
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

        self.frame_width = frame_width
        self.frame_height = frame_height
        self.zone_repository = ZoneRepository(frame_width,frame_height)
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
        self.zone_states.setdefault(zone_name,self.create_empty_state())

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

        self.background_frame = (
            cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )
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

        occupancy_ratio = (occupancy_pixels / total_zone_pixels)

        occupied = (
            occupancy_ratio >
            AppConfig.OCCUPANCY_PERCENT
        )

        return {
            "occupied": occupied,
            "occupancy_pixels": occupancy_pixels,
            "occupancy_ratio": occupancy_ratio
        }

    def process_all_zones(self,motion_frame):
        results = []
        events = []

        for zone in self.zone_repository.zones:
            zone_mask = cv2.bitwise_and(
                motion_frame,
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
                events.append(f"Object ENTERED {zone.name}")

            elif previous and not current:
                events.append(f"Object EXITED {zone.name}")

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

        old_name = (self.zone_repository.zones[index].name)

        self.zone_repository.update_zone(
            index,
            name,
            points
        )

        if old_name != name:
            self.rename_zone(old_name, name)

    def delete_zone(self, index):
        zone_name = (self.zone_repository.zones[index].name)

        self.zone_repository.delete_zone(index)
        self.remove_zone(zone_name)

    def load_layout(self, file_path):
        self.zone_repository.load_layout(file_path)
        self.rebuild_zone_states()
