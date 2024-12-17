import statistics
import random
from unit import Unit
import game
from player import Player
import battlefield
import setup

from dice import DICE_TYPES  # Assuming dice.py is available and has DICE_TYPES

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

# Keywords list
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

# Possible stat modifications
STAT_MODS = [
    "num_models",          # increase from 5 to 10 (if applicable)
    "wounds_per_model",    # increase by 1
    "armor",               # improve one step
    "movement",            # increase by 2
    "missile_attack_dice", # add one random die
    "melee_attack_dice",   # add one random die
    "attack_range"         # increase by 4
]

ARMOR_TIERS = ['Unarmored', 'Light Armor', 'Medium Armor', 'Heavy Armor']
# Probability distributions (tweak as needed):
# Keywords: 0 keywords ~70%, 1 keyword ~20%, 2 keywords ~10%
# Stats: 0 mods ~50%, 1 mod ~30%, 2 mods ~15%, 3 mods ~4%, 4 mods ~1%
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

# Unit templates as given
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

# Tracking dictionaries:
# keys: category ("<=2 AP", "<=4 AP", ">4 AP"), then keyword/stat -> track occurrences and performance
keyword_stats = {
    "<=2": {},
    "<=4": {},
    ">4": {}
}
stat_mod_stats = {
    "<=2": {},
    "<=4": {},
    ">4": {}
}

def get_category(ap_cost):
    if ap_cost <= 2:
        return "<=2"
    elif ap_cost <=4:
        return "<=4"
    else:
        return ">4"

def apply_random_modifications(unit):
    base_ap = unit.ap_cost
    category = get_category(base_ap)

    applied_keywords = []
    applied_stats = []

    # Add keywords
    k_count = num_keywords_to_add()
    if k_count > 0:
        chosen_keywords = random.sample(KEYWORDS_LIST, k_count)
        for kw in chosen_keywords:
            unit.keywords.append(kw)
            # track keyword application
            keyword_stats[category].setdefault(kw, {"count":0, "wins":0, "losses":0})
            keyword_stats[category][kw]["count"] += 1
            applied_keywords.append(kw)

    # Add stat modifications
    s_count = num_stats_to_add()
    if s_count > 0:
        chosen_stats = random.sample(STAT_MODS, s_count)
        for smod in chosen_stats:
            apply_stat_mod(unit, smod, category, applied_stats)

    return applied_keywords, applied_stats

def apply_stat_mod(unit, smod, category, applied_stats):
    # Apply the chosen stat modification to the unit
    # Also track the modification
    if smod == "num_models":
        # increase from 5 to 10 if unit has less than 10 now
        if unit.num_models < 10:
            unit.num_models = 10
            # Need to add models' dice?
            # For simplicity, assume base dice arrays scale with num_models.  
            # Just track occurrence.
            stat_mod_stats[category].setdefault("num_models_10", {"count":0, "wins":0, "losses":0})
            stat_mod_stats[category]["num_models_10"]["count"] += 1
            applied_stats.append("num_models_10")

    elif smod == "wounds_per_model":
        unit.wounds_per_model += 1
        stat_mod_stats[category].setdefault("wounds_per_model+1", {"count":0, "wins":0, "losses":0})
        stat_mod_stats[category]["wounds_per_model+1"]["count"] += 1
        applied_stats.append("wounds_per_model+1")

    elif smod == "armor":
        # improve armor one step if possible
        current_index = ARMOR_TIERS.index(unit.armor) if unit.armor in ARMOR_TIERS else 0
        if current_index < len(ARMOR_TIERS)-1:
            # improve one step
            unit.armor = ARMOR_TIERS[current_index+1]
            stat_mod_stats[category].setdefault("armor_improved", {"count":0, "wins":0, "losses":0})
            stat_mod_stats[category]["armor_improved"]["count"] += 1
            applied_stats.append("armor_improved")

    elif smod == "movement":
        unit.movement += 2
        stat_mod_stats[category].setdefault("movement+2", {"count":0, "wins":0, "losses":0})
        stat_mod_stats[category]["movement+2"]["count"] += 1
        applied_stats.append("movement+2")

    elif smod == "missile_attack_dice":
        # add one random die type
        die_type = random.choice(list(DICE_TYPES.keys()))
        unit.base_missile_attack_dice.append(die_type)
        stat_mod_stats[category].setdefault(f"missile_die_{die_type}", {"count":0, "wins":0, "losses":0})
        stat_mod_stats[category][f"missile_die_{die_type}"]["count"] += 1
        applied_stats.append(f"missile_die_{die_type}")

    elif smod == "melee_attack_dice":
        die_type = random.choice(list(DICE_TYPES.keys()))
        unit.base_melee_attack_dice.append(die_type)
        stat_mod_stats[category].setdefault(f"melee_die_{die_type}", {"count":0, "wins":0, "losses":0})
        stat_mod_stats[category][f"melee_die_{die_type}"]["count"] += 1
        applied_stats.append(f"melee_die_{die_type}")

    elif smod == "attack_range":
        unit.attack_range += 4
        stat_mod_stats[category].setdefault("attack_range+4", {"count":0, "wins":0, "losses":0})
        stat_mod_stats[category]["attack_range+4"]["count"] += 1
        applied_stats.append("attack_range+4")


