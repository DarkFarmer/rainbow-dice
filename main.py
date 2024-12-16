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


# Define all unit types from your spreadsheet (initially all AP=1)
unit_templates = {
    "Basic Infantry": {
        "num_models": 5, "movement": 6, "armor_save": 6, "wounds": 1,
        "melee_dice": ["White"], "ranged_dice": ["White"], "range": 12, "ap_cost": 1.5
    },
    "Elite Infantry": {
        "num_models": 5, "movement": 6, "armor_save": 5, "wounds": 1,
        "melee_dice": ["Green"], "ranged_dice": ["Green"], "range": 12, "ap_cost": 4
    },
    "Heavy Weapons": {
        "num_models": 5, "movement": 6, "armor_save": 6, "wounds": 1,
        "melee_dice": ["Purple"], "ranged_dice": ["Purple"], "range": 12, "ap_cost": 4
    },
    "Fast Attack": {
        "num_models": 5, "movement": 12, "armor_save": 6, "wounds": 1,
        "melee_dice": ["White"], "ranged_dice": ["White"], "range": 12, "ap_cost": 6.5
    },
    "Mech": {
        "num_models": 1, "movement": 8, "armor_save": 4, "wounds": 4,
        "melee_dice": ["Green","Green","Green","Green","Green"],
        "ranged_dice": ["Green","Green","Green","Green","Green"], "range": 12, "ap_cost": 5
    },
    "Aliens": {
        "num_models": 5, "movement": 8, "armor_save": 5, "wounds": 1,
        "melee_dice": ["Green"], "ranged_dice": [], "range": 0, "ap_cost": 4
    },
    "Heavy Infantry": {
        "num_models": 5, "movement": 5, "armor_save": 4, "wounds": 2,
        "melee_dice": ["Blue"], "ranged_dice": ["Blue"], "range": 12, "ap_cost": 4
    },
    "Super-Heavy Infantry": {
        "num_models": 5, "movement": 5, "armor_save": 3, "wounds": 3,
        "melee_dice": ["Purple"], "ranged_dice": ["Purple"], "range": 12, "ap_cost": 1
    },
    "Heavy Aliens": {
        "num_models": 5, "movement": 6, "armor_save": 4, "wounds": 2,
        "melee_dice": ["Purple"], "ranged_dice": [], "range": 0, "ap_cost": 4
    },
    "Tank": {
        "num_models": 1, "movement": 10, "armor_save": 4, "wounds": 4,
        "melee_dice": ["Green","Green"], "ranged_dice": ["Black","Green","Green"], "range": 24, "ap_cost": 6
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

def run_simulation():
    results = []
    # We'll run indefinitely until you cancel. Just a loop.
    i = 0
    while True:
        i += 1
        # Randomly pick 5 units for each player from the templates
        unit_names = list(unit_templates.keys())
        player1_choices = random.sample(unit_names, 5)
        player2_choices = random.sample(unit_names, 5)

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
            loser = "Player2"
        elif player2.score > player1.score:
            winner = "Player2"
            loser = "Player1"
        else:
            winner = None
            loser = None

        # Adjust AP based on result
        if winner is not None:
            # Increase winner units AP by 1
            for name in (player1_choices if winner == "Player1" else player2_choices):
                unit_templates[name]["ap_cost"] += 0.01
            # Decrease loser units AP by 1, but not below 1 (if you want a floor)
            for name in (player2_choices if winner == "Player1" else player1_choices):
                unit_templates[name]["ap_cost"] = max(1, unit_templates[name]["ap_cost"] - 0.01)

        # Print latest AP totals
        print(f"--- After Run {i} ---")
        for name in unit_templates:
            print(f"{name}: AP={unit_templates[name]['ap_cost']}")

if __name__ == "__main__":
    run_simulation()
