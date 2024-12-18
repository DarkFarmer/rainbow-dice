import statistics
import random
from unit import Unit
import game
from player import Player
import battlefield
import setup
from dice import DICE_TYPES

DICE_MAPPING = {
    'White': 'White',
    'Green': 'Green',
    'Blue': 'Blue',
    'Purple': 'Purple',
    'Pink': 'Pink',
    'Black': 'Black',
    'Gunmetal': 'Gunmetal',
    'Silver': 'Silver',
    'Gold': 'Gold',
    'Red': 'Red',
    'Crimson': 'Crimson',
}

KEYWORDS_LIST = [
    "Shields",
    "Last Stand",
    "Degrade",
    "Commander",
    "Camouflage",
    "Sharpshooter",
    "Attack Augmentation",
    "Crushing Charge",
    "Withering Fire",
    "Relentless",
    "Slayer",
    "Lucky",
    "Assassin"
]

STAT_MODS = [
    "num_models",
    "wounds_per_model",
    "armor",
    "movement",
    "missile_attack_dice",
    "melee_attack_dice",
    "attack_range"
]

ARMOR_TIERS = ['Unarmored', 'Light Armor', 'Medium Armor', 'Heavy Armor']

# Cost dictionaries split by category
# Categories: "<=2", "<=4", ">4"
keyword_costs = {
    "<=2": {kw: 0.1 for kw in KEYWORDS_LIST},
    "<=4": {kw: 0.1 for kw in KEYWORDS_LIST},
    ">4": {kw: 0.1 for kw in KEYWORDS_LIST}
}

stat_costs = {
    "<=2": {},
    "<=4": {},
    ">4": {}
}

# Initialize stat costs for each category
base_stat_keys = [
    "num_models_10",
    "wounds_per_model+1",
    "armor_improved",
    "movement+2",
    "attack_range+4",
]

for cat in stat_costs:
    for stk in base_stat_keys:
        stat_costs[cat][stk] = 0.1
    # For dice additions
    for dtype in DICE_TYPES.keys():
        stat_costs[cat][f"missile_die_{dtype}"] = 0.1
        stat_costs[cat][f"melee_die_{dtype}"] = 0.1

def num_keywords_to_add():
    x = random.random()
    if x < 0.7:
        return 0
    elif x < 0.9:
        return 1
    else:
        return 2

def num_stats_to_add():
    x = random.random()
    if x < 0.5:
        return 0
    elif x < 0.8:
        return 1
    elif x < 0.95:
        return 2
    elif x < 0.99:
        return 3
    else:
        return 4

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

def create_unit(name, data):
    armor = {
        6: 'Unarmored',
        5: 'Light Armor',
        4: 'Medium Armor',
        3: 'Heavy Armor'
    }.get(data["armor_save"], 'Light Armor')

    melee_attack_dice = []
    for _ in range(data["num_models"]):
        melee_attack_dice.extend([DICE_MAPPING[d] for d in data["melee_dice"]])

    missile_attack_dice = []
    if data["ranged_dice"]:
        for _ in range(data["num_models"]):
            missile_attack_dice.extend([DICE_MAPPING[d] for d in data["ranged_dice"]])

    u = Unit(
        name=name,
        num_models=data["num_models"],
        wounds_per_model=data["wounds"],
        armor=armor,
        movement=data["movement"],
        ap_cost=data["ap_cost"],
        missile_attack_dice=missile_attack_dice,
        melee_attack_dice=melee_attack_dice,
        attack_range=data["range"],
        special_rules=None,
        keywords=[]
    )
    return u

def get_category(ap_cost):
    if ap_cost <= 2:
        return "<=2"
    elif ap_cost <=4:
        return "<=4"
    else:
        return ">4"

def apply_random_modifications(unit):
    # Determine category from base AP (before modifications)
    base_category = get_category(unit.ap_cost)

    k_count = num_keywords_to_add()
    s_count = num_stats_to_add()

    chosen_keywords = []
    chosen_stats = []

    # Add keywords
    if k_count > 0:
        picked_keywords = random.sample(KEYWORDS_LIST, k_count)
        for kw in picked_keywords:
            unit.keywords.append(kw)
            chosen_keywords.append(kw)

    # Add stat modifications
    if s_count > 0:
        chosen_mods = random.sample(STAT_MODS, s_count)
        for smod in chosen_mods:
            stat_key = apply_stat_mod(unit, smod)
            if stat_key:
                chosen_stats.append(stat_key)

    # Calculate cost from this category
    add_cost = 0.0
    for kw in chosen_keywords:
        add_cost += keyword_costs[base_category][kw]

    for st in chosen_stats:
        add_cost += stat_costs[base_category][st]

    unit.ap_cost += add_cost

    return base_category, chosen_keywords, chosen_stats

