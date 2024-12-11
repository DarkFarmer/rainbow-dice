from math import sqrt
 
def distance(pos1, pos2):
    return abs(pos1[0]-pos2[0]) + abs(pos1[1]-pos2[1])

def count_models_in_range(player, cp, radius):
    count = 0
    for u in player.units:
        if u.is_alive() and distance(u.position, (cp.x, cp.y)) <= radius:
            count += u.num_models
    return count

def move_towards(current_position, target_position, max_distance):
    """
    Move from the current position towards the target position by a maximum distance.

    :param current_position: Tuple (x, y) of the current position.
    :param target_position: Tuple (x, y) of the target position.
    :param max_distance: Maximum distance the unit can move.
    :return: New position (x, y) after moving towards the target.
    """
   

    current_x, current_y = current_position
    target_x, target_y = target_position

    dx = target_x - current_x
    dy = target_y - current_y

    distance_to_target = sqrt(dx**2 + dy**2)

    if distance_to_target <= max_distance:
        return target_position

    scaling_factor = max_distance / distance_to_target
    new_x = current_x + dx * scaling_factor
    new_y = current_y + dy * scaling_factor

    return (new_x, new_y)