# main_ai.py
import statistics
from unit import Unit
import game
from player import Player
import battlefield
import setup
import random

def setup_players():
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

    player1_units = [
        Unit(**solar_knights_data),
        Unit(**solar_knights_data),
    ]

    player2_units = [
        Unit(**alien_warriors_data),
        Unit(**alien_warriors_data),
        Unit(**alien_warriors_data),
        Unit(**shooty_aliens_data),
        Unit(**shooty_aliens_data)
    ]

    player1 = Player(name="Frank", units=player1_units)
    player2 = Player(name="Dee", units=player2_units)

    return player1, player2

def run_simulation(num_games=10):
    results = []
    for i in range(num_games):
        player1, player2 = setup_players()
        control_points, width, height = setup.setup_battlefield()
        bf = battlefield.Battlefield(width, height, control_points, [])
        setup.place_units_randomly(player1, player2)

        game.play_game(player1, player2, bf)

        if player1.score > player2.score:
            results.append("Player1")
        elif player2.score > player1.score:
            results.append("Player2")
        else:
            results.append("Draw")

    # Print results summary
    p1_wins = results.count("Player1")
    p2_wins = results.count("Player2")
    draws = results.count("Draw")
    print(f"Out of {num_games} games:")
    print(f"Player 1 wins: {p1_wins}")
    print(f"Player 2 wins: {p2_wins}")
    print(f"Draws: {draws}")

if __name__ == "__main__":
    run_simulation(100)  # Run 100 games for testing
