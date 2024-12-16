import random

# Define Dice Types with their respective outcomes
DICE_TYPES = {
    'White': {'normal_wounds': 2, 'double_wounds': 1, 'mortal_wounds': 0, 'double_mortal_wounds': 0},
    'Green': {'normal_wounds': 3, 'double_wounds': 1, 'mortal_wounds': 0, 'double_mortal_wounds': 0},
    'Blue': {'normal_wounds': 3, 'double_wounds': 2, 'mortal_wounds': 0, 'double_mortal_wounds': 0},
    'Purple': {'normal_wounds': 3, 'double_wounds': 2, 'mortal_wounds': 1, 'double_mortal_wounds': 0},
    'Black': {'normal_wounds': 2, 'double_wounds': 2, 'mortal_wounds': 1, 'double_mortal_wounds': 1},
    'Gunmetal': {'normal_wounds': 1, 'double_wounds': 0, 'mortal_wounds': 2, 'double_mortal_wounds': 1},
    'Silver': {'normal_wounds': 1, 'double_wounds': 0, 'mortal_wounds': 3, 'double_mortal_wounds': 1},
    'Gold': {'normal_wounds': 2, 'double_wounds': 0, 'mortal_wounds': 2, 'double_mortal_wounds': 2},
    'Pink': {'normal_wounds': 1, 'double_wounds': 2, 'mortal_wounds': 0, 'double_mortal_wounds': 0},
    'Red': {'normal_wounds': 1, 'double_wounds': 3, 'mortal_wounds': 0, 'double_mortal_wounds': 0},
    'Crimson': {'normal_wounds': 1, 'double_wounds': 4, 'mortal_wounds': 0, 'double_mortal_wounds': 0},
}

def roll_dice(dice_type):
    result = {'normal': 0, 'double': 0, 'mortal': 0, 'double_mortal': 0}
    dice_stats = DICE_TYPES[dice_type]
    die_faces = []

    # Build the die faces according to the dice stats
    die_faces.extend(['normal'] * dice_stats.get('normal_wounds', 0))
    die_faces.extend(['double'] * dice_stats.get('double_wounds', 0))
    die_faces.extend(['mortal'] * dice_stats.get('mortal_wounds', 0))
    die_faces.extend(['double_mortal'] * dice_stats.get('double_mortal_wounds', 0))
    # Fill the remaining faces with 'miss' to make a total of 6 faces
    die_faces.extend(['miss'] * (6 - len(die_faces)))

    # Roll the die by randomly selecting one face
    roll = random.choice(die_faces)
    if roll == 'double':
        # Add 2 normal wounds instead of 1 double wound
        result['normal'] += 2
    elif roll == 'double_mortal':
        # Add 2 mortal wounds instead of 1 double mortal wound
        result['mortal'] += 2
    elif roll != 'miss':
        result[roll] += 1

    return result