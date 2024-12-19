import statistics
import random
from unit import Unit
import game
import util
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

    # Store chosen addons in the unit for reference at end of game
    unit.chosen_keywords = chosen_keywords
    unit.chosen_stats = chosen_stats
    unit.category = base_category

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

def run_simulation():
    # Number of games to run per batch
    BATCH_SIZE = 1000
    game_number = 0

    # Track performance of keywords and stats
    # Structure: performance_data[category]["keywords"][kw] = {"wins":X, "losses":Y}
    # Similarly for stats.
    performance_data = {
        "<=2": {"keywords": {}, "stats": {}},
        "<=4": {"keywords": {}, "stats": {}},
        ">4": {"keywords": {}, "stats": {}},
    }

    # Initialize performance_data counters
    for cat in performance_data:
        for kw in KEYWORDS_LIST:
            performance_data[cat]["keywords"][kw] = {"wins":0,"losses":0}
        for stcat in stat_costs[cat].keys():
            performance_data[cat]["stats"][stcat] = {"wins":0,"losses":0}
        # Also include dice expansions:
        for st in stat_costs[cat].keys():
            # already covered above
            pass

    while True:
        # Run a batch of BATCH_SIZE games
        for _ in range(BATCH_SIZE):
            game_number += 1
            unit_names = list(unit_templates.keys())
            player1_choices = random.sample(unit_names, 5)
            player2_choices = random.sample(unit_names, 5)

            player1_units = []
            player2_units = []
            player1_mods = []
            player2_mods = []

            for name in player1_choices:
                data = unit_templates[name]
                u = create_unit(name, data)
                cat, kws, sts = apply_random_modifications(u)
                player1_mods.append((cat, kws, sts))
                player1_units.append(u)

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

            game.play_game(player1, player2, bf, stat_costs, keyword_costs)

            # Determine winner, record performance
            if player1.score > player2.score:
                # player1 wins, increment "wins" for their keywords/stats
                # player2 loses, increment "losses" for theirs
                for (cat, kw_list, st_list) in player1_mods:
                    for kw in kw_list:
                        performance_data[cat]["keywords"][kw]["wins"] += 1
                    for st in st_list:
                        performance_data[cat]["stats"][st]["wins"] += 1

                for (cat, kw_list, st_list) in player2_mods:
                    for kw in kw_list:
                        performance_data[cat]["keywords"][kw]["losses"] += 1
                    for st in st_list:
                        performance_data[cat]["stats"][st]["losses"] += 1

            elif player2.score > player1.score:
                # player2 wins
                for (cat, kw_list, st_list) in player2_mods:
                    for kw in kw_list:
                        performance_data[cat]["keywords"][kw]["wins"] += 1
                    for st in st_list:
                        performance_data[cat]["stats"][st]["wins"] += 1

                for (cat, kw_list, st_list) in player1_mods:
                    for kw in kw_list:
                        performance_data[cat]["keywords"][kw]["losses"] += 1
                    for st in st_list:
                        performance_data[cat]["stats"][st]["losses"] += 1
            else:
                # Draw: no changes
                pass

        # After BATCH_SIZE games, do batch cost adjustment
        # For each category, keyword, and stat:
        # net = wins - losses
        # if net > 0 => increase cost, if net <0 => decrease cost
        # Then reset counters for the next batch
        for cat in performance_data:
            # Keywords
            for kw, data in performance_data[cat]["keywords"].items():
                net = data["wins"] - data["losses"]
                if net != 0:
                    adjustment = 0.01 * net  # Base adjustment scaled by performance
                    current_cost = keyword_costs[cat][kw]

                    # Apply EMA adjustment
                    new_cost = util.ema_adjustment(current_cost, adjustment)

                    # Ensure no cost drops below zero unless the keyword is "Degrade"
                    if kw != "Degrade" and new_cost < 0:
                        new_cost = 0
                    elif kw == "Degrade" and new_cost > 0:
                        new_cost = 0

                    keyword_costs[cat][kw] = new_cost

                # Reset counters
                data["wins"] = 0
                data["losses"] = 0

            # Stats
            for st, data in performance_data[cat]["stats"].items():
                net = data["wins"] - data["losses"]
                if net != 0:
                    adjustment = 0.01 * net  # Base adjustment scaled by performance
                    current_cost = stat_costs[cat][st]

                    # Apply EMA adjustment
                    new_cost = util.ema_adjustment(current_cost, adjustment)

                    # Ensure no cost drops below zero
                    if new_cost < 0:
                        new_cost = 0

                    stat_costs[cat][st] = new_cost

                # Reset counters
                data["wins"] = 0
                data["losses"] = 0

        # Print results after each batch
        print(f"--- After {game_number} Games (Batch of {BATCH_SIZE}) ---")
        for cat in ["<=2", "<=4", ">4"]:
            print(f"Category {cat}:")
            print(" Keyword Costs:")
            for kw, c in keyword_costs[cat].items():
                print(f"  {kw}: {c:.2f}")
            print(" Stat Costs:")
            for st, c in stat_costs[cat].items():
                print(f"  {st}: {c:.2f}")
        print()

if __name__ == "__main__":
    run_simulation()
