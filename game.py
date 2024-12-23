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
    # 1) Determine AP for both
    ap_a, ap_b = ap.determine_ap_allocation(player_a, player_b)

    # By your existing logic, maybe Player A = user, Player B = AI
    # Or you can decide it differently
    user_player = player_a
    ai_player = player_b

    # Reset each unit’s has_activated
    for u in player_a.units + player_b.units:
        u.has_activated = False

    # Print board state at start of turn (optional)
    state = get_board_state(player_a, player_b, battlefield, turn_number, user_player)
    visualization = get_board_visualization(player_a, player_b, battlefield, state)
    #print(f"Board state at start of Turn {turn_number}:")
    #print(visualization)
    #print(f"AP: {player_a.name}={ap_a}, {player_b.name}={ap_b}")

    # 2) Alternate single activations
    while True:
        all_user_done = all(not u.is_alive() or u.has_activated for u in user_player.units)
        all_ai_done   = all(not u.is_alive() or u.has_activated for u in ai_player.units)

        # If both players have no AP left or all units are done, break
        if (ap_a <= 0 and ap_b <= 0) or (all_user_done and all_ai_done):
            break

        # A) Human Activation (only if AP left and not all done)
        if ap_a > 0 and not all_user_done:
            spent = activate_unit_this_turn(user_player, ai_player, battlefield, ap_a, turn_number)
            ap_a -= spent

        # B) AI Activation (only if AP left and not all done)
        if ap_b > 0 and not all_ai_done:
            spent = activate_unit_this_turn(ai_player, user_player, battlefield, ap_b, turn_number)
            ap_b -= spent

        # If we get here and neither side could do anything, break to avoid infinite loop
        if (ap_a <= 0 or all_user_done) and (ap_b <= 0 or all_ai_done):
            break

    # Scoring after all activations
    score_control_points(player_a, player_b, battlefield)
    print(f"End of Turn {turn_number} Scores: {player_a.name}={player_a.score}, {player_b.name}={player_b.score}")

def activate_unit_this_turn(active_player, opposing_player, battlefield, ap_available, turn_number):
    """
    Perform exactly one unit activation for 'active_player'.
    Return the AP cost spent.
    """
    if active_player.is_human:
        from user_input import user_activate_unit
        chosen_unit = user_activate_unit(
            active_player, opposing_player, battlefield, 
            active_a=True,  # or False if you like, not critical now
            turn_number=turn_number
        )
    else:
        from ai_third_input import ai_activate_unit
        chosen_unit = ai_activate_unit(
            active_player, opposing_player, battlefield, 
            active_a=False,  # or True if you prefer, purely for AI logic
            turn_number=turn_number
        )

    if chosen_unit:
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
