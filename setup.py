import random
from battlefield import ControlPoint

def setup_battlefield():
    # Battlefield dimensions
    battlefield_width = 60
    battlefield_height = 40

    # Grid size
    grid_width = 6    # 6 squares along the x-axis (0 to 5)
    grid_height = 4   # 4 squares along the y-axis (0 to 3)
    square_size = 10  # 10" per square

    # Random number of control points between 2 and 4
    num_control_points = random.randint(2, 4)

    control_points = []
    # Place control points in squares y=2 (middle rows)
    for _ in range(num_control_points):
        x_square = random.randint(0, 5)
        y_square = 2

        x_pos = x_square * square_size
        y_pos = y_square * square_size

        cp = ControlPoint(x_pos, y_pos, _+1)
        control_points.append(cp)

    return control_points, battlefield_width, battlefield_height

def place_units_randomly(player_a, player_b):
    square_size = 10
    def calculate_position(x_square, y_square):
        x_pos = x_square * square_size + random.uniform(0, square_size)
        y_pos = y_square * square_size + random.uniform(0, square_size)
        return (round(x_pos), round(y_pos))

    # Player A top row (y=0)
    for unit in player_a.units:
        x_square = random.randint(0, 5)
        unit.position = calculate_position(x_square, 0)

    # Player B bottom row (y=3)
    for unit in player_b.units:
        x_square = random.randint(0, 5)
        unit.position = calculate_position(x_square, 3)


def place_terrain(battlefield):
    # We roll 2D3: two random integers 1-3 each, summed.
    terrain_count = random.randint(1,3) + random.randint(1,3)  # 2 to 6 pieces

    # Terrain area between squares x=1..2 and y=1..2
    # That gives us a 2x2 area = 4 possible squares: (1,1), (1,2), (2,1), (2,2)
    possible_squares = [(1,1),(1,2),(2,1),(2,2)]
    random.shuffle(possible_squares)

    terrain_types = ["Forest", "Building", "Hard Cover"]

    terrain_map = []
    square_size = 10

    for _ in range(terrain_count):
        if not possible_squares:
            break
        x_sq, y_sq = possible_squares.pop()
        ttype = random.choice(terrain_types)
        x_pos = x_sq * square_size
        y_pos = y_sq * square_size
        # Each terrain is 10x10, same as a square
        terrain_map.append({
            "type": ttype,
            "x": x_pos,
            "y": y_pos,
            "width": 10,
            "height": 10
        })

    battlefield.terrain_map = terrain_map
