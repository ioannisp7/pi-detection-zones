import cv2
import numpy as np

class AppConfig:
    # Camera resolution
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720

    # Camera window size. This is the nominal (maximum) preview size and also defines the preview aspect ratio.
    # When the application window is too small, the previews are scaled down to fit
    DISPLAY_WIDTH = 800
    DISPLAY_HEIGHT = 450

    # Padding in pixels around and between the preview areas and the right column
    LAYOUT_PADDING = 10

    # Smallest preview width allowed when the application window is very small
    MIN_PREVIEW_WIDTH = 160

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
    OBJECT_ENTERED = "Object ENTERED {zone_name}"
    OBJECT_EXITED = "Object EXITED {zone_name}"
    MOUSE_CLICK = "Mouse click: x={x}, y={y}"

    #Error messages
    POINTS_AS_LIST = "Invalid layout file: zone points must be a list"
    DUPLICATE_ZONE_NAME = "Zone name already exists"
    INVALID_COORDINATE_FORMAT = "Invalid coordinate format"
    COORDINATE_OUT_OF_BOUNDS = "Coordinate out of bounds"
    EMPTY_ZONE_NAME = "Zone name cannot be empty"
    INVALID_ZONE_POINTS = "Zone requires 4 valid points"
    INVALID_LAYOUT_FILE = "Invalid layout file: 'zones' entry is missing"
    ZONES_AS_LIST = "Invalid layout file: 'zones' must be a list"
    INVALID_ZONE_FORMAT = "Invalid layout file: each zone needs a 'name' and 'points'"
    ZONE_CONTAIN_4_POINTS = "Invalid layout file: each zone must have 4 points"
    POINT_AS_LIST = "Invalid layout file: each point must be a list [x, y]"
    ZONE_CONTAIN_XY = "Invalid layout file: each point must have an x and a y value"
    POINTS_AS_INTEGERS = "Invalid layout file: point coordinates must be whole numbers"
    VALIDATION_ERROR = "Validation error"
    LAYOUT_SAVE_FAILED = "Layout could not be saved: {error}"
    NO_CAMERA_FRAME = "No camera frame available, background not captured"
    CAMERA_CAPTURE_FAILED = "Camera frame capture failed"
