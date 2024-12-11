from unit import Unit
import game
from player import Player
import battlefield
import setup

def main():
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

    # Place units randomly
    setup.place_units_randomly(player1, player2)

    # Start the game
    game.play_game(player1, player2, bf)

if __name__ == "__main__":
    main()
