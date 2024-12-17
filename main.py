import statistics
import random
from unit import Unit
import game
from player import Player
import battlefield
import setup

# Mapping dice colors to your dice notation. Adjust as needed.
DICE_MAPPING = {
    'White': 'White',
    'Green': 'Green',
    'Blue': 'Blue',
    'Purple': 'Purple',
    'Pink': 'Pink',
    'Black': 'Black',
}

# Define a function to create a unit
def create_unit(name, num_models, movement, armor_save, wounds_per_model,
                melee_dice_per_model, ranged_dice_per_model, range_distance, ap_cost):
    armor = {
        6: 'Unarmored',
        5: 'Light Armor',
        4: 'Medium Armor',
        3: 'Heavy Armor'
    }.get(armor_save, 'Light Armor')

    melee_attack_dice = []
    for _ in range(num_models):
        melee_attack_dice.extend([DICE_MAPPING[d] for d in melee_dice_per_model])

    missile_attack_dice = []
    if ranged_dice_per_model:
        for _ in range(num_models):
            missile_attack_dice.extend([DICE_MAPPING[d] for d in ranged_dice_per_model])

    return Unit(
        name=name,
        num_models=num_models,
        wounds_per_model=wounds_per_model,
        armor=armor,
        movement=movement,
        ap_cost=ap_cost,
        missile_attack_dice=missile_attack_dice,
        melee_attack_dice=melee_attack_dice,
        attack_range=range_distance,
        special_rules=None,
        keywords=[]
    )

#--- After Run 2294960 ---
#Basic Infantry: AP=3.639999999999966
#Elite Infantry: AP=8.489999999999863
#Heavy Weapons: AP=10.609999999999818
#Fast Attack: AP=17.439999999999927
#Mech: AP=15.18999999999972
#Aliens: AP=10.689999999999817
#Heavy Infantry: AP=9.799999999999836
#Super-Heavy Infantry: AP=14.369999999999738
#Heavy Aliens: AP=3.389999999999972
#Tank: AP=16.579999999999792

# Define all unit types from your spreadsheet (initially all AP=1) 3.5
unit_templates = {
    "Basic Infantry": {
        "num_models": 5, "movement": 6, "armor_save": 6, "wounds": 1,
        "melee_dice": ["White"], "ranged_dice": ["White"], "range": 12, "ap_cost": 1
    },
    "Elite Infantry": {
        "num_models": 5, "movement": 6, "armor_save": 5, "wounds": 1,
        "melee_dice": ["Green"], "ranged_dice": ["Green"], "range": 12, "ap_cost": 2.5
    },
    "Heavy Weapons": {
        "num_models": 5, "movement": 6, "armor_save": 6, "wounds": 1,
        "melee_dice": ["Purple"], "ranged_dice": ["Purple"], "range": 12, "ap_cost": 3
    },
    "Fast Attack": {
        "num_models": 5, "movement": 12, "armor_save": 6, "wounds": 1,
        "melee_dice": ["White"], "ranged_dice": ["White"], "range": 12, "ap_cost": 5
    },
    "Mech": {
        "num_models": 1, "movement": 8, "armor_save": 4, "wounds": 4,
        "melee_dice": ["Blue","Blue","Blue","Blue","Blue"],
        "ranged_dice": ["Blue","Blue","Blue","Blue","Blue"], "range": 12, "ap_cost": 4
    },
    "Aliens": {
        "num_models": 5, "movement": 8, "armor_save": 5, "wounds": 1,
        "melee_dice": ["Green"], "ranged_dice": [], "range": 0, "ap_cost": 3
    },
    "Heavy Infantry": {
        "num_models": 5, "movement": 5, "armor_save": 4, "wounds": 2,
        "melee_dice": ["Blue"], "ranged_dice": ["Blue"], "range": 12, "ap_cost": 3
    },
    "Super-Heavy Infantry": {
        "num_models": 5, "movement": 5, "armor_save": 3, "wounds": 3,
        "melee_dice": ["Purple"], "ranged_dice": ["Purple"], "range": 12, "ap_cost": 4
    },
    "Heavy Aliens": {
        "num_models": 5, "movement": 6, "armor_save": 4, "wounds": 2,
        "melee_dice": ["Purple"], "ranged_dice": [], "range": 0, "ap_cost": 1
    },
    "Tank": {
        "num_models": 1, "movement": 10, "armor_save": 4, "wounds": 4,
        "melee_dice": ["Green","Green"], "ranged_dice": ["Black","Green","Green"], "range": 24, "ap_cost": 5
    },
}

def build_unit_from_template(name, template):
    return create_unit(
        name,
        template["num_models"],
        template["movement"],
        template["armor_save"],
        template["wounds"],
        template["melee_dice"],
        template["ranged_dice"],
        template["range"],
        template["ap_cost"]
    )

def run_simulation(total_value):
    """
    Simulates battles with equivalently valued forces for both players and
    evaluates win rates.

    Args:
        total_value (int): The total value of units for each player.
    """
    results = []
    i = 0

    def select_units_for_value(target_value):
        """
        Selects a combination of units that matches the target value.

        Args:
            target_value (int): The total value to match.

        Returns:
            list: A list of unit names whose combined value matches the target.
        """
        unit_names = list(unit_templates.keys())
        while True:
            choices = [random.choice(unit_names) for _ in range(5)]
            total_cost = sum(unit_templates[name]["ap_cost"] for name in choices)
            print(f"makin a list cost:  {total_cost}")
            if abs(total_cost - target_value) < 10:  # Allowing a small tolerance
                return choices

    while True:
        i += 1

        # Choose units for each player with equivalent total value
        player1_choices = select_units_for_value(total_value)
        player2_choices = select_units_for_value(total_value)

        player1_units = [build_unit_from_template(name, unit_templates[name]) for name in player1_choices]
        player2_units = [build_unit_from_template(name, unit_templates[name]) for name in player2_choices]

        player1 = Player(name="Player1", units=player1_units)
        player2 = Player(name="Player2", units=player2_units)

        control_points, width, height = setup.setup_battlefield()
        bf = battlefield.Battlefield(width, height, control_points, [])
        setup.place_units_randomly(player1, player2)

        game.play_game(player1, player2, bf)

        # Determine result
        if player1.score > player2.score:
            winner = "Player1"
            results.append(winner)
        elif player2.score > player1.score:
            winner = "Player2"
            results.append(winner)
        else:
            results.append("Draw")

        # Print results summary every 10 runs
        
        player1_wins = results.count("Player1")
        player2_wins = results.count("Player2")
        draws = results.count("Draw")
        total_games = len(results)

        print(f"--- After {i} Runs ---")
        print(f"Player1 Wins: {player1_wins} ({player1_wins / total_games:.2%})")
        print(f"Player2 Wins: {player2_wins} ({player2_wins / total_games:.2%})")
        print(f"Draws: {draws} ({draws / total_games:.2%})")


if __name__ == "__main__":
    run_simulation(22)
