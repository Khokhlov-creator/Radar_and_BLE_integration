# Parking Lot Intruder Detection System

![Parking Intruder Detection](https://via.placeholder.com/800x200.png?text=Parking+Lot+Intruder+Detection+System)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Intruder Detection Logic](#intruder-detection-logic)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

The **Parking Lot Intruder Detection System** is a Python-based solution designed to monitor parking areas using Bluetooth Low Energy (BLE) tags and radar data. It visualizes the positions of tagged vehicles, detects untagged objects (potential intruders), and provides real-time alerts based on predefined thresholds. The system leverages BLE triangulation and radar point detections to ensure accurate monitoring and reliable intruder detection.

## Features

- **BLE Tag Parsing & Triangulation:** Reads BLE signals from two stations to triangulate the positions of tagged vehicles.
- **Radar Data Integration:** Processes radar detections to identify objects within the parking area.
- **Real-Time Visualization:** Displays BLE-tagged positions, radar detections, and parking area on an interactive Matplotlib plot.
- **Intruder Detection:** Cumulatively counts unique untagged (red) points within the parking area and flags intruders when thresholds are exceeded.
- **Reset Mechanism:** Automatically resets intruder counts and annotations when a tagged vehicle is detected within the parking area.
- **Configurable Parameters:** Easily adjust thresholds, COM ports, parking area coordinates, and other settings to fit different environments.

## Architecture

![System Architecture](https://via.placeholder.com/800x400.png?text=System+Architecture+Diagram)

1. **BLE Stations:**
   - Two BLE stations receive signals from BLE tags attached to vehicles.
   - Signals are parsed to extract azimuth angles, which are then used to triangulate the vehicle's position.

2. **Radar System:**
   - Captures point detections within the parking area.
   - Processes these points to identify tagged (green) and untagged (red) objects.

3. **Visualization & Detection:**
   - Real-time plotting of BLE-tagged positions and radar detections.
   - Intruder detection logic based on the cumulative count of unique untagged points within the parking area.

## Prerequisites

- **Python Version:** Python 3.7 or higher
- **Operating System:** Windows, Linux, or macOS

### Python Libraries

- `pyserial`
- `matplotlib`
- `numpy`
- `regex` (built-in `re` module is used)
- `collections` (built-in)
- `threading` (built-in)
- `queue` (built-in)
- `time` (built-in)

### Custom Modules

- `radar_interface`: A custom module/interface for interacting with the radar hardware. Ensure this module is correctly implemented and accessible.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/parking-intruder-detection.git
   cd parking-intruder-detection
   ```

2. **Create a Virtual Environment (Optional but Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   **Note:** If you don't have a `requirements.txt`, you can install the necessary libraries individually:

   ```bash
   pip install pyserial matplotlib numpy
   ```

4. **Ensure `radar_interface` is Available:**

   Make sure the `radar_interface.py` module is present in the project directory or installed in your Python environment.

## Configuration

Before running the script, adjust the configuration parameters as per your setup.

1. **COM Ports:**

   - **BLE Ports:**
     - `BLE_PORT1`: COM port for BLE Station 1 (default: `"COM27"`)
     - `BLE_PORT2`: COM port for BLE Station 2 (default: `"COM30"`)
   - **Radar Port:**
     - `RADAR_PORT`: COM port for Radar (default: `"COM18"`)

   **Example:**

   ```python
   BLE_PORT1 = "COM27"
   BLE_PORT2 = "COM30"
   RADAR_PORT = "COM18"
   ```

2. **Parking Area Coordinates:**

   Define the parking area's boundaries as `(xmin, xmax, ymin, ymax)`.

   ```python
   PARKING_PLACE = (2, 4, -20, -10)  # Example coordinates
   ```

3. **Intruder Detection Parameters:**

   - `INTRUDER_THRESHOLD`: Number of unique untagged points to declare an intruder (default: `20`)
   - `PROXIMITY_THRESHOLD`: Distance to consider points as unique (default: `0.5` units)

   **Example:**

   ```python
   INTRUDER_THRESHOLD = 20
   PROXIMITY_THRESHOLD = 0.5
   ```

4. **Radar Configuration:**

   - `RADAR_BAUD_RATE`: Baud rate for radar communication (default: `921600`)

   ```python
   RADAR_BAUD_RATE = 921600
   ```

5. **BLE Stations Positions:**

   Define the positions of BLE stations for triangulation.

   ```python
   STATION1_POSITION = (0, 0)
   STATION2_POSITION = (10, 0)
   ```

6. **Trail and Persistence Durations:**

   - `TRAIL_DURATION`: Duration (in seconds) to keep track of BLE tag trails (default: `3`)
   - `PERSISTENCE_DURATION`: Duration (in seconds) to retain radar points after they are no longer detected (default: `2.0`)

   ```python
   TRAIL_DURATION = 3
   PERSISTENCE_DURATION = 2.0
   ```

## Usage

Run the script using Python:

```bash
python intruder_detection.py
```

**Script Execution Steps:**

1. **Start BLE Listening Threads:**
   - Two threads listen to BLE data from the specified COM ports.
   - BLE messages are parsed to extract tag IDs and azimuth angles.

2. **Start Radar Reading Thread:**
   - A separate thread reads radar data from the specified COM port.
   - Radar points are parsed and queued for processing.

3. **Launch Visualization & Intruder Detection:**
   - An interactive Matplotlib window displays:
     - BLE-tagged vehicle positions with trails and auras (green).
     - Radar detections as scatter points (green for tagged, red for untagged).
     - Parking area boundaries.
   - Intruder detection annotations appear when the threshold is exceeded.

4. **Terminate Execution:**
   - Close the Matplotlib window to gracefully terminate all threads and exit the script.

## Intruder Detection Logic

The system detects intruders based on the cumulative count of **unique untagged (red) points** detected within the parking area across all frames. Here's how it works:

1. **Detection of Points:**
   - **Tagged Points (Green):** Points within the parking area that fall inside the BLE aura ellipses, indicating legitimate vehicles.
   - **Untagged Points (Red):** Points within the parking area that do not fall inside any BLE aura, indicating potential intruders.

2. **Unique Point Counting:**
   - Each unique untagged (red) point within the parking area is counted only once, regardless of how many frames it appears in.
   - A proximity threshold (`PROXIMITY_THRESHOLD`) ensures that points close to each other are considered the same object to avoid overcounting.

3. **Intruder Flagging:**
   - When the cumulative count of unique untagged points exceeds the `INTRUDER_THRESHOLD`, the system flags an intruder by displaying an "Intruder Detected" annotation on the plot.

4. **Reset Mechanism:**
   - Detection of any tagged (green) point within the parking area resets the unique untagged point count and removes the intruder annotation, assuming the presence of a legitimate vehicle.

### Example Scenario

- **Scenario:**
  - An untagged object (e.g., a car) enters the parking area.
  - The radar detects this object as a set of red points.
  - Each unique detection increments the cumulative count.
  - Once the count exceeds 20, the system flags an intruder.
  - If a legitimate vehicle (with a BLE tag) arrives and is detected within the parking area, the system resets the count and removes the intruder flag.

## Troubleshooting

1. **Serial Port Errors:**
   - **Issue:** Unable to open specified COM ports.
   - **Solution:** Ensure that the devices (BLE stations and radar) are correctly connected to the specified COM ports and that no other application is using them.

2. **Radar Interface Issues:**
   - **Issue:** Radar data not being read or parsed correctly.
   - **Solution:** Verify the implementation of the `RadarInterface` module and ensure it matches the radar's communication protocol.

3. **No Intruder Detection:**
   - **Issue:** Intruders are not being detected even when present.
   - **Solution:**
     - Check if `INTRUDER_THRESHOLD` is set appropriately.
     - Ensure that untagged objects are within the parking area and are being detected as red points.
     - Verify the `PROXIMITY_THRESHOLD` to accurately count unique points.

4. **Performance Issues:**
   - **Issue:** Script runs slowly or the plot lags.
   - **Solution:**
     - Optimize the proximity check in `is_unique_point` (e.g., using spatial indexing like KD-trees).
     - Reduce the `FuncAnimation` update interval if necessary.

5. **Visualization Problems:**
   - **Issue:** Plot does not display correctly or annotations are misplaced.
   - **Solution:**
     - Verify parking area coordinates and ensure they match the real-world setup.
     - Adjust plot limits (`ax.set_xlim`, `ax.set_ylim`) as needed.