def apply_stat_mod(unit, smod):
    if smod == "num_models":
        if unit.num_models < 10:
            unit.num_models = 10
            # Add 5 additional basic attack dice for both melee and missile
            if unit.base_melee_attack_dice:
                basic_melee_die = unit.base_melee_attack_dice[0]  # First die type in melee pool
                unit.base_melee_attack_dice.extend([basic_melee_die] * 5)
            if unit.base_missile_attack_dice:
                basic_missile_die = unit.base_missile_attack_dice[0]  # First die type in missile pool
                unit.base_missile_attack_dice.extend([basic_missile_die] * 5)
            return "num_models_10"

    elif smod == "wounds_per_model":
        unit.wounds_per_model += 1
        return "wounds_per_model+1"

    elif smod == "armor":
        if unit.armor in ARMOR_TIERS:
            idx = ARMOR_TIERS.index(unit.armor)
            if idx < len(ARMOR_TIERS)-1:
                unit.armor = ARMOR_TIERS[idx+1]
                return "armor_improved"

    elif smod == "movement":
        unit.movement += 2
        return "movement+2"

    elif smod == "missile_attack_dice":
        die_type = random.choice(list(DICE_TYPES.keys()))
        unit.base_missile_attack_dice.append(die_type)
        return f"missile_die_{die_type}"

    elif smod == "melee_attack_dice":
        die_type = random.choice(list(DICE_TYPES.keys()))
        unit.base_melee_attack_dice.append(die_type)
        return f"melee_die_{die_type}"

    elif smod == "attack_range":
        unit.attack_range += 4
        return "attack_range+4"

    return None

def adjust_costs_for_results(player_mods, winner):
    # player_mods: list of tuples (cat, [keywords], [stats])
    # winner: True/False
    delta = 0.01 if winner else -0.01

    for (cat, kw_list, st_list) in player_mods:
        for kw in kw_list:
            new_val = keyword_costs[cat][kw] + delta
            keyword_costs[cat][kw] = new_val
        for st in st_list:
            new_val = stat_costs[cat][st] + delta
            stat_costs[cat][st] = new_val

def run_simulation():
    i = 0
    while True:
        i += 1
        unit_names = list(unit_templates.keys())
        player1_choices = random.sample(unit_names, 5)
        player2_choices = random.sample(unit_names, 5)

        player1_units = []
        player2_units = []
        player1_mods = []
        player2_mods = []

        # Build and modify Player1 units
        for name in player1_choices:
            data = unit_templates[name]
            u = create_unit(name, data)
            cat, kws, sts = apply_random_modifications(u)
            player1_mods.append((cat, kws, sts))
            player1_units.append(u)

        # Build and modify Player2 units
        for name in player2_choices:
            data = unit_templates[name]
            u = create_unit(name, data)
            cat, kws, sts = apply_random_modifications(u)
            player2_mods.append((cat, kws, sts))
            player2_units.append(u)

        player1 = Player(name="Player1", units=player1_units)
        player2 = Player(name="Player2", units=player2_units)

        control_points, width, height = setup.setup_battlefield()
        bf = battlefield.Battlefield(width, height, control_points, [])
        setup.place_terrain(bf)
        setup.place_units_randomly(player1, player2)

        game.play_game(player1, player2, bf)

        if player1.score > player2.score:
            adjust_costs_for_results(player1_mods, True)
            adjust_costs_for_results(player2_mods, False)
        elif player2.score > player1.score:
            adjust_costs_for_results(player1_mods, False)
            adjust_costs_for_results(player2_mods, True)
        else:
            # Draw: no cost adjustments
            pass

        if i % 100 == 0:
            print(f"--- After Run {i} ---")
            for cat in ["<=2", "<=4", ">4"]:
                print(f"Category {cat}:")
                print(" Keyword Costs:")
                for kw, c in keyword_costs[cat].items():
                    print(f"  {kw}: {c:.2f}")
                print(" Stat Costs:")
                for st, c in stat_costs[cat].items():
                    print(f"  {st}: {c:.2f}")

if __name__ == "__main__":
    run_simulation()
