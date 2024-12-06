import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import defaultdict
import time

# Configuration
TRAIL_DURATION = 3  # Trail duration in seconds
ANCHORS = {
    "Station 1": (0, 0),   # Position of Station 1 (X1, Y1)
    "Station 2": (10, 0),  # Position of Station 2 (X2, Y2)
}

# Store recent triangulated positions for each tag
tag_positions = defaultdict(list)  # tag_id -> [(timestamp, x, y)]


def add_tag_position(tag_id, x, y, timestamp):
    """
    Add a new triangulated position for a tag and remove outdated points.
    """
    # Add the new position
    tag_positions[tag_id].append((timestamp, x, y))

    # Remove points older than TRAIL_DURATION
    tag_positions[tag_id] = [
        (t, px, py) for t, px, py in tag_positions[tag_id] if timestamp - t <= TRAIL_DURATION
    ]


def simulate_data():
    """
    Simulates triangulated data for demonstration purposes.
    Replace this with real data fetching logic.
    """
    import random
    timestamp = time.time()
    for i in range(3):  # Simulate 3 tags
        x = random.uniform(-10, 20)
        y = random.uniform(-10, 10)
        tag_id = f"Tag-{i+1}"
        add_tag_position(tag_id, x, y, timestamp)


def create_plot():
    """
    Create and update a Matplotlib plot for visualizing triangulated tag positions in real time.
    """
    # Initialize Matplotlib figure
    fig, ax = plt.subplots()
    ax.set_xlim(-10, 20)  # Adjust as needed for the station layout
    ax.set_ylim(-10, 10)
    ax.set_xlabel("X Position (m)")
    ax.set_ylabel("Y Position (m)")
    ax.set_title("Real-Time Tag Position Visualization with Anchors")

    def update_plot(frame):
        """
        Update the scatter plot with triangulated positions.
        """
        simulate_data()  # Simulate data (replace with real data fetching)
        ax.clear()
        ax.set_xlim(-10, 20)
        ax.set_ylim(-10, 10)
        ax.set_xlabel("X Position (m)")
        ax.set_ylabel("Y Position (m)")
        ax.set_title("Real-Time Tag Position Visualization with Anchors")

        # Plot anchor positions
        for anchor_name, (x, y) in ANCHORS.items():
            ax.scatter(x, y, c="red", marker="^", s=100, label=anchor_name)  # Anchors as red triangles
            ax.text(x, y + 0.5, anchor_name, color="red", fontsize=10, ha="center")  # Anchor labels

        # Plot data for each tag
        for tag_id, positions in tag_positions.items():
            if positions:
                _, x_vals, y_vals = zip(*positions)
                ax.plot(x_vals, y_vals, label=f"{tag_id} Trail", alpha=0.7)  # Trail
                ax.scatter(x_vals[-1], y_vals[-1], label=f"{tag_id} Current", alpha=1.0)  # Current position

        ax.legend(loc="upper right")

    # Animate the plot
    ani = FuncAnimation(fig, update_plot, interval=500)  # Update every 500 ms
    plt.show()


def main():
    """
    Main function to start the visualization.
    """
    create_plot()


if __name__ == "__main__":
    main()
