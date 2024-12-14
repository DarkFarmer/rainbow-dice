import util
import board_state
import random

def genetic_ai_activate_unit(active_player, opposing_player, battlefield, strategy, turn_number):
    """
    Automatically:
    - Choose a unit to activate based on the strategy's preferences.
    - Move the unit towards a control point or an opposing unit.
    - Decide on missile attacks and melee engagements based on strategy weights.
    """
    # Filter alive units for activation
    alive_units = [u for u in active_player.units if u.is_alive()]
    if not alive_units:
        return None

    # Choose a unit to activate (for simplicity, pick the first alive unit)
    chosen_unit = alive_units[0]

    # Move unit based on strategy weights
    control_points = battlefield.get_control_points()
    enemy_units = [u for u in opposing_player.units if u.is_alive()]

    target_position = None
    if random.uniform(0, 1) < strategy.control_point_capture:
        # Move towards a control point
        if control_points:
            closest_cp = min(control_points, key=lambda cp: util.distance(chosen_unit.position, (cp.x, cp.y)))
            target_position = (closest_cp.x, closest_cp.y)
    elif enemy_units:
        # Move towards an enemy unit based on strategy
        closest_enemy = min(enemy_units, key=lambda enemy: util.distance(chosen_unit.position, enemy.position))
        target_position = closest_enemy.position

    if target_position:
        move_distance = chosen_unit.movement
        chosen_unit.position = util.move_towards(chosen_unit.position, target_position, move_distance)

    # Decide on missile attack
    viable_targets = [enemy for enemy in enemy_units if util.distance(chosen_unit.position, enemy.position) <= chosen_unit.attack_range]
    if viable_targets and random.uniform(0, 1) < strategy.missile_preference:
        target = viable_targets[0]  # Target the first viable enemy
        from fight import simulate_fight
        simulate_fight(chosen_unit, target)

    # Decide on melee engagement
    if viable_targets and random.uniform(0, 1) < strategy.melee_preference:
        target = viable_targets[0]  # Engage the first viable enemy in melee
        from fight import simulate_fight, melee_favorable
        if melee_favorable(chosen_unit, target):
            simulate_fight(chosen_unit, target, 0, 'melee')

    return chosen_unit

def find_unit_by_id_or_name(units, identifier):
    """
    identifier can be an integer ID or a string name.
    If name is used and multiple units share it, user must use ID.
    """
    try:
        unit_id = int(identifier)
        for u in units:
            if getattr(u, 'id', None) == unit_id:
                return u
        return None
    except ValueError:
        matches = [u for u in units if u.name.lower() == identifier.lower()]
        if len(matches) == 1:
            return matches[0]
        return None

def roll_2d6():
    import random
    return random.randint(1, 6) + random.randint(1, 6)
