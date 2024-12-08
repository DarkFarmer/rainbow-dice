from ai import ai_choose_unit_to_activate, ai_move_unit_towards_control_point, find_enemy_in_range
from fight import simulate_fight
import ap
import util

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

    # On odd turns, attacker (player_a) goes first, on even turns, player_b goes first.
    first_player, second_player = (player_a, player_b) if turn_number % 2 == 1 else (player_b, player_a)
    first_ap, second_ap = (ap_a, ap_b) if first_player == player_a else (ap_b, ap_a)

    # Reset activation flags
    for u in player_a.units + player_b.units:
        u.has_activated = False

    # Activation loop
    while (first_ap > 0 or second_ap > 0):
        # First player activation
        if first_ap > 0:
            unit = ai_choose_unit_to_activate(first_player, first_ap)
            if unit:
                # Activate unit
                first_ap -= unit.ap_cost
                unit.has_activated = True
                # Move unit towards control point or enemy
                ai_move_unit_towards_control_point(unit, battlefield)
                # Check for enemy in range to shoot
                enemies = player_b.units if first_player == player_a else player_a.units
                enemy_target = find_enemy_in_range(unit, enemies)
                if enemy_target:
                    simulate_fight(unit, enemy_target)
            else:
                # No unit can be activated by first player
                first_ap = 0

        # Second player activation
        if second_ap > 0:
            unit = ai_choose_unit_to_activate(second_player, second_ap)
            if unit:
                second_ap -= unit.ap_cost
                unit.has_activated = True
                ai_move_unit_towards_control_point(unit, battlefield)
                enemies = player_a.units if second_player == player_b else player_b.units
                enemy_target = find_enemy_in_range(unit, enemies)
                if enemy_target:
                    simulate_fight(unit, enemy_target)
            else:
                second_ap = 0

        # If both players can't activate, break
        if first_ap <= 0 and second_ap <= 0:
            break

    # Scoring Phase
    score_control_points(player_a, player_b, battlefield)

def score_control_points(player_a, player_b, battlefield):
    # For each control point, see how many models each player has within 3"
    for cp in battlefield.control_points:
        a_models = util.count_models_in_range(player_a, cp, 3)
        b_models = util.count_models_in_range(player_b, cp, 3)
        if a_models > b_models:
            player_a.score += 1
        elif b_models > a_models:
            player_b.score += 1
