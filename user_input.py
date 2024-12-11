import util
import board_state

def user_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    """
    Interactively:
    - Ask user which unit to activate (by name or ID).
    - Move that unit towards a control point or an opposing unit.
    - Let the user pick an enemy unit to target for missile attack (if in range).
    - Offer the option to charge and fight in melee if possible.
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
        print(f"ID: {u.id}, Name: {u.name}, Position: {u.position}, Alive: {u.is_alive()}")

    # Choose unit
    chosen_unit = None
    while not chosen_unit:
        user_input = input("Enter the unit ID or Name to activate: ").strip()
        chosen_unit = find_unit_by_id_or_name(active_player.units, user_input)
        if not chosen_unit:
            print("No matching unit found. Try again.")
            continue
        if not chosen_unit.is_alive():
            print("That unit is not alive. Choose another unit.")
            chosen_unit = None

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

    # Missile attack
    print("Enemy units:")
    alive_enemies = [u for u in opposing_player.units if u.is_alive()]
    for e in alive_enemies:
        if util.distance(chosen_unit.position, e.position) <= chosen_unit.attack_range:
            print(f"ID: {e.id}, Name: {e.name}, Position: {e.position}")

    enemy_target = None
    while True:
        target_input = input("Enter enemy unit ID or Name to target with missile attack, or press Enter to skip: ").strip()
        if target_input == "":
            break
        enemy_target = find_unit_by_id_or_name(alive_enemies, target_input)
        if enemy_target:
            break
        else:
            print("No matching enemy found. Try again or press Enter to skip.")

    if enemy_target:
        dist = util.distance(chosen_unit.position, enemy_target.position)
        if dist <= chosen_unit.attack_range:
            print(f"Attacking {enemy_target.name} with missile attack!")
            from fight import simulate_fight
            simulate_fight(chosen_unit, enemy_target)
        else:
            print(f"Target out of range. (Distance: {dist}, Range: {chosen_unit.attack_range}) Skipping missile attack.")

    # Charge and melee
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
