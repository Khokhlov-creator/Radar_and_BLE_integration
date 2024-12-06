import serial
import re
import threading
import time
import queue
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math
from collections import defaultdict

# Configuration
BAUD_RATE = 115200
PORT1 = "COM30"  # Station 1 now on COM30
PORT2 = "COM27"  # Station 2 now on COM27
STATION1_POSITION = (0, 0)    # Station 1 position (X1, Y1)
STATION2_POSITION = (10, 0)   # Station 2 position (X2, Y2)
TRAIL_DURATION = 3            # Trail duration in seconds
TIME_THRESHOLD = 1            # seconds

# Regex patterns for parsing BLE messages
AZIMUTH_PATTERN = re.compile(
    r'\+UUDF:([0-9A-Fa-f]{12}),(-?\d+),(-?\d+),(-?\d+),(\d+),(\d+),"([0-9A-Fa-f]{12})","",(\d+),(\d+)'
)

# Shared queue for real-time visualization
data_queue = queue.Queue()

# Store recent data for each tag and station
station_data = defaultdict(lambda: {"station1": None, "station2": None})
tag_positions = defaultdict(list)


def convert_azimuth_to_math_angle(azimuth):
    """
    Convert azimuth angle measured clockwise from North to mathematical angle counter-clockwise from East.
    """
    math_angle = (90 - azimuth) % 360
    return math_angle


def parse_message(message, station):
    """
    Parse a BLE message and store azimuth data for triangulation.
    """
    match = AZIMUTH_PATTERN.match(message)
    if match:
        # Extract values from the message
        ed_instance_id = match.group(1)
        azimuth = int(match.group(3))
        math_angle = convert_azimuth_to_math_angle(azimuth)  # Convert azimuth
        timestamp = time.time()  # Current time for synchronization

        # Store azimuth data for the corresponding station
        if station == "1":
            station_data[ed_instance_id]["station1"] = {"azimuth": math_angle, "timestamp": timestamp}
        elif station == "2":
            station_data[ed_instance_id]["station2"] = {"azimuth": math_angle, "timestamp": timestamp}

        # Push the tag ID to the queue for visualization
        data_queue.put(ed_instance_id)

        # Output the received azimuth
        print(f"Station: {station} | Tag: {ed_instance_id} | Azimuth: {azimuth}° | Math Angle: {math_angle}°")