def run_simulation():
    i = 0
    while True:
        i += 1
        unit_names = list(unit_templates.keys())
        player1_choices = random.sample(unit_names, 5)
        player2_choices = random.sample(unit_names, 5)

        player1_units = []
        player2_units = []

        # Track modifications for each player this round
        player1_mods = [] # list of (ap_category, [keywords], [stats])
        player2_mods = []

        # Build and modify Player1 units
        for name in player1_choices:
            data = unit_templates[name]
            u = create_unit(name, data)
            kw, st = apply_random_modifications(u)
            player1_mods.append((get_category(data["ap_cost"]), kw, st))
            player1_units.append(u)

        # Build and modify Player2 units
        for name in player2_choices:
            data = unit_templates[name]
            u = create_unit(name, data)
            kw, st = apply_random_modifications(u)
            player2_mods.append((get_category(data["ap_cost"]), kw, st))
            player2_units.append(u)

        player1 = Player(name="Player1", units=player1_units)
        player2 = Player(name="Player2", units=player2_units)

        control_points, width, height = setup.setup_battlefield()
        bf = battlefield.Battlefield(width, height, control_points, [])
        setup.place_units_randomly(player1, player2)

        game.play_game(player1, player2, bf)

        # Determine result
        if player1.score > player2.score:
            winner = "Player1"
        elif player2.score > player1.score:
            winner = "Player2"
        else:
            winner = None

        # Update win/loss counts for keywords and stats
        def update_results(mods_list, is_winner):
            for (cat, kw_list, st_list) in mods_list:
                for kw in kw_list:
                    if kw in keyword_stats[cat]:
                        if is_winner:
                            keyword_stats[cat][kw]["wins"] += 1
                        else:
                            keyword_stats[cat][kw]["losses"] += 1
                for st in st_list:
                    if st in stat_mod_stats[cat]:
                        if is_winner:
                            stat_mod_stats[cat][st]["wins"] += 1
                        else:
                            stat_mod_stats[cat][st]["losses"] += 1

        if winner == "Player1":
            update_results(player1_mods, True)
            update_results(player2_mods, False)
        elif winner == "Player2":
            update_results(player1_mods, False)
            update_results(player2_mods, True)
        else:
            # Draw - no wins/losses increment
            pass

        # Print summary occasionally
        if i % 100 == 0:
            print(f"--- After Run {i} ---")
            print("Keyword Stats:")
            for cat in keyword_stats:
                print(f"Category {cat}:")
                for kw, data in keyword_stats[cat].items():
                    print(f"  {kw}: count={data['count']}, wins={data['wins']}, losses={data['losses']}")

            print("Stat Mod Stats:")
            for cat in stat_mod_stats:
                print(f"Category {cat}:")
                for st, data in stat_mod_stats[cat].items():
                    print(f"  {st}: count={data['count']}, wins={data['wins']}, losses={data['losses']}")

if __name__ == "__main__":
    run_simulation()
