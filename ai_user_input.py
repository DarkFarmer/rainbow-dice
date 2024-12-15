import util
import board_state
import random

def ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    """
    Automated version of user_activate_unit:
    - No human input.
    - Chooses a unit that has not activated yet, at random.
    - If in melee, fights melee. Otherwise moves towards nearest control point or nearest enemy.
    - If shooting possible, shoot at a random valid target.
    - If charging possible, attempt charge.

    This is a simple AI as an example.
    """

    # Print board for debug (optional)
    # print(board_state.get_board_visualization(
    #     active_player, opposing_player, battlefield,
    #     board_state.get_board_state(active_player, opposing_player, battlefield, turn_number, active_player)
    # ))

    # Find a unit that hasn't activated
    available_units = [u for u in active_player.units if u.is_alive() and not u.has_activated]
    if not available_units:
        return None

    chosen_unit = random.choice(available_units)
    # Check if unit is in melee
    enemy_in_melee = next(
        (e for e in opposing_player.units if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 1),
        None
    )

    if enemy_in_melee:
        melee_fight(chosen_unit, enemy_in_melee)
        # If enemy_in_melee not alive now, proceed with normal activation
        if not enemy_in_melee.is_alive():
            # Continue with normal turn
            pass
        else:
            # If enemy still alive, activation ends
            chosen_unit.has_activated = True
            return chosen_unit

    # If not in melee or melee target destroyed, attempt a move
    # Move towards the closest control point or enemy, chosen randomly
    move_target = decide_move_target(chosen_unit, opposing_player, battlefield)
    if move_target:
        move_distance = chosen_unit.movement
        chosen_unit.position = util.move_towards(chosen_unit.position, move_target, move_distance)

    # Randomly decide whether to skip shooting and charging for an extra move
    # For simplicity, 50% chance:
    if random.random() < 0.3:
        # Roll 2D6 and move again
        extra_move = roll_2d6()
        if move_target:
            chosen_unit.position = util.move_towards(chosen_unit.position, move_target, extra_move)
        chosen_unit.has_activated = True
        return chosen_unit

    # Attempt missile attack if possible
    try_missile_attack(chosen_unit, active_player, opposing_player)

    # Attempt charge if possible
    try_charge(chosen_unit, opposing_player)

    chosen_unit.has_activated = True
    return chosen_unit

def decide_move_target(chosen_unit, opposing_player, battlefield):
    # Decide whether to move towards a control point or an enemy
    control_points = battlefield.get_control_points()
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]

    # If no enemies, go for control point
    if not alive_enemies and control_points:
        cp = random.choice(control_points)
        return (cp.x, cp.y)

    # If no control points, go for enemy
    if not control_points and alive_enemies:
        e = random.choice(alive_enemies)
        return e.position

    # Otherwise randomly pick what to move towards
    if random.random() < 0.5 and control_points:
        cp = random.choice(control_points)
        return (cp.x, cp.y)
    else:
        e = random.choice(alive_enemies) if alive_enemies else None
        return e.position if e else None

def try_missile_attack(chosen_unit, active_player, opposing_player):
    # Fire at a random valid target if in range and not engaged in melee
    alive_enemies = [e for e in opposing_player.units if e.is_alive()]
    # Exclude enemies engaged in melee
    viable_targets = [
        e for e in alive_enemies 
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range
        and not any(util.distance(e.position, ally.position) <= 1 for ally in active_player.units if ally.is_alive())
    ]
    if viable_targets:
        enemy_target = random.choice(viable_targets)
        from fight import simulate_fight
        simulate_fight(chosen_unit, enemy_target)

def try_charge(chosen_unit, opposing_player):
    # Attempt to charge the nearest enemy if within 12" and melee favorable
    from fight import simulate_fight, melee_favorable
    enemies_in_range = [e for e in opposing_player.units if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 12]
    if not enemies_in_range:
        return
    enemy_target = min(enemies_in_range, key=lambda e: util.distance(chosen_unit.position, e.position))
    dist = util.distance(chosen_unit.position, enemy_target.position)
    charge_roll = roll_2d6()
    if charge_roll >= dist and melee_favorable(chosen_unit, enemy_target):
        simulate_fight(chosen_unit, enemy_target, 0, 'melee')

def melee_fight(chosen_unit, enemy_target):
    from fight import simulate_fight
    simulate_fight(chosen_unit, enemy_target, 0, 'melee')

def find_unit_by_id_or_name(units, identifier):
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
    return random.randint(1, 6) + random.randint(1, 6)
