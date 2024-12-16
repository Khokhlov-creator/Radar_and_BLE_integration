import serial
import re
import threading
import time
import queue
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math
import numpy as np
from collections import defaultdict
from matplotlib.patches import Ellipse

from radar.radar_interface import RadarInterface

# BLE Configuration
BLE_BAUD_RATE = 115200
BLE_PORT1 = "COM27"
BLE_PORT2 = "COM30"
STATION1_POSITION = (0, 0)
STATION2_POSITION = (10, 0)

# Time and Threshold Parameters
TRAIL_DURATION = 3
TIME_THRESHOLD = 1
PERSISTENCE_DURATION = 2.0
MOVEMENT_THRESHOLD = 0.5
# Removed ILLEGAL_WAIT_DURATION and STABILITY_DURATION as per new requirements
ILLEGAL_PERSISTENCE_DURATION = 10.0  # Keep showing intruder after disappearance

# Parking Place Coordinates
PARKING_PLACE = (2, 4, -20, -10)  # (xmin, xmax, ymin, ymax)

# Radar Configuration
RADAR_PORT = "COM18"
RADAR_BAUD_RATE = 921600

# Intruder Detection Parameters
INTRUDER_THRESHOLD = 20  # Number of unique red points to declare intruder
PROXIMITY_THRESHOLD = 0.5  # Distance to consider points as unique

# Data Structures
data_queue = queue.Queue()
station_data = defaultdict(lambda: {"station1": None, "station2": None})
tag_positions = defaultdict(list)
radar_positions = []

# Tracking Structures
point_history = {}
point_annotations = {}
parked_points = {}

# Intruder Detection Tracking
intruder_annotation = None
unique_parking_points = []  # List to store unique red points inside parking
intruder_flagged = False  # Flag to indicate if intruder has been flagged

# Regex Pattern for BLE Messages
AZIMUTH_PATTERN = re.compile(
    r'\+UUDF:([0-9A-Fa-f]{12}),'
    r'(-?\d+),(-?\d+),(-?\d+),'
    r'(\d+),(\d+),'
    r'"([0-9A-Fa-f]{12})","",(\d+),(\d+)'
)

def convert_azimuth_to_math_angle(azimuth):
    return (90 - azimuth) % 360

def parse_ble_message(message, station):
    match = AZIMUTH_PATTERN.match(message)
    if match:
        tag_id = match.group(1)
        azimuth = int(match.group(3))
        math_angle = convert_azimuth_to_math_angle(azimuth)
        timestamp = time.time()

        if station == "1":
            station_data[tag_id]["station1"] = {"azimuth": math_angle, "timestamp": timestamp}
        elif station == "2":
            station_data[tag_id]["station2"] = {"azimuth": math_angle, "timestamp": timestamp}

        data_queue.put(("BLE", tag_id))

def read_ble_port(port, station, stop_event):
    while not stop_event.is_set():
        try:
            with serial.Serial(port, BLE_BAUD_RATE, timeout=1) as ser:
                ser.reset_input_buffer()
                print(f"Listening on {port} (Station {station})...")
                while not stop_event.is_set():
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        parse_ble_message(line, station)
        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print(f"Stopping listening on {port}.")
            break

def triangulate_position(tag_id):
    data1 = station_data[tag_id]["station1"]
    data2 = station_data[tag_id]["station2"]

    if not data1 or not data2:
        return None

    if abs(data1["timestamp"] - data2["timestamp"]) > TIME_THRESHOLD:
        return None

    theta1 = math.radians(data1["azimuth"])
    theta2 = math.radians(data2["azimuth"])
    X1, Y1 = STATION1_POSITION
    X2, Y2 = STATION2_POSITION

    try:
        A = [
            [math.cos(theta1), -math.cos(theta2)],
            [math.sin(theta1), -math.sin(theta2)]
        ]
        B = [X2 - X1, Y2 - Y1]
        det = A[0][0]*A[1][1] - A[0][1]*A[1][0]

        if abs(det) < 1e-6:
            return None

        inv_det = 1/det
        t1 = (A[1][1]*B[0] - A[0][1]*B[1])*inv_det
        X = X1 + t1*math.cos(theta1)
        Y = Y1 + t1*math.sin(theta1)
        return (X, Y)
    except Exception as e:
        print(f"Error in triangulation for Tag {tag_id}: {e}")
        return None

def update_trail(tag_id, position):
    current_time = time.time()
    tag_positions[tag_id].append((current_time, position))
    tag_positions[tag_id] = [
        (t, pos) for t, pos in tag_positions[tag_id] if current_time - t <= TRAIL_DURATION
    ]

