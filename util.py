from math import sqrt
 
SMOOTHING_FACTOR = 0.2  # Adjust this value based on how responsive or stable you want the adjustments to be

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

def ema_adjustment(current_cost, delta):
    """
    Adjust the cost using an Exponential Moving Average (EMA).
    
    :param current_cost: The current cost of the unit or stat.
    :param delta: The suggested change based on game outcomes.
    :return: The new adjusted cost.
    """
    return SMOOTHING_FACTOR * delta + (1 - SMOOTHING_FACTOR) * current_cost