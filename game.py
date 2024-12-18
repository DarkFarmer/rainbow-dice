import ai_second_input
import ai_third_input
from fight import simulate_fight, melee_favorable
import ap
import util
import random
from board_state import get_board_state, get_board_visualization

def play_game(player_a, player_b, battlefield, stat_costs, keyword_costs):
    # Run a fixed number of turns, for example
    for turn_number in range(1, 5):
        #print(f"\n===== START OF TURN {turn_number} =====")
        play_turn(player_a, player_b, battlefield, turn_number)
    adjust_costs_based_on_performance(player_a, player_b, stat_costs, keyword_costs)
    # End of game
    #if player_a.score > player_b.score:
        #print(f"{player_a.name} wins! Final Score: {player_a.score} vs {player_b.score}")
    #elif player_b.score > player_a.score:
        #print(f"{player_b.name} wins! Final Score: {player_b.score} vs {player_a.score}")
    #else:
        #print(f"It's a draw! Final Score: {player_a.score} vs {player_b.score}")

def play_turn(player_a, player_b, battlefield, turn_number):
    # Determine AP for both
    ap_a, ap_b = ap.determine_ap_allocation(player_a, player_b)

    first_player, second_player = (player_a, player_b) if turn_number % 2 == 1 else (player_b, player_a)
    first_ap, second_ap = (ap_a, ap_b) if first_player == player_a else (ap_b, ap_a)
    first_player_is_active = turn_number % 2 == 1

    # Reset activation flags
    for u in player_a.units + player_b.units:
        u.has_activated = False

    # Print board state at start of turn
    state = get_board_state(player_a, player_b, battlefield, turn_number, first_player if first_player_is_active else second_player)
    visualization = get_board_visualization(player_a, player_b, battlefield, state)
    #print("Board state at start of turn:")
    #print(visualization)
    #print(f"AP: {player_a.name}={ap_a}, {player_b.name}={ap_b}")

    # Activation loop
    while first_ap > 0 or second_ap > 0:
        all_a_done = all(not u.is_alive() or u.has_activated for u in first_player.units)
        all_b_done = all(not u.is_alive() or u.has_activated for u in second_player.units)

        if all_a_done and all_b_done:
            #print("All units on both sides activated or dead. Ending turn early.")
            break

        # If first player cannot activate a unit, we let them spend 1 AP doing nothing
        if first_ap > 0 and all_a_done:
            #print(f"{first_player.name} has no units to activate. Forcing AP usage.")
            first_ap -= 1

        # If second player cannot activate a unit, we do the same
        if second_ap > 0 and all_b_done:
            #print(f"{second_player.name} has no units to activate. Forcing AP usage.")
            second_ap -= 1

        # If after this both have no units and no AP to do anything meaningful, we might just break out
        if all_a_done and all_b_done:
            break

        # Try to activate first player's unit if they still have AP and not done
        if first_ap > 0 and not all_a_done:
            ap_spent = activate_unit_this_turn(first_player, second_player, battlefield, first_ap, first_player_is_active, turn_number)
            first_ap -= ap_spent

        # Try to activate second player's unit if they still have AP and not done
        if second_ap > 0 and not all_b_done:
            ap_spent = activate_unit_this_turn(second_player, first_player, battlefield, second_ap, not first_player_is_active, turn_number)
            second_ap -= ap_spent

        # If no progress is made in a loop iteration (no AP spent), consider breaking out.
        if ap_spent == 0 and all_a_done and all_b_done:
            # Safety check to avoid infinite loop
            break

    # Scoring Phase
    score_control_points(player_a, player_b, battlefield)
    #print(f"End of Turn {turn_number} Scores: {player_a.name}={player_a.score}, {player_b.name}={player_b.score}")

def activate_unit_this_turn(active_player, opposing_player, battlefield, ap_available, active_a, turn_number):
    
    if active_a:
        chosen_unit = ai_third_input.ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number)
    else:
        chosen_unit = ai_third_input.ai_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number)
    # After AI moves and optionally attacks/charges, mark AP spent
    if chosen_unit:
        #print(f"{active_player.name}'s unit {chosen_unit.name} spent {chosen_unit.ap_cost} AP this activation.")
        return chosen_unit.ap_cost
    else:
        return 0

def score_control_points(player_a, player_b, battlefield):
    for i, cp in enumerate(battlefield.control_points, start=1):
        a_models = util.count_models_in_range(player_a, cp, 6)
        b_models = util.count_models_in_range(player_b, cp, 6)
        
        if a_models > b_models:
            player_a.score += 1
            # Increment CP capture for all units from player_a in range
            for u in player_a.units:
                dist = util.distance(u.position, (cp.x, cp.y))
                if dist <= 6 and u.is_alive():
                    u.record_cp_capture()
        elif b_models > a_models:
            player_b.score += 1
            # Increment CP capture for all units from player_b in range
            for u in player_b.units:
                dist = util.distance(u.position, (cp.x, cp.y))
                if dist <= 6 and u.is_alive():
                    u.record_cp_capture()

def adjust_costs_based_on_performance(player_a, player_b, stat_costs, keyword_costs):
    # If a unit captured a CP or destroyed an enemy unit, increase addon costs
    # If a unit was destroyed or never scored a CP, decrease addon costs
    delta_positive = 0.01
    delta_negative = -0.01

    for player in [player_a, player_b]:
        for u in player.units:
            if u.category is None:
                # Means no modifications were applied, skip
                continue
            cat = u.category
            # If unit is destroyed or never captured CP:
            # Check destruction
            unit_destroyed = not u.is_alive()

            # Conditions for increase:
            # If unit captured CP or destroyed enemy
            performed_well = (u.cp_captured > 0 or u.enemies_destroyed > 0)
            # Conditions for decrease:
            # If unit is destroyed or no CP captured
            performed_poorly = (unit_destroyed or u.cp_captured == 0)

            # If performed well, increase cost for chosen addons
            if performed_well:
                for kw in u.chosen_keywords:
                    keyword_costs[cat][kw] = max(0.0, keyword_costs[cat][kw] + delta_positive)
                for st in u.chosen_stats:
                    stat_costs[cat][st] = max(0.0, stat_costs[cat][st] + delta_positive)

            # If performed poorly, decrease cost
            if performed_poorly:
                for kw in u.chosen_keywords:
                    keyword_costs[cat][kw] = max(0.0, keyword_costs[cat][kw] + delta_negative)
                for st in u.chosen_stats:
                    stat_costs[cat][st] = max(0.0, stat_costs[cat][st] + delta_negative)
