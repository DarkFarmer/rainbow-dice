from ai import ai_choose_unit_to_activate, ai_move_unit_towards_control_point, find_enemy_in_range
from fight import simulate_fight, melee_favorable
import ap
import util
import random
from board_state import get_board_state
from user_input import user_activate_unit

def play_game(player_a, player_b, battlefield):
    # Initial deployment
    # deploy_units(player_a, battlefield, side='left')
    # deploy_units(player_b, battlefield, side='right')

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

    # Determine activation flag order based on turn number
    first_player_is_active = turn_number % 2 == 1

    # Reset activation flags
    for u in player_a.units + player_b.units:
        u.has_activated = False

    # Activation loop
    while first_ap > 0 or second_ap > 0:
        # First player activation
        if first_ap > 0:
            ap_spent = activate_unit_this_turn(first_player, second_player, battlefield, first_ap, first_player_is_active, turn_number)
            if ap_spent == 0:
                first_ap = 0
            else:
                first_ap -= ap_spent

        # Second player activation
        if second_ap > 0:
            ap_spent = activate_unit_this_turn(second_player, first_player, battlefield, second_ap, not first_player_is_active, turn_number)
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
    chosen_unit = user_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number)

    # After user moves and optionally attacks/charges, mark AP spent
    if chosen_unit:
        return chosen_unit.ap_cost
    return 0

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

