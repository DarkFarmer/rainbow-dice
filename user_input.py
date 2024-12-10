
import util
import board_state
def user_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number):
    """
    Interactively:
    - Ask user which unit to activate (by name or ID).
    - Move that unit to a specified position.
    - Let the user pick an enemy unit to target for missile attack (if in range).
    - Offer the option to charge and fight in melee if possible.
    """

    # Assign IDs if not present
    # Assuming each unit does not already have a unique ID, we assign them based on their index.
    # In a real codebase, units would have persistent IDs.
    assign_ids_to_units(active_player, opposing_player)
    if active_a:
        print(board_state.get_board_visualization(active_player, opposing_player, battlefield, board_state.get_board_state(active_player, opposing_player, battlefield, turn_number, active_player)))
    else:
        print(board_state.get_board_visualization(opposing_player, active_player, battlefield, board_state.get_board_state(opposing_player, active_player, battlefield, turn_number, active_player)))
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

    # Move unit
    print(f"Chosen unit: {chosen_unit.name} (ID: {chosen_unit.id}). Current position: {chosen_unit.position}")
    move_x = float(input("Enter the new X coordinate to move this unit to: ").strip())
    move_y = float(input("Enter the new Y coordinate to move this unit to: ").strip())
    # We assume the unit can move anywhere for simplicity. Real logic would check movement limit.
    chosen_unit.position = (move_x, move_y)
    print(f"Moved {chosen_unit.name} to position ({move_x}, {move_y})")

    # Missile attack
    print("Enemy units:")
    alive_enemies = [u for u in opposing_player.units if u.is_alive()]
    for e in alive_enemies:
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
        # Check range
        dist = util.distance(chosen_unit.position, enemy_target.position)
        if dist <= chosen_unit.attack_range:
            print(f"Attacking {enemy_target.name} with missile attack!")
            from fight import simulate_fight
            simulate_fight(chosen_unit, enemy_target)  # Missile attack by default
        else:
            print(f"Target out of range. (Distance: {dist}, Range: {chosen_unit.attack_range}) Skipping missile attack.")

    # Charge and melee
    if enemy_target and enemy_target.is_alive():
        # Ask if want to charge
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
    # Check if integer ID
    try:
        unit_id = int(identifier)
        for u in units:
            if getattr(u, 'id', None) == unit_id:
                return u
        return None
    except ValueError:
        # identifier is a string, match by name
        matches = [u for u in units if u.name.lower() == identifier.lower()]
        if len(matches) == 1:
            return matches[0]
        return None

def assign_ids_to_units(player_a, player_b):
    # Assign IDs if not already assigned
    # Just assign sequential IDs across both players for simplicity
    # In a real game, you'd keep these separate or have unique IDs per player
    current_id = 1
    for u in player_a.units:
        u.id = current_id
        current_id += 1
    for u in player_b.units:
        u.id = current_id
        current_id += 1

def roll_2d6():
    import random
    return random.randint(1,6) + random.randint(1,6)
