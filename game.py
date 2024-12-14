from genetic_ai import genetic_ai_activate_unit
from genetic import Strategy, genetic_algorithm
import ap
import util
import random
from board_state import get_board_state
from user_input import user_activate_unit
from unit import Unit
import game
from player import Player
import battlefield
import setup

def play_game(player_a, player_b, battlefield, strategy_a=None, strategy_b=None):
    # Initial deployment
    # deploy_units(player_a, battlefield, side='left')
    # deploy_units(player_b, battlefield, side='right')

    for turn_number in range(1, 5):
        play_turn(player_a, player_b, battlefield, turn_number, strategy_a, strategy_b)

    # End of game
    if player_a.score > player_b.score:
        print(f"{player_a.name} wins!")
    elif player_b.score > player_a.score:
        print(f"{player_b.name} wins!")
    else:
        print("It's a draw!")

def play_turn(player_a, player_b, battlefield, turn_number, strategy_a, strategy_b):
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
            ap_spent = activate_unit_this_turn(first_player, second_player, battlefield, first_ap, first_player_is_active, turn_number, strategy_a if first_player == player_a else strategy_b)
            if ap_spent == 0:
                first_ap = 0
            else:
                first_ap -= ap_spent

        # Second player activation
        if second_ap > 0:
            ap_spent = activate_unit_this_turn(second_player, first_player, battlefield, second_ap, not first_player_is_active, turn_number, strategy_a if second_player == player_a else strategy_b)
            if ap_spent == 0:
                second_ap = 0
            else:
                second_ap -= ap_spent

        # If both players can't activate, break
        if first_ap <= 0 and second_ap <= 0:
            break

    # Scoring Phase
    score_control_points(player_a, player_b, battlefield)

def activate_unit_this_turn(active_player, opposing_player, battlefield, ap_available, active_a, turn_number, strategy):
    if strategy:
        # Use genetic AI
        chosen_unit = genetic_ai_activate_unit(active_player, opposing_player, battlefield, strategy, turn_number)
    else:
        # Use user input for activation
        chosen_unit = user_activate_unit(active_player, opposing_player, battlefield, active_a, turn_number)

    # After activation, mark AP spent
    if chosen_unit:
        return chosen_unit.ap_cost
    return 0

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

def score_control_points(player_a, player_b, battlefield):
    for i, cp in enumerate(battlefield.control_points, start=1):
        a_models = util.count_models_in_range(player_a, cp, 3)
        b_models = util.count_models_in_range(player_b, cp, 3)
        
        if a_models > b_models:
            player_a.score += 1
        elif b_models > a_models:
            player_b.score += 1
    print(f"Turn Score: Player A - {player_a.score}, Player B - {player_b.score}")

# Example of integration with genetic strategies
if __name__ == "__main__":
    # Define unit data
    solar_knights_data = {
        "name": "Solar Knights",
        "num_models": 5,
        "wounds_per_model": 2,
        "armor": "Medium Armor",
        "movement": 6,
        "ap_cost": 4,
        "missile_attack_dice": ['Blue'] * 5,
        "melee_attack_dice": ['Green'] * 5,
        "attack_range": 18,
        "special_rules": None,
        "keywords": ["Withering Fire"]
    }

    heavy_solar_knights_data = {
        "name": "Heavy Solar Knights",
        "num_models": 5,
        "wounds_per_model": 2,
        "armor": "Heavy Armor",
        "movement": 5,
        "ap_cost": 4,
        "missile_attack_dice": ['Blue'] * 5,
        "melee_attack_dice": ['Green'] * 5,
        "attack_range": 24,
        "special_rules": None,
        "keywords": ["Withering Fire", "Relentless"]
    }

    alien_warriors_data = {
        "name": "Alien Warriors",
        "num_models": 10,
        "wounds_per_model": 1,
        "armor": "Light Armor",
        "movement": 8,
        "ap_cost": 3,
        "missile_attack_dice": [],
        "melee_attack_dice": ['Pink'] * 10,
        "attack_range": 0,
        "special_rules": None,
        "keywords": ["Relentless"]
    }

    shooty_aliens_data = {
        "name": "Shooty Aliens",
        "num_models": 10,
        "wounds_per_model": 1,
        "armor": "Light Armor",
        "movement": 8,
        "ap_cost": 3,
        "missile_attack_dice": ['Blue'] * 10,
        "melee_attack_dice": ['Pink'] * 5,
        "attack_range": 18,
        "special_rules": None,
        "keywords": ["Withering Fire"]
    }

    # Create units
    player1_units = [
        Unit(**solar_knights_data),
        Unit(**solar_knights_data),
        Unit(**heavy_solar_knights_data)
    ]

    player2_units = [
        Unit(**alien_warriors_data),
        Unit(**alien_warriors_data),
        Unit(**alien_warriors_data),
        Unit(**shooty_aliens_data),
        Unit(**shooty_aliens_data)
    ]

    # Create players
    player1 = Player(name="Frank", units=player1_units)
    player2 = Player(name="Dee", units=player2_units)

    # Setup battlefield
    control_points, width, height = setup.setup_battlefield()
    bf = battlefield.Battlefield(width, height, control_points, [])

    # Genetic algorithm loop for strategy refinement
    generations = 20
    population_size = 50
    evolution_iterations = 1000  # Number of times to simulate games and evolve strategies

    # Initial population
    strategies = genetic_algorithm(generations=generations, population_size=population_size)

    for iteration in range(evolution_iterations):
        print(f"\n--- Evolution Iteration {iteration + 1} ---\n")
        strategy_a = strategies[0]  # Best strategy for player A
        strategy_b = strategies[1]  # Second best strategy for player B

        # Place units randomly
        setup.place_units_randomly(player1, player2)

        # Simulate game
        play_game(player1, player2, bf, strategy_a, strategy_b)

        # Use the results to evolve strategies
        strategies = genetic_algorithm(generations=generations, population_size=population_size)

    # Output final strategies
    final_strategy_a = strategies[0]
    final_strategy_b = strategies[1]
    print("\nFinal Strategies:")
    print(f"Player A Strategy: {vars(final_strategy_a)}")
    print(f"Player B Strategy: {vars(final_strategy_b)}")

