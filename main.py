from unit import Unit
from simulation import simulate_multiple_battles

def main():
    unit1 = Unit(
        name="Solar Knights",
        num_models=5,
        wounds_per_model=2,
        armor='Medium Armor',
        movement=6,
        ap_cost=4,
        missile_attack_dice=['Blue'] * 5,
        melee_attack_dice=['Green'] * 5,
        attack_range=18,
        special_rules=None,  # No special rules provided for this unit
        keywords=['Withering Fire']
    )

    unit2 = Unit(
        name="Alien Warriors",
        num_models=10,
        wounds_per_model=1,
        armor='Light Armor',
        movement=8,
        ap_cost=3,
        missile_attack_dice=[],  # No missile attack dice for this unit
        melee_attack_dice=['Pink'] * 10,
        attack_range=0,
        special_rules=None,  # No special rules provided for this unit
        keywords=['Relentless']
    )


    simulate_multiple_battles(unit1, unit2, num_battles=1000)

if __name__ == "__main__":
    main()
