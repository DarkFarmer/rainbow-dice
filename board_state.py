import math

def get_board_state(player_a, player_b, battlefield, turn, active_player):
    def euclidean_distance(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def unit_total_wounds_remaining(unit):
        total_possible_wounds = unit.num_models * unit.wounds_per_model
        current_wounds = sum(model.current_wounds for model in unit.models)
        return current_wounds  # current_wounds represents how many wounds remain

    def closest_cp_distance(unit, control_points):
        if not control_points:
            return None
        distances = [euclidean_distance(unit.position, (cp.x, cp.y)) for cp in control_points]
        return min(distances)

    def units_distance_to_cp_by_player(cp, player):
        distances = [euclidean_distance(u.position, (cp.x, cp.y)) 
                     for u in player.units if u.is_alive()]
        return min(distances) if distances else float('inf')

    def is_contested_cp(cp):
        a_in_range = any(euclidean_distance(u.position, (cp.x, cp.y)) <= 3 
                         for u in player_a.units if u.is_alive())
        b_in_range = any(euclidean_distance(u.position, (cp.x, cp.y)) <= 3 
                         for u in player_b.units if u.is_alive())
        return a_in_range and b_in_range

    # Assign IDs to control points
    control_points_data = []
    for i, cp in enumerate(battlefield.control_points, start=1):
        dist_a = units_distance_to_cp_by_player(cp, player_a)
        dist_b = units_distance_to_cp_by_player(cp, player_b)

        cp_data = {
            'id': i,
            'x': cp.x,
            'y': cp.y,
            'is_contested': is_contested_cp(cp),
            'distance_to_cp': {
                player_a.name: dist_a if dist_a != float('inf') else None,
                player_b.name: dist_b if dist_b != float('inf') else None
            }
        }
        control_points_data.append(cp_data)

    # Units for Player A
    def player_units_data(player, base_id_start=1):
        units_data = []
        for i, u in enumerate(player.units, start=base_id_start):
            dist_cp = None if u.position is None else closest_cp_distance(u, battlefield.control_points)
            unit_data = {
                'id': i,
                'name': u.name,
                'position': u.position,
                'template': u.name,
                'total_wounds_remaining': unit_total_wounds_remaining(u),
                'has_activated': u.has_activated,
            }
            if dist_cp is not None and dist_cp != float('inf'):
                unit_data['distance_to_cp'] = dist_cp
            units_data.append(unit_data)
        return units_data

    player_a_units = player_units_data(player_a, 1)
    player_b_units = player_units_data(player_b, 1 + len(player_a.units))

    state = {
        'battlefield': {
            'width': battlefield.width,
            'height': battlefield.height,
            'control_points': control_points_data
        },
        'players': {
            player_a.name: {
                'score': player_a.score,
                'units': player_a_units
            },
            player_b.name: {
                'score': player_b.score,
                'units': player_b_units
            }
        },
        'turn': turn,
        'active_player': active_player.name if active_player else None
    }

    return state

def get_board_visualization(player_a, player_b, battlefield, state):
    """
    Returns a multi-line string showing a rough visual approximation of the board.
    Each cell represents ~4 inches.
    Control points are marked as C<ID>.
    Player A units as A<ID>, Player B units as B<ID>.
    If multiple items in the same cell, separate by '|'.

    Top-left corner is (0,0). 
    Y increases downward, X to the right.
    """
    scale = 4
    width_cells = battlefield.width // scale
    height_cells = battlefield.height // scale

    # Create a 2D grid filled with '.'
    grid = [['.' for _ in range(width_cells)] for _ in range(height_cells)]

    # Mark control points
    for cp in state['battlefield']['control_points']:
        cx = int(cp['x'] // scale)
        cy = int(cp['y'] // scale)
        if 0 <= cy < height_cells and 0 <= cx < width_cells:
            if grid[cy][cx] == '.':
                grid[cy][cx] = f"C{cp['id']}"
            else:
                grid[cy][cx] = f"{grid[cy][cx]}|C{cp['id']}"

    # We need mapping from state units back to players
    # We'll assume IDs assigned as in get_board_state
    # Player A units
    for u in state['players'][player_a.name]['units']:
        if u['position'] is None:
            continue
        ux = int(u['position'][0] // scale)
        uy = int(u['position'][1] // scale)
        if 0 <= uy < height_cells and 0 <= ux < width_cells:
            label = f"A{u['id']}"
            if grid[uy][ux] == '.':
                grid[uy][ux] = label
            else:
                grid[uy][ux] = f"{grid[uy][ux]}|{label}"

    # Player B units
    for u in state['players'][player_b.name]['units']:
        if u['position'] is None:
            continue
        ux = int(u['position'][0] // scale)
        uy = int(u['position'][1] // scale)
        if 0 <= uy < height_cells and 0 <= ux < width_cells:
            label = f"B{u['id']}"
            if grid[uy][ux] == '.':
                grid[uy][ux] = label
            else:
                grid[uy][ux] = f"{grid[uy][ux]}|{label}"

    # Build the multi-line string
    lines = []
    for row in range(height_cells):
        lines.append(' '.join(grid[row]))

    return "\n".join(lines)
