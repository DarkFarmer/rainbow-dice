import util
import board_state
import random

def user_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    """
    Interactively:
    - Handle melee-only activation for units in melee range.
    - Allow normal activation if a unit destroys its melee opponent.
    - Move towards control points or enemy units.
    - Skip shooting and charging for additional movement.
    - Prevent shooting at units engaged in melee.
    """

    if active_a:
        print(board_state.get_board_visualization(
            active_player, opposing_player, battlefield,
            board_state.get_board_state(active_player, opposing_player, battlefield, turn_number, active_player)
        ))
    else:
        print(board_state.get_board_visualization(
            opposing_player, active_player, battlefield,
            board_state.get_board_state(opposing_player, active_player, battlefield, turn_number, active_player)
        ))

    print(f"Available units for {active_player.name}:")
    for u in active_player.units:
        if not u.has_activated:
            print(f"ID: {u.id}, Name: {u.name}, Position: {u.position}, Alive: {u.is_alive()}")

    # Choose unit
    chosen_unit = None
    while not chosen_unit:
        user_input = input("Enter the unit ID or Name to activate: ").strip()
        chosen_unit = find_unit_by_id_or_name(active_player.units, user_input)
        if not chosen_unit:
            print("No matching unit found. Try again.")
            continue
        if chosen_unit.has_activated:
            print("That unit has already been activated. Choose another unit.")
            chosen_unit = None
        if chosen_unit and not chosen_unit.is_alive():
            print("That unit is not alive. Choose another unit.")
            chosen_unit = None

    # Check if the unit is in melee
    enemy_target = next(
        (e for e in opposing_player.units if util.distance(chosen_unit.position, e.position) <= 1 and e.is_alive()),
        None
    )

    if enemy_target:
        print(f"{chosen_unit.name} is in melee combat with {enemy_target.name}.")
        melee_fight(chosen_unit, enemy_target)

        # If the melee target is destroyed, allow normal activation
        if not enemy_target.is_alive():
            print(f"{enemy_target.name} was destroyed! {chosen_unit.name} can take a normal turn.")
        else:
            print(f"{chosen_unit.name} finished its melee combat.")
            chosen_unit.has_activated = True
            return chosen_unit

    # Move unit towards a control point or an opposing unit
    print(f"Chosen unit: {chosen_unit.name} (ID: {chosen_unit.id}). Current position: {chosen_unit.position}")

    move_target = None
    while not move_target:
        move_input = input("Do you want to move towards a control point (c) or an opposing unit (u)? ").strip().lower()
        if move_input == 'c':
            control_points = battlefield.get_control_points()
            print("Available control points:")
            for cp in control_points:
                print(f"ID: {cp.id}, X: {cp.x}, Y: {cp.y}")
            cp_input = input("Enter the control point ID to move towards: ").strip()
            move_target = next((cp for cp in control_points if str(cp.id) == cp_input), None)
            if move_target:
                target_position = (move_target.x, move_target.y)
            else:
                print("No matching control point found. Try again.")
        elif move_input == 'u':
            alive_enemies = [u for u in opposing_player.units if u.is_alive()]
            print("Available enemy units:")
            for e in alive_enemies:
                print(f"ID: {e.id}, Name: {e.name}, Position: {e.position}")
            enemy_input = input("Enter the enemy unit ID to move towards: ").strip()
            move_target = find_unit_by_id_or_name(alive_enemies, enemy_input)
            if move_target:
                target_position = move_target.position
            else:
                print("No matching enemy unit found. Try again.")

    if move_target:
        move_distance = chosen_unit.movement
        chosen_unit.position = util.move_towards(chosen_unit.position, target_position, move_distance)
        print(f"Moved {chosen_unit.name} towards position {target_position}, now at {chosen_unit.position}")

    # Offer the option to skip shooting and charging to move an additional D6
    skip_option = input("Do you want to skip shooting and charging to move an additional D6? (y/n): ").strip().lower()
    if skip_option == 'y':
        extra_move = roll_2d6()
        target_position = util.move_towards(chosen_unit.position, target_position, extra_move)
        chosen_unit.position = target_position
        print(f"{chosen_unit.name} moved an additional {extra_move} inches to position {chosen_unit.position}.")
        chosen_unit.has_activated = True
        return chosen_unit

    # Missile attack
    print("Enemy units:")
    alive_enemies = [u for u in opposing_player.units if u.is_alive()]
    # Exclude units engaged in melee combat
    viable_targets = [
        e for e in alive_enemies 
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range 
        and not any(util.distance(e.position, ally.position) <= 1 for ally in active_player.units if ally.is_alive())
    ]

    if viable_targets:
        for e in viable_targets:
            print(f"ID: {e.id}, Name: {e.name}, Position: {e.position}")

        enemy_target = None
        while True:
            target_input = input("Enter enemy unit ID or Name to target with missile attack, or press Enter to skip: ").strip()
            if target_input == "":
                break
            enemy_target = find_unit_by_id_or_name(viable_targets, target_input)
            if enemy_target:
                break
            else:
                print("No matching enemy found. Try again or press Enter to skip.")

        if enemy_target:
            print(f"Attacking {enemy_target.name} with missile attack!")
            from fight import simulate_fight
            simulate_fight(chosen_unit, enemy_target)
    else:
        print("No valid enemies in missile range. Skipping missile attack.")

    # Charge and melee
    enemy_target = next((e for e in alive_enemies if util.distance(chosen_unit.position, e.position) <= 12), None)
    if enemy_target and enemy_target.is_alive():
        charge_input = input("Do you want to charge and fight melee? (y/n): ").strip().lower()
        if charge_input == 'y':
            from fight import simulate_fight, melee_favorable
            dist = util.distance(chosen_unit.position, enemy_target.position)
            charge_roll = roll_2d6()
            print(f"Charge roll: {charge_roll}, Distance: {dist}")
            if charge_roll >= dist and melee_favorable(chosen_unit, enemy_target):
                print(f"Charging {enemy_target.name} and fighting melee!")
                simulate_fight(chosen_unit, enemy_target, 0, 'melee')
            else:
                print("Charge failed or not favorable. No melee attack.")

    chosen_unit.has_activated = True
    return chosen_unit

def melee_fight(chosen_unit, enemy_target):
    """Handle melee combat."""
    from fight import simulate_fight
    print(f"{chosen_unit.name} is engaging in melee combat with {enemy_target.name}.")
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
