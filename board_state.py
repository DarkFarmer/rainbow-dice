import math

def get_board_state(player_a, player_b, battlefield, turn, active_player):
    def euclidean_distance(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def unit_total_wounds_remaining(unit):
        # total_possible_wounds = num_models * wounds_per_model
        # current_wounds = sum of each model's current_wounds
        # total_wounds_remaining = total_possible_wounds - wounds_taken
        total_possible_wounds = unit.num_models * unit.wounds_per_model
        current_wounds = sum(model.current_wounds for model in unit.models)
        return current_wounds  # This represents how many wounds are still left unspent
                               # (i.e., total_possible_wounds - wounds_taken = current_wounds)

    def closest_cp_distance(unit, control_points):
        if not control_points:
            return None
        distances = [euclidean_distance(unit.position, (cp.x, cp.y)) for cp in control_points]
        return min(distances)

    def units_distance_to_cp_by_player(cp, player):
        # Return min distance from player's units to this CP
        distances = [euclidean_distance(u.position, (cp.x, cp.y)) 
                     for u in player.units if u.is_alive()]
        if distances:
            return min(distances)
        return float('inf')

    def is_contested_cp(cp):
        # A CP is contested if both players have units within scoring range (3") of it
        a_in_range = any(euclidean_distance(u.position, (cp.x, cp.y)) <= 3 
                         for u in player_a.units if u.is_alive())
        b_in_range = any(euclidean_distance(u.position, (cp.x, cp.y)) <= 3 
                         for u in player_b.units if u.is_alive())
        return a_in_range and b_in_range

    # Assign IDs to control points and units
    # Control Points
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

    # Units
    # We'll assume units appear in the order given and that gives them IDs
    def player_units_data(player, base_id_start=1):
        # Find closest CP for each unit
        units_data = []
        for i, u in enumerate(player.units, start=base_id_start):
            if u.position is None:
                # If unit has no position, assign None or handle accordingly
                dist_cp = None
            else:
                dist_cp = closest_cp_distance(u, battlefield.control_points)

            unit_data = {
                'id': i,
                'name': u.name,
                'position': u.position,
                'template': u.name,  # Using name as template, or you could store a separate template attribute
                'total_wounds_remaining': unit_total_wounds_remaining(u),
                'has_activated': u.has_activated,
            }
            # Add distance_to_cp if available
            if dist_cp is not None and dist_cp != float('inf'):
                unit_data['distance_to_cp'] = dist_cp

            units_data.append(unit_data)
        return units_data

    player_a_units = player_units_data(player_a, 1)
    # Offset player B's unit IDs so they don't overlap with player A's
    player_b_units = player_units_data(player_b, 1 + len(player_a.units))

    # Construct final state
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