def read_from_port(port, station):
    """
    Read BLE data from the specified serial port.
    """
    while True:
        try:
            with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
                ser.reset_input_buffer()  # Flush input buffer
                print(f"Listening on {port} (Station {station})...")
                while True:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"Received: {line}")  # Received message
                        parse_message(line, station)
        except serial.SerialException as e:
            print(f"Error opening serial port {port}: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print(f"Stopping listening on {port}.")
            break


def triangulate_position(tag_id):
    """
    Calculate the position of the tag using triangulation based on AoA (azimuth angles).
    :param tag_id: The ID of the tag being triangulated
    :return: (X, Y) position of the tag or None if triangulation fails
    """
    # Retrieve azimuth data for the tag from both stations
    data1 = station_data[tag_id]["station1"]
    data2 = station_data[tag_id]["station2"]

    if not data1 or not data2:
        print(f"Not enough data for triangulation for Tag {tag_id}.")
        return None

    # Check if the data timestamps are within the threshold
    if abs(data1["timestamp"] - data2["timestamp"]) > TIME_THRESHOLD:
        print(f"Data for Tag {tag_id} is not synchronized (difference > {TIME_THRESHOLD} seconds).")
        return None

    # Extract azimuth angles and station positions
    theta1 = math.radians(data1["azimuth"])  # Convert to radians
    theta2 = math.radians(data2["azimuth"])  # Convert to radians
    X1, Y1 = STATION1_POSITION  # Station 1 position
    X2, Y2 = STATION2_POSITION  # Station 2 position

    try:
        # Define the coefficients matrix A and the constants vector B
        A = [
            [math.cos(theta1), -math.cos(theta2)],
            [math.sin(theta1), -math.sin(theta2)]
        ]
        B = [
            X2 - X1,
            Y2 - Y1
        ]

        # Calculate the determinant of A
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        EPSILON = 1e-6  # Define a small threshold
        if abs(det) < EPSILON:
            print(f"Azimuth angles result in parallel lines for Tag {tag_id}. Cannot triangulate.")
            return None

        # Compute the inverse of the determinant
        inv_det = 1 / det

        # Calculate t1 using Cramer's Rule
        t1 = (A[1][1] * B[0] - A[0][1] * B[1]) * inv_det
        # t2 = (-A[1][0] * B[0] + A[0][0] * B[1]) * inv_det  # Not used here

        # Calculate the intersection point (X, Y) using t1
        X = X1 + t1 * math.cos(theta1)
        Y = Y1 + t1 * math.sin(theta1)

        # Round the results for readability
        X = round(X, 2)
        Y = round(Y, 2)

        print(f"Triangulation for Tag {tag_id}: X = {X}, Y = {Y}")
        return (X, Y)

    except Exception as e:
        print(f"Error in triangulation for Tag {tag_id}: {e}")
        return None



def update_trail(tag_id, position):
    """
    Add new position for a tag and remove outdated positions based on TRAIL_DURATION.
    """
    current_time = time.time()
    tag_positions[tag_id].append((current_time, position))
    tag_positions[tag_id] = [
        (t, pos) for t, pos in tag_positions[tag_id] if current_time - t <= TRAIL_DURATION
    ]


def create_plot():
    """
    Create and update a Matplotlib plot for visualizing BLE tag positions in real time.
    """
    # Initialize Matplotlib figure
    fig, ax = plt.subplots()
    ax.set_xlim(0, 10)  # Adjust as needed for the station layout
    ax.set_ylim(-40, 0)
    ax.set_xlabel("X Position (m)")
    ax.set_ylabel("Y Position (m)")
    ax.set_title("BLE Real-Time Triangulation Visualization")

    # Plot anchors with distinct colors and markers
    ax.scatter(STATION1_POSITION[0], STATION1_POSITION[1], color="red", label="Station 1", marker="^", s=100)
    ax.scatter(STATION2_POSITION[0], STATION2_POSITION[1], color="blue", label="Station 2", marker="s", s=100)

    # Dictionaries to hold scatter and trail plots for each tag
    tag_scatter = {}
    tag_trails = {}
    azimuth_lines = {}  # To hold azimuth lines for each tag

    def update_plot(frame):
        """
        Update the scatter plot with new triangulated positions and azimuth lines.
        """
        while not data_queue.empty():
            tag_id = data_queue.get()
            position = triangulate_position(tag_id)
            if position:
                update_trail(tag_id, position)

        # Update tag plots
        for tag_id, positions in tag_positions.items():
            if positions:
                timestamps, coords = zip(*positions)
                x_vals, y_vals = zip(*coords)

                # Update trail
                if tag_id not in tag_trails:
                    tag_trails[tag_id], = ax.plot([], [], label=f"Tag {tag_id} Trail", alpha=0.7)
                tag_trails[tag_id].set_data(x_vals, y_vals)

                # Update current position
                if tag_id not in tag_scatter:
                    # Assign a unique color to each tag
                    color = plt.cm.tab10(len(tag_scatter) % 10)
                    tag_scatter[tag_id] = ax.scatter([], [], color=color, label=f"Tag {tag_id} Current",
                                                    alpha=1.0, edgecolors='k', s=50)
                tag_scatter[tag_id].set_offsets([x_vals[-1], y_vals[-1]])

                # Plot azimuth lines from Station 1 and Station 2
                data1 = station_data[tag_id]["station1"]
                data2 = station_data[tag_id]["station2"]
                if data1 and data2:
                    theta1 = math.radians(data1["azimuth"])
                    theta2 = math.radians(data2["azimuth"])
                    X1, Y1 = STATION1_POSITION
                    X2, Y2 = STATION2_POSITION

                    # Define two points far along each azimuth line for visualization
                    line_length = 100  # Fixed length for azimuth lines

                    # Azimuth line from Station 1
                    az1_x = [X1, X1 - line_length * math.cos(theta1)]
                    az1_y = [Y1, Y1 - line_length * math.sin(theta1)]

                    # Azimuth line from Station 2
                    az2_x = [X2, X2 - line_length * math.cos(theta2)]
                    az2_y = [Y2, Y2 - line_length * math.sin(theta2)]

                    if tag_id not in azimuth_lines:
                        azimuth_lines[tag_id] = {
                            "station1": ax.plot([], [], color="red", linestyle='--', linewidth=1)[0],
                            "station2": ax.plot([], [], color="blue", linestyle='--', linewidth=1)[0]
                        }

                    # Update azimuth lines
                    azimuth_lines[tag_id]["station1"].set_data(az1_x, az1_y)
                    azimuth_lines[tag_id]["station2"].set_data(az2_x, az2_y)

        # Redraw legend
        ax.legend(loc="upper right")

    ani = FuncAnimation(fig, update_plot, interval=100)  # Update every 100 ms
    plt.show()


def main():
    """
    Main function to read BLE data and visualize triangulated positions.
    """
    # Start the BLE readers in separate threads
    thread1 = threading.Thread(target=read_from_port, args=(PORT1, "1"), daemon=True)
    thread2 = threading.Thread(target=read_from_port, args=(PORT2, "2"), daemon=True)
    thread1.start()
    thread2.start()

    # Start the visualization
    create_plot()

    # Wait for the BLE readers to finish (if ever)
    thread1.join()
    thread2.join()


if __name__ == "__main__":
    main()
