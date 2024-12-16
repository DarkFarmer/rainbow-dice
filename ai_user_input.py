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

    if enemy_in_melee and 'Disengage' in chosen_unit.keywords:
        # Move away from enemy before doing anything else
        # Just pick a direction away from enemy and move full movement
        away_position = (chosen_unit.position[0] + 5, chosen_unit.position[1] + 5)  # Arbitrary
        chosen_unit.position = util.move_towards(chosen_unit.position, away_position, chosen_unit.movement)
        enemy_in_melee = None  # now not in melee

    elif enemy_in_melee:
        # If no Disengage, just fight melee
        melee_fight(chosen_unit, enemy_in_melee, active_player)
        chosen_unit.has_activated = True
        return chosen_unit

    # Decide if Regenerate (if 'Regenerate' in chosen_unit.keywords)
    # For simplicity, 10% chance to regenerate if wounded:
    if 'Regenerate' in chosen_unit.keywords and random.random() < 0.1:
        chosen_unit.regenerate()
        chosen_unit.has_activated = True
        return chosen_unit

    # Normal move/attack/charge logic unchanged
    move_target = decide_move_target(chosen_unit, opposing_player, battlefield)
    if move_target:
        move_distance = chosen_unit.movement
        chosen_unit.position = util.move_towards(chosen_unit.position, move_target, move_distance)

    # Attempt missile attack
    try_missile_attack(chosen_unit, active_player, opposing_player)

    # Attempt charge
    try_charge(chosen_unit, opposing_player, active_player)

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
        simulate_fight(chosen_unit, enemy_target, active_player)

def try_charge(chosen_unit, opposing_player, active_player):
    from fight import simulate_fight, melee_favorable
    enemies_in_range = [e for e in opposing_player.units if e.is_alive() and util.distance(chosen_unit.position, e.position) <= 12]
    if not enemies_in_range:
        return
    enemy_target = min(enemies_in_range, key=lambda e: util.distance(chosen_unit.position, e.position))
    dist = util.distance(chosen_unit.position, enemy_target.position)
    charge_roll = roll_2d6()

    # Overwatch: If enemy has Overwatch and not activated, enemy fires before charge roll is even executed.
    # This should happen before the charge distance roll in a full implementation.
    # For simplicity, assume Overwatch is triggered here if conditions met:
    if 'Overwatch' in enemy_target.keywords and not enemy_target.has_activated:
        # Enemy gets a missile attack before movement
        enemy_target.attack(chosen_unit, 'missile', charging=False)

    if charge_roll >= dist and melee_favorable(chosen_unit, enemy_target):
        simulate_fight(chosen_unit, enemy_target, active_player, 0, 'melee', charging=True)


def melee_fight(chosen_unit, enemy_target, active_player):
    from fight import simulate_fight
    simulate_fight(chosen_unit, enemy_target, active_player, 0, 'melee')

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
