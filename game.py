from ai import ai_choose_unit_to_activate, ai_move_unit_towards_control_point, find_enemy_in_range
from fight import simulate_fight, melee_favorable
import ap
import util
import random

def play_game(player_a, player_b, battlefield):
    # Initial deployment
    deploy_units(player_a, battlefield, side='left')
    deploy_units(player_b, battlefield, side='right')

    for turn_number in range(1, 7):
        print(f"\n=== TURN {turn_number} ===")
        play_turn(player_a, player_b, battlefield, turn_number)

    # End of game
    if player_a.score > player_b.score:
        print(f"{player_a.name} wins!")
    elif player_b.score > player_a.score:
        print(f"{player_b.name} wins!")
    else:
        print("It's a draw!")

def deploy_units(player, battlefield, side='left'):
    # Example: place units in a line on chosen side
    if side == 'left':
        x_positions = range(0, len(player.units)*2, 2)
        for i, unit in enumerate(player.units):
            unit.position = (x_positions[i], battlefield.height//2)
    else:
        x_positions = range(battlefield.width-1, battlefield.width - 1 - (len(player.units)*2), -2)
        for i, unit in enumerate(player.units):
            unit.position = (x_positions[i], battlefield.height//2)

def play_turn(player_a, player_b, battlefield, turn_number):
    # Determine AP for both
    ap_a, ap_b = ap.determine_ap_allocation(player_a, player_b)
    print(f"AP Allocations - {player_a.name}: {ap_a}, {player_b.name}: {ap_b}")

    # On odd turns, player_a goes first, on even turns, player_b goes first.
    first_player, second_player = (player_a, player_b) if turn_number % 2 == 1 else (player_b, player_a)
    first_ap, second_ap = (ap_a, ap_b) if first_player == player_a else (ap_b, ap_a)

    # Reset activation flags
    for u in player_a.units + player_b.units:
        u.has_activated = False

    # Activation loop
    while (first_ap > 0 or second_ap > 0):
        # First player activation
        if first_ap > 0:
            print(f"{first_player.name} has {first_ap} AP left.")
            ap_spent = activate_unit_this_turn(first_player, second_player, battlefield, first_ap)
            if ap_spent == 0:
                print(f"{first_player.name} can no longer activate any units.")
                first_ap = 0
            else:
                first_ap -= ap_spent

        # Second player activation
        if second_ap > 0:
            print(f"{second_player.name} has {second_ap} AP left.")
            ap_spent = activate_unit_this_turn(second_player, first_player, battlefield, second_ap)
            if ap_spent == 0:
                print(f"{second_player.name} can no longer activate any units.")
                second_ap = 0
            else:
                second_ap -= ap_spent

        # If both players can't activate, break
        if first_ap <= 0 and second_ap <= 0:
            break

    # Scoring Phase
    score_control_points(player_a, player_b, battlefield)

def activate_unit_this_turn(active_player, opposing_player, battlefield, ap_available):
    # Choose one unit to activate
    unit = ai_choose_unit_to_activate(active_player, ap_available)
    
    if unit is None:
        print("DEBUG: No unit can be activated with the available AP.")
        return 0
    else:
        print("DEBUG: Activating unit: " + unit.name)
    
    ap_cost = unit.ap_cost
    if ap_cost > ap_available:
        print("DEBUG: Not enough AP to activate this unit.")
        return 0

    unit.has_activated = True

    # Track how many times this unit has fought melee during this activation
    melee_fights_this_activation = 0

    # 1. If the unit starts in melee, it must fight first.
    if unit.is_locked_in_melee():
        print(f"DEBUG: {unit.name} starts locked in melee.")
        opponent = unit.melee_opponent  # Assuming you have a reference stored
        if opponent and opponent.is_alive():
            simulate_fight(unit, opponent, 0, 'melee')
            melee_fights_this_activation += 1

            # Check if still locked or dead
            if not unit.is_alive():
                print(f"DEBUG: {unit.name} died in melee start, activation ends.")
                return ap_cost

            if unit.is_locked_in_melee():
                print(f"DEBUG: {unit.name} still locked in melee after fight, activation ends.")
                return ap_cost
        else:
            print(f"DEBUG: {unit.name} not actually locked in melee with a valid opponent.")
            unit.unlock_melee()

    # 2. Normal activation sequence after clearing melee
    if not unit.is_locked_in_melee():
        print(f"DEBUG: {unit.name} moving towards objective.")
        ai_move_unit_towards_control_point(unit, battlefield)
        print(f"DEBUG: {unit.name} position after move: {unit.position}")

    # Check for enemy in range
    enemies = [e for e in opposing_player.units if e.is_alive()]
    enemy_target = find_enemy_in_range(unit, enemies)

    if enemy_target:
        print(f"DEBUG: {unit.name} found enemy {enemy_target.name} in range. Attempting to shoot.")
        simulate_fight(unit, enemy_target)

        if not unit.is_alive():
            print(f"DEBUG: {unit.name} died after shooting attempt.")
            return ap_cost

        if enemy_target.is_alive():
            print(f"DEBUG: Enemy {enemy_target.name} survived shooting.")
            # Enemy survived shooting, consider charging
            if melee_fights_this_activation < 2:  # Can only fight melee twice max
                print("DEBUG: Considering charging into melee.")
                if can_charge_and_fight(unit, enemy_target):
                    print("DEBUG: Charge successful. Fighting melee.")
                    simulate_fight(unit, enemy_target, 0, 'melee')
                    melee_fights_this_activation += 1

                    if not unit.is_alive():
                        print(f"DEBUG: {unit.name} died in melee after charge.")
                        return ap_cost

                    if unit.is_locked_in_melee():
                        print(f"DEBUG: {unit.name} locked in melee after charge fight. Activation ends.")
                        return ap_cost
                else:
                    print("DEBUG: Charge not possible or not favorable.")
            else:
                print("DEBUG: Already fought melee twice this activation. No further melee allowed.")
        else:
            print(f"DEBUG: {enemy_target.name} died from shooting. No charge needed.")
    else:
        print(f"DEBUG: {unit.name} found no enemies in range. Activation ends.")

    # Unit finished its single activation for the turn
    return ap_cost

def can_charge_and_fight(unit, target):
    """
    Check if unit can charge target.
    Roll 2D6 and check if distance is covered and if melee is favorable.
    """
    distance = util.distance(unit.position, target.position)
    charge_roll = random.randint(1,6) + random.randint(1,6)
    favorable = melee_favorable(unit, target)
    print(f"DEBUG: {unit.name} attempting charge. Distance={distance}, roll={charge_roll}, favorable={favorable}")
    if charge_roll >= distance and favorable:
        return True
    return False

def score_control_points(player_a, player_b, battlefield):
    print("\n--- Scoring Control Points ---")
    for i, cp in enumerate(battlefield.control_points, start=1):
        a_models = util.count_models_in_range(player_a, cp, 3)
        b_models = util.count_models_in_range(player_b, cp, 3)
        
        print(f"\nControl Point {i}:")
        print(f"  Player A models in range: {a_models}")
        print(f"  Player B models in range: {b_models}")
        
        if a_models > b_models:
            player_a.score += 1
            print(f"  Player A controls Control Point {i}. Updated score: {player_a.score}")
        elif b_models > a_models:
            player_b.score += 1
            print(f"  Player B controls Control Point {i}. Updated score: {player_b.score}")
        else:
            print(f"  Control Point {i} is contested. No score awarded.")
    print("\n--- Scoring Complete ---")
    print(f"Final Score: Player A - {player_a.score}, Player B - {player_b.score}")

