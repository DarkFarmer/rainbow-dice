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
        "wounds_per_model": 1,
        "armor": "Medium Armor",
        "movement": 6,
        "ap_cost": 4,
        "missile_attack_dice": ['Blue'] * 5,
        "melee_attack_dice": ['Blue'] * 5,
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
        "ap_cost": 5,
        "missile_attack_dice": ['Purple'] * 5,
        "melee_attack_dice": ['Purple'] * 5,
        "attack_range": 24,
        "special_rules": None,
        "keywords": ["Withering Fire", "Relentless"]
    }

    alien_warriors_data = {
        "name": "Alien Warriors",
        "num_models": 10,
        "wounds_per_model": 1,
        "armor": "Light Armor",
        "movement": 12,
        "ap_cost": 4,
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
        "ap_cost": 4,
        "missile_attack_dice": ['Blue'] * 10,
        "melee_attack_dice": ['White'] * 10,
        "attack_range": 18,
        "special_rules": None,
        "keywords": ["Withering Fire"]
    }

    player1_units = [
        Unit(**solar_knights_data),
        Unit(**solar_knights_data),
        Unit(**heavy_solar_knights_data),
        Unit(**heavy_solar_knights_data),
        Unit(**solar_knights_data),
    ]

    player2_units = [
        Unit(**alien_warriors_data),
        Unit(**alien_warriors_data),
        Unit(**alien_warriors_data),
        Unit(**shooty_aliens_data),
        Unit(**shooty_aliens_data),
    ]

    player1 = Player(name="Frank", units=player1_units)
    player2 = Player(name="Dee", units=player2_units)

    return player1, player2

def run_simulation(num_games=10):
    results = []
    p1_units_wiped = []
    p2_units_wiped = []
    p1_melee_kills = []
    p1_missile_kills = []
    p2_melee_kills = []
    p2_missile_kills = []

    for i in range(num_games):
        player1, player2 = setup_players()
        control_points, width, height = setup.setup_battlefield()
        bf = battlefield.Battlefield(width, height, control_points, [])
        setup.place_units_randomly(player1, player2)

        # Track kills and units wiped for this game
        player1.melee_kills = 0
        player1.missile_kills = 0
        player2.melee_kills = 0
        player2.missile_kills = 0

        game.play_game(player1, player2, bf)

        # Calculate percentage of units wiped out
        p1_wiped = sum(not unit.is_alive() for unit in player1.units) / len(player1.units) * 100
        p2_wiped = sum(not unit.is_alive() for unit in player2.units) / len(player2.units) * 100
        p1_units_wiped.append(p1_wiped)
        p2_units_wiped.append(p2_wiped)
        # Record kill details
        p1_melee_kills.append(player1.melee_kills)
        p1_missile_kills.append(player1.missile_kills)
        p2_melee_kills.append(player2.melee_kills)
        p2_missile_kills.append(player2.missile_kills)

        # Determine game result
        if player1.score > player2.score:
            results.append("Player1")
        elif player2.score > player1.score:
            results.append("Player2")
        else:
            results.append("Draw")

    # Summarize results
    p1_wins = results.count("Player1")
    p2_wins = results.count("Player2")
    draws = results.count("Draw")

    # Calculate averages
    avg_p1_wiped = statistics.mean(p1_units_wiped)
    avg_p2_wiped = statistics.mean(p2_units_wiped)
    avg_p1_melee = statistics.mean(p1_melee_kills)
    avg_p1_missile = statistics.mean(p1_missile_kills)
    avg_p2_melee = statistics.mean(p2_melee_kills)
    avg_p2_missile = statistics.mean(p2_missile_kills)

    print(f"Out of {num_games} games:")
    print(f"Player 1 wins: {p1_wins}")
    print(f"Player 2 wins: {p2_wins}")
    print(f"Draws: {draws}\n")

    print(f"Average Units Wiped: Player 1 = {avg_p1_wiped:.2f}%, Player 2 = {avg_p2_wiped:.2f}%")
    print(f"Average Kills: Player 1 - Melee = {avg_p1_melee:.2f}, Missile = {avg_p1_missile:.2f}")
    print(f"Average Kills: Player 2 - Melee = {avg_p2_melee:.2f}, Missile = {avg_p2_missile:.2f}")

if __name__ == "__main__":
    run_simulation(1000)  # Run 100 games for testing
