# Parking Lot Intruder Detection System

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
- **Configurable Parameters:** Easily adjust thresholds, COM ports, parking area coordinates, and other settings directly in the code to fit different environments.

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
- **Operating System:** Software was used with Windows os only, but feel free to modify it to use on other os

### Python Libraries

- `pyserial`
- `matplotlib`
- `numpy`
- `re` (built-in)
- `collections` (built-in)
- `threading` (built-in)
- `queue` (built-in)
- `time` (built-in)
- `math` (built-in)

### Custom Modules

- `radar_interface`: A custom module/interface for interacting with the radar hardware. Ensure this module is correctly implemented and accessible.
- `radar_ui`: A custom module for radar visualization. Ensure this module is correctly implemented and accessible.

### Additional Tools

- **S-Center Application:** Used to verify and manage COM ports. Ensure you have S-Center installed to check COM port configurations before running the system.

## Installation

1. **Clone the Repository:**

   ```bash
   (https://github.com/Khokhlov-creator/Radar_and_BLE_integration.git)
   cd Radar_and_BLE_integration
   ```

2. **Create a Virtual Environment (Optional but Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install pyserial matplotlib numpy
   ```

4. **Ensure `radar_interface` and `radar_ui` are Available:**

   Make sure the `radar_interface.py` and `radar_ui.py` modules are present in the project directory or installed in your Python environment.

## Configuration

### Step 1: Verify COM Ports with S-Center

Before configuring the radar or running the system, ensure that the COM ports are correctly assigned and available.

1. **Install and Open S-Center Application:**

   - **Download:** [S-Center Application Download Link](https://www.u-blox.com/en/product/s-center)
   - **Installation:** Follow the installation instructions provided with the application.

2. **Check COM Port Assignments:**

   - Open S-Center and navigate to the COM port management section.
   - Verify that the following ports are assigned:
     - **BLE Station 1:** `COM_X`
     - **BLE Station 2:** `COM_Y`
     - **Radar:** `COM_Z`
   - If these ports are not assigned, adjust them accordingly or note the assigned ports for later configuration.

### Step 2: Configure and Test the Radar

Before running the main intruder detection system, configure and verify the radar setup.

1. **Navigate to the Radar Directory:**

   ```bash
   cd radar
   ```

2. **Locate the Radar Configuration Files:**

   All radar configuration files are located in the `radar/tdm` directory since the system uses Time-Division Multiplexing (TDM) instead of Direct-Division Multiplexing (DDM).

   ```bash
   radar/tdm/profile_2d_3AzimTx.cfg
   ```

3. **Modify Configuration Files (If Needed):**

   If you need to test different radar settings, edit the configuration files within the `radar/tdm` directory.

   ```bash
   nano tdm/profile_2d_3AzimTx.cfg  # Replace with your preferred text editor
   ```

   **Configuration Parameters Explanation:**

   - **Radar Configuration (`rad.py`):**

     ```python
     RADAR_CONFIG = "./tdm/profile_2d_3AzimTx.cfg"
     BAUD_RATE_CON = 115200
     BAUD_RATE_DAT = 921600
     con_timeout = 0.01
     dat_timeout = 1
     configDataPort = f"configDataPort {BAUD_RATE_DAT} 0"
     ```

     - **RADAR_CONFIG:** Path to the radar configuration `.cfg` file.
     - **BAUD_RATE_CON:** Baud rate for radar configuration communication.
     - **BAUD_RATE_DAT:** Baud rate for radar data communication.
     - **con_timeout:** Configuration communication timeout.
     - **dat_timeout:** Data communication timeout.
     - **configDataPort:** Command string to set the data port configuration.

4. **Run the Radar Configuration Script:**

   As the first step, start the radar configuration and testing by running the `rad.py` script. This will configure the radar and provide a visualization of what the radar detects.

   ```bash
   python rad.py
   ```

   **Script Execution Steps:**

   1. **Configure the Radar:**
      - Sends configuration commands to the radar based on the specified `.cfg` file.
      - Ensures the radar starts correctly and is ready to send data.

   2. **Visualize Radar Data:**
      - Launches the radar UI to display radar detections in real-time.
      - Allows you to verify that the radar is accurately detecting objects within its range.

   **Note:**
   - Ensure that the COM ports are correctly set in the script or verify them using the Device manager of your pc before running.
   - If the fixed ports `COM19` (config) and `COM18` (data) are not accessible, the script will prompt an error and exit. Make sure these ports are free or adjust them in the script as needed.

## Usage

### Step 1: Configure and Test the Radar

As outlined in the [Configuration](#configuration) section, start by running the radar configuration script to ensure the radar is set up correctly and to visualize radar detections.

```bash
python radar/rad.py
```

This script will:

1. **Configure the Radar:**
   - Sends configuration commands to the radar based on the specified `.cfg` file.
   - Ensures the radar starts correctly and is ready to send data.

2. **Visualize Radar Data:**
   - Launches the radar UI to display radar detections in real-time.
   - Allows you to verify that the radar is accurately detecting objects within its range.

### Step 2: Run the Intruder Detection System

After verifying the radar setup:

1. **Navigate to the Project Root Directory:**

   ```bash
   cd ..
   ```

2. **Run the Intruder Detection Script:**

   ```bash
   python implementation/final.py
   ```

   **Script Execution Steps:**

   1. **Start BLE Listening Threads:**
      - Two threads listen to BLE data from the specified COM ports (`COM_X` and `COM_Y` by default).
      - BLE messages are parsed to extract tag IDs and azimuth angles.

   2. **Start Radar Reading Thread:**
      - A separate thread reads radar data from the specified COM port (`COM_Z` by default).
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

1. **COM Ports Verification:**
   - **Issue:** Unable to open specified COM ports.
   - **Solution:**
     - Use the **S-Center Application** to verify that the COM ports are correctly assigned and not in use by other applications.
     - Ensure that the COM ports specified in the code (`COM_X`, `COM_Y`, `COM_Z`) match those assigned to the BLE stations and radar.

2. **Serial Port Errors:**
   - **Issue:** Unable to open specified COM ports.
   - **Solution:** Ensure that the devices (BLE stations and radar) are correctly connected to the specified COM ports and that no other application is using them.

3. **Radar Interface Issues:**
   - **Issue:** Radar data not being read or parsed correctly.
   - **Solution:**
     - Verify the implementation of the `RadarInterface` module and ensure it matches the radar's communication protocol.
     - Check the radar configuration files in `radar/tdm` for correctness.

4. **No Intruder Detection:**
   - **Issue:** Intruders are not being detected even when present.
   - **Solution:**
     - Check if `INTRUDER_THRESHOLD` is set appropriately.
     - Ensure that untagged objects are within the parking area and are being detected as red points.
     - Verify the `PROXIMITY_THRESHOLD` to accurately count unique points.

5. **Performance Issues:**
   - **Issue:** Script runs slowly or the plot lags.
   - **Solution:**
     - Optimize the proximity check in `is_unique_point` (e.g., using spatial indexing like KD-trees).
     - Reduce the `FuncAnimation` update interval if necessary.

6. **Visualization Problems:**
   - **Issue:** Plot does not display correctly or annotations are misplaced.
   - **Solution:**
     - Verify parking area coordinates and ensure they match the real-world setup.
     - Adjust plot limits (`ax.set_xlim`, `ax.set_ylim`) as needed.

7. **Configuration File Errors:**
   - **Issue:** Radar configuration commands are not being applied correctly.
   - **Solution:**
     - Ensure that the configuration files are correctly formatted and located in the `radar/tdm` directory.
     - Check for any syntax errors or incorrect parameters in the `.cfg` files.

## Contact

For any inquiries or support, please contact [khokhdmi@fel.cvut.cz](mailto:khokhdmi@fel.cvut.cz).

# Additional Information

### Radar Configuration File Reference

In the provided radar configuration code (`rad.py`), the radar configuration file is specified as follows:

```python
RADAR_CONFIG = "./tdm/profile_2d_3AzimTx.cfg"
```

All radar configuration files are stored in the `radar/tdm` directory. If you wish to test different radar settings or modify the existing configuration, edit the corresponding `.cfg` files within this directory.

For example, to change the radar profile, you might modify `profile_2d_3AzimTx.cfg` or add new configuration files as needed.

Ensure that any changes to the configuration files are compatible with your radar hardware and do not disrupt the communication protocol.

### Radar Configuration Script (`rad.py`) Overview

The `rad.py` script is responsible for configuring the radar hardware and providing a visualization of radar detections.


## Summary

This updated README provides clear, concise instructions tailored to your project's final implementation located at `implementation/final.py`. It includes:

1. **Using the S-Center Application** to verify and manage COM ports.
2. **Configuring and Testing the Radar** using the `rad.py` script before running the main intruder detection system.
3. **Modifying Radar Configuration Files** located in the `radar/tdm` directory for testing and customization purposes.
4. **Running the Intruder Detection System** with step-by-step guidance.
