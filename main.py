from unit import Unit
from simulation import simulate_multiple_battles

def main():
    unit1 = Unit(
        name="Solar Knights",
        num_models=5,
        wounds_per_model=2,
        attack_range=18,
        movement=6,
        armor='Medium Armor',
        keywords=['Withering Fire'],
        missile_attack_dice=['Blue'] * 5,
        melee_attack_dice=['Green'] * 5
    )

    unit2 = Unit(
        name="Alien Warriors",
        num_models=10,
        attack_range=0,
        movement=8,
        wounds_per_model=1,
        armor='Light Armor',
        keywords=['Relentless'],
        missile_attack_dice=[],
        melee_attack_dice=['Pink'] * 10
    )

    simulate_multiple_battles(unit1, unit2, num_battles=1000)

if __name__ == "__main__":
    main()
