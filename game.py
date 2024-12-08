from ai import ai_choose_unit_to_activate, ai_move_unit_towards_control_point, find_enemy_in_range
from fight import simulate_fight, melee_favorable
import ap
import util
import random
from board_state import get_board_state

def play_game(player_a, player_b, battlefield):
    # Initial deployment
    deploy_units(player_a, battlefield, side='left')
    deploy_units(player_b, battlefield, side='right')

    for turn_number in range(1, 5):
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
            ap_spent = activate_unit_this_turn(first_player, second_player, battlefield, first_ap, True, turn_number)
            if ap_spent == 0:
                first_ap = 0
            else:
                first_ap -= ap_spent

        # Second player activation
        if second_ap > 0:
            ap_spent = activate_unit_this_turn(second_player, first_player, battlefield, second_ap, False, turn_number)
            if ap_spent == 0:
                second_ap = 0
            else:
                second_ap -= ap_spent

        # If both players can't activate, break
        if first_ap <= 0 and second_ap <= 0:
            break

    # Scoring Phase
    score_control_points(player_a, player_b, battlefield)

def activate_unit_this_turn(active_player, opposing_player, battlefield, ap_available, active_a, turn_number):
    # Choose one unit to activate
    unit = ai_choose_unit_to_activate(active_player, ap_available)
    
    if unit is None:
        return 0
    
    ap_cost = unit.ap_cost
    if ap_cost > ap_available:
        return 0

    unit.has_activated = True

    # Track how many times this unit has fought melee during this activation
    melee_fights_this_activation = 0

    # 1. If the unit starts in melee, it must fight first.
    if unit.is_locked_in_melee():
        opponent = unit.melee_opponent  # Assuming you have a reference stored
        if opponent and opponent.is_alive():
            simulate_fight(unit, opponent, 0, 'melee')
            melee_fights_this_activation += 1

            # Check if still locked or dead
            if not unit.is_alive():
                return ap_cost

            if unit.is_locked_in_melee():
                return ap_cost
        else:
            unit.unlock_melee()

    # 2. Normal activation sequence after clearing melee
    if not unit.is_locked_in_melee():
        ai_move_unit_towards_control_point(unit, battlefield)

    # Check for enemy in range
    enemies = [e for e in opposing_player.units if e.is_alive()]
    enemy_target = find_enemy_in_range(unit, enemies)

    if enemy_target:
        simulate_fight(unit, enemy_target)

        if not unit.is_alive():
            return ap_cost

        if enemy_target.is_alive():
            # Enemy survived shooting, consider charging
            if melee_fights_this_activation < 2:  # Can only fight melee twice max
                if can_charge_and_fight(unit, enemy_target):
                    simulate_fight(unit, enemy_target, 0, 'melee')
                    melee_fights_this_activation += 1

                    if not unit.is_alive():
                        return ap_cost

                    if unit.is_locked_in_melee():
                        return ap_cost

    if active_a:
        print(get_board_state(active_player, opposing_player, battlefield, turn_number, active_player))
    else:
        print(get_board_state(opposing_player, active_player, battlefield, turn_number, active_player))
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
    if charge_roll >= distance and favorable:
        return True
    return False

def score_control_points(player_a, player_b, battlefield):
    for i, cp in enumerate(battlefield.control_points, start=1):
        a_models = util.count_models_in_range(player_a, cp, 3)
        b_models = util.count_models_in_range(player_b, cp, 3)
        
        if a_models > b_models:
            player_a.score += 1
        elif b_models > a_models:
            player_b.score += 1
    print(f"Turn Score: Player A - {player_a.score}, Player B - {player_b.score}")

