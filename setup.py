import random
from battlefield import ControlPoint

def setup_battlefield():
    # Battlefield dimensions
    battlefield_width = 60
    battlefield_height = 40

    # Grid size
    grid_width = 6    # 6 squares along the x-axis
    grid_height = 4   # 4 squares along the y-axis
    square_size = 10  # 10" per square

    # Random number of control points between 2 and 4
    num_control_points = random.randint(2, 4)

    control_points = []
    # Control points go into squares between x=0..5 and y=1..2
    # That gives a 6x2 area in the middle rows of the board
    for _ in range(num_control_points):
        x_square = random.randint(0, 5)  # horizontal squares from 0 to 5
        y_square = random.randint(1, 2)  # vertical squares 1 to 2

        # Random coordinates within the chosen square
        x_pos = x_square * square_size + random.uniform(0, square_size)
        y_pos = y_square * square_size + random.uniform(0, square_size)

        cp = ControlPoint(x_pos, y_pos)
        control_points.append(cp)

    return control_points, battlefield_width, battlefield_height

def place_units_randomly(player_a, player_b):
    # Unit placement:
    # Player A places units in the top row (y=0)
    # Player B places units in the bottom row (y=3)
    # Each unit is placed in a random 10"x10" cell along that row

    square_size = 10
    
    # Place Player A units along y=0 row
    for unit in player_a.units:
        x_square = random.randint(0, 5)
        # y is fixed at 0 row
        x_pos = x_square * square_size + random.uniform(0, square_size)
        y_pos = 0 * square_size + random.uniform(0, square_size)
        unit.position = (x_pos, y_pos)

    # Place Player B units along y=3 row
    for unit in player_b.units:
        x_square = random.randint(0, 5)
        # y is fixed at 3 row
        x_pos = x_square * square_size + random.uniform(0, square_size)
        y_pos = 3 * square_size + random.uniform(0, square_size)
        unit.position = (x_pos, y_pos)
