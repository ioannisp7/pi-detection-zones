import cv2
import numpy as np

class AppConfig:
    # Camera resolution
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720

    # Camera window size
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 450

    # Application window size
    WINDOW_WIDTH = 1250
    WINDOW_HEIGHT = 950

    # OpenCV font settings
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.7
    FONT_THICKNESS = 2
    MASK_FONT_SCALE = 0.6

    # Frame rate. Number increase, lowers refresh rate and CPU usage, also lowers detection accuracy
    GUI_UPDATE_DELAY = 30

    # Percentage of changed pixels required to mark a zone as occupied
    # 0.08 = 8%
    OCCUPANCY_PERCENT = 0.08

    # Difference threshold in pixel level. How different must ONE pixel become before it counts as changed
    # Larger value = less sensitive to image changes
    DIFF_THRESHOLD = 25

    # Enable/disable image cleanup
    USE_CLEANUP = True

    # Morphology kernel size. Defines aggressiveness of cleanup
    # Lower values remove tiny noise but keeps more detail. Higher values remove much more noise but damage image. 5 is
    # moderate cleanup strength
    KERNEL_SIZE = 5

    MAX_LOG_LINES = 300

    # Pre-created morphology kernel matrix
    MORPH_KERNEL = np.ones((KERNEL_SIZE, KERNEL_SIZE), np.uint8)
    
    # Colors (BGR format for OpenCV)
    COLOR_WHITE = (255, 255, 255)
    COLOR_GREEN = (30, 255, 0)
    COLOR_RED = (0, 0, 255)

  
class Messages:
    ADD_NEW_ZONE_OPTION = "Add new zone"
    LAYOUT_LOADED = "Layout loaded"
    LAYOUT_SAVED = "Layout saved"
    PREVIEW_STOPPED = "Preview stopped"
    PREVIEW_RESUMED = "Preview resumed"
    ZONE_ADDED_SUFFIX = "zone created"
    ZONE_UPDATED_SUFFIX = "zone updated"
    ZONE_DELETED_SUFFIX = "zone deleted"
    BACKGROUND_CAPTURED = "Background reference captured"
    DETECTION_ARMED = "Occupancy detection armed"
    INVALID_JSON_FILE = "Selected JSON file is invalid"
    EXITING = "Exiting"

    #Error messages
    POINTS_AS_LIST = "POINTS_AS_LIST"
    DUPLICATE_ZONE_NAME = "Zone name already exists"
    INVALID_COORDINATE_FORMAT = "Invalid coordinate format"
    COORDINATE_OUT_OF_BOUNDS = "COORDINATE_OUT_OF_BOUNDS"
    EMPTY_ZONE_NAME = "Zone name cannot be empty"
    INVALID_ZONE_POINTS = "Zone requires 4 valid points"
    INVALID_LAYOUT_FILE = "INVALID_LAYOUT_FILE"
    ZONES_AS_LIST = "ZONES_AS_LIST"
    INVALID_ZONE_FORMAT = "INVALID_ZONE_FORMAT"
    ZONE_CONTAIN_4_POINTS = "ZONE_CONTAIN_4_POINTS"
    POINT_AS_LIST = "POINT_AS_LIST"
    ZONE_CONTAIN_XY = "ZONE_CONTAIN_XY"
    POINTS_AS_INTEGERS = "POINTS_AS_INTEGERS"
    CAMERA_CAPTURE_FAILED = "Camera frame capture failed"