def read_radar_data(stop_event):
    global radar_positions
    radar_center = (5, 0)
    radar = RadarInterface(port=RADAR_PORT, baudrate=RADAR_BAUD_RATE)
    try:
        while not stop_event.is_set():
            raw_data = radar.read_data()
            parsed_results = radar.parse_frame(raw_data)
            if parsed_results and parsed_results[0] == 0:
                detectedX_array = parsed_results[7]
                detectedY_array = parsed_results[8]
                detected_points = [
                    (radar_center[0] - x*10, radar_center[1] - y*10)
                    for x, y in zip(detectedX_array, detectedY_array)
                ]
                radar_positions = detected_points
                data_queue.put(("Radar", detected_points))
    except KeyboardInterrupt:
        print("Stopping radar data collection.")
    finally:
        radar.close()

def point_in_parking(px, py, region):
    xmin, xmax, ymin, ymax = region
    return xmin <= px <= xmax and ymin <= py <= ymax

def is_unique_point(px, py, unique_points, threshold=PROXIMITY_THRESHOLD):
    for (ux, uy) in unique_points:
        distance = math.hypot(px - ux, py - uy)
        if distance < threshold:
            return False
    return True

def create_plot(stop_event):
    global intruder_annotation, unique_parking_points, intruder_flagged
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10)
    ax.set_ylim(-90, 0)
    ax.set_title("Parking Lot Visualization")

    # Plot BLE stations
    anchor_positions = [STATION1_POSITION, STATION2_POSITION]
    for i, (x, y) in enumerate(anchor_positions):
        ax.plot(x, y, 'D', label=f"Anchor {i+1}", color="purple", markersize=8)

    # Plot Radar center
    radar_center = (5, 2)
    ax.plot(radar_center[0], radar_center[1], 's', label="Radar", color="red", markersize=8)

    # Draw parking place for visualization
    rect = plt.Rectangle((PARKING_PLACE[0], PARKING_PLACE[2]),
                         PARKING_PLACE[1]-PARKING_PLACE[0],
                         PARKING_PLACE[3]-PARKING_PLACE[2],
                         fill=False, edgecolor='blue', linestyle='--', label="Parking Place")
    ax.add_patch(rect)

    radar_scatter = ax.scatter([], [], s=20, label="Radar Detections", alpha=0.7)

    ble_trails = {}
    ble_scatters = {}
    aura_ellipses = {}

    ax.legend(loc="upper right")

    # Initialize intruder tracking
    unique_parking_points = []
    intruder_annotation = None
    intruder_flagged = False

    def update(frame):
        global intruder_annotation, unique_parking_points, intruder_flagged
        current_time = time.time()

        # Process incoming data
        while not data_queue.empty():
            data_type, data_value = data_queue.get()
            if data_type == "BLE":
                position = triangulate_position(data_value)
                if position:
                    update_trail(data_value, position)

        # Remove old aura ellipses
        for tag_id, ellipse in aura_ellipses.items():
            ellipse.remove()
        aura_ellipses.clear()

        # Update BLE tags and their auras
        for tag_id, trail in tag_positions.items():
            if not trail:
                continue
            _, coords = zip(*trail)
            if tag_id not in ble_trails:
                ble_trails[tag_id], = ax.plot([], [], label=f"Tag {tag_id} Trail", alpha=0.7)
            ble_trails[tag_id].set_data(*zip(*coords))

            if tag_id not in ble_scatters:
                ble_scatters[tag_id] = ax.scatter([], [], label=f"Tag {tag_id} Current", edgecolor='k', s=50)
            ble_scatters[tag_id].set_offsets([coords[-1]])

            aura_ellipse = Ellipse(
                coords[-1],
                width=2,
                height=10,
                color="green",
                alpha=0.3
            )
            ax.add_patch(aura_ellipse)
            aura_ellipses[tag_id] = aura_ellipse

        new_points = radar_positions if radar_positions else []
        updated_keys = set()

        # Update detected points and track unique objects
        for (px, py) in new_points:
            inside_aura = False
            for ellipse in aura_ellipses.values():
                x0, y0 = ellipse.center
                aura_radius_x = ellipse.width / 2.0
                aura_radius_y = ellipse.height
                dx = (px - x0)/aura_radius_x
                dy = (py - y0)/aura_radius_y
                if dx**2 + dy**2 <= 1:
                    inside_aura = True
                    break
            color = "green" if inside_aura else "red"

            prev_info = point_history.get((px, py))
            if prev_info is None:
                # New point
                point_history[(px, py)] = {
                    'last_seen': current_time,
                    'color': color,
                    'prev_pos': (px, py),
                    'parking_enter_count': 0  # Initialize count
                }
            else:
                # Update existing point
                point_history[(px, py)]['last_seen'] = current_time
                point_history[(px, py)]['color'] = color

            updated_keys.add((px, py))

        # Build final list of points and handle expired points
        filtered_points = []
        filtered_colors = []
        expired_keys = []

        for (key_px, key_py), info in point_history.items():
            if (key_px, key_py) not in updated_keys:
                # Not updated this frame
                if current_time - info['last_seen'] <= PERSISTENCE_DURATION:
                    filtered_points.append((key_px, key_py))
                    filtered_colors.append(info['color'])
                else:
                    expired_keys.append((key_px, key_py))
            else:
                filtered_points.append((key_px, key_py))
                filtered_colors.append(info['color'])

        # Remove expired points from point_history and normal annotations
        for k in expired_keys:
            if k in point_annotations:
                point_annotations[k].remove()
                del point_annotations[k]
            if k in point_history:
                del point_history[k]

        current_set = set(filtered_points)

        # Intruder Detection Logic
        for (px, py), c in zip(filtered_points, filtered_colors):
            inside_parking = point_in_parking(px, py, PARKING_PLACE)
            untagged = (c == "red")

            if untagged and inside_parking:
                # Check if this point is unique
                if is_unique_point(px, py, unique_parking_points, PROXIMITY_THRESHOLD):
                    unique_parking_points.append((px, py))
                    intruder_count = len(unique_parking_points)
                    print(f"Unique red point detected at ({px:.1f}, {py:.1f}). Total unique red points: {intruder_count}")

                    if intruder_count > INTRUDER_THRESHOLD and not intruder_flagged:
                        print(f"Intruder detected! {intruder_count} unique red points inside parking.")
                        # Place annotation at the center of parking place
                        mid_x = (PARKING_PLACE[0] + PARKING_PLACE[1]) / 2
                        mid_y = (PARKING_PLACE[2] + PARKING_PLACE[3]) / 2
                        intruder_annotation = ax.text(mid_x, mid_y, "Intruder Detected", fontsize=12, color="red",
                                                     ha='center', va='center',
                                                     bbox=dict(facecolor='yellow', alpha=0.5))
                        intruder_flagged = True
            elif c == "green" and inside_parking:
                # Reset intruder detection
                if intruder_annotation:
                    intruder_annotation.remove()
                    intruder_annotation = None
                    print("Tagged vehicle detected inside parking. Intruder annotation removed.")
                unique_parking_points.clear()
                intruder_flagged = False

        # Handle parked_points that disappeared (optional, can be kept for other logic)
        for pt in list(parked_points.keys()):
            if pt not in current_set:
                info = parked_points[pt]
                # If absent too long, consider left
                if current_time - info['last_seen'] > ILLEGAL_PERSISTENCE_DURATION:
                    print(f"Intruder left the parking lot (previously at {pt})")
                    info['annot'].remove()
                    del parked_points[pt]

        # Update scatter plot
        if filtered_points:
            radar_scatter.set_offsets(filtered_points)
            radar_scatter.set_facecolors(filtered_colors)
        else:
            radar_scatter.set_offsets(np.empty((0, 2)))
            radar_scatter.set_facecolors([])

    ani = FuncAnimation(fig, update, interval=100, cache_frame_data=False)

    try:
        plt.show()
    except KeyboardInterrupt:
        print("Plot closed by user")

def main():
    stop_event = threading.Event()

    # Start BLE listening threads
    ble_thread1 = threading.Thread(target=read_ble_port, args=(BLE_PORT1, "1", stop_event), daemon=True)
    ble_thread2 = threading.Thread(target=read_ble_port, args=(BLE_PORT2, "2", stop_event), daemon=True)

    ble_thread1.start()
    ble_thread2.start()

    # Start Radar reading thread
    radar_thread = threading.Thread(target=read_radar_data, args=(stop_event,), daemon=True)
    radar_thread.start()

    # Start plotting and intruder detection
    create_plot(stop_event)

    # When plotting window is closed, signal threads to stop
    stop_event.set()
    ble_thread1.join(timeout=2)
    ble_thread2.join(timeout=2)
    radar_thread.join(timeout=2)
    print("Exiting main.")

if __name__ == "__main__":
    main()
