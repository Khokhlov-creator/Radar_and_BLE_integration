import math


def calculate_object_position(x1, x2, alpha, beta, l):
    """
    Calculate the position of the object in 2D space given anchors aligned along the Y-axis.

    Parameters:
    - x1, x2: X-coordinates of the anchors (y-coordinates are both 0)
    - alpha: Angle at the first anchor (in degrees)
    - beta: Angle at the second anchor (in degrees)
    - l: Distance between the two anchors

    Returns:
    - (X, Y): Coordinates of the object
    """
    # Convert angles from degrees to radians
    alpha_rad = math.radians(alpha)
    beta_rad = math.radians(beta)

    # Calculate distance (d) to the object
    d = l * (math.sin(alpha_rad) * math.sin(beta_rad)) / math.sin(alpha_rad + beta_rad)

    # Calculate the X and Y coordinates of the object relative to the first anchor
    X_rel = d * math.cos(alpha_rad)
    Y_rel = d * math.sin(alpha_rad)

    # Adjust the X-coordinate based on the global position of the first anchor
    X = x1 + X_rel
    print("D is", d)
    return X, Y_rel


# Example Usage:
# Coordinates of the anchors
x1 = 0  # Anchor A
x2 = 10  # Anchor B
l = x2 - x1  # Distance between anchors

# Angles at the anchors in degrees
alpha = -37  # Angle at A
beta = 77  # Angle at B

# Calculate position
object_position = calculate_object_position(x1, x2, alpha, beta, l)
print("Object Position (X, Y):", object_position)
