from unit import Unit
import random

def simulate_battle(unit_a, unit_b):
    turn = 1
    phase = 'missile'
    total_wounds_by_phase = {
        unit_a.name: {'missile': 0, 'melee': 0},
        unit_b.name: {'missile': 0, 'melee': 0},
    }

    def should_switch_to_melee(unit_a, unit_b):
        """
        Calculate the likelihood of switching to melee based on range, movement, and attack strength.
        """
        range_factor = max(unit_a.attack_range - unit_b.movement, 0) - max(unit_b.attack_range - unit_a.movement, 0)
        melee_preference = sum(1 if 'Relentless' in unit.keywords else -1 for unit in [unit_a, unit_b])
        roll = random.randint(1, 20)
        return roll > (5 + range_factor + melee_preference)

    while unit_a.is_alive() and unit_b.is_alive():
        if phase == 'missile':
            unit_a.attack(unit_b, phase)
            total_wounds_by_phase[unit_a.name][phase] += unit_b.calculate_total_wounds()

            if not unit_b.is_alive():
                break

            unit_b.attack(unit_a, phase)
            total_wounds_by_phase[unit_b.name][phase] += unit_a.calculate_total_wounds()

            if not unit_a.is_alive():
                break

            if should_switch_to_melee(unit_a, unit_b):
                phase = 'melee'

        else:
            unit_a.attack(unit_b, phase)
            total_wounds_by_phase[unit_a.name][phase] += unit_b.calculate_total_wounds()

            if not unit_b.is_alive():
                break

            unit_b.attack(unit_a, phase)
            total_wounds_by_phase[unit_b.name][phase] += unit_a.calculate_total_wounds()

            if not unit_a.is_alive():
                break

        turn += 1

    survivors = unit_a.num_models if unit_a.is_alive() else unit_b.num_models
    winning_unit = unit_a.name if unit_a.is_alive() else unit_b.name
    return {
        "winner": winning_unit,
        "survivors": survivors,
        "turns": turn,
        "wounds_by_phase": total_wounds_by_phase,
    }

def simulate_multiple_battles(unit_a, unit_b, num_battles=100):
    battle_results = []
    total_wounds = {
        unit_a.name: {'missile': 0, 'melee': 0},
        unit_b.name: {'missile': 0, 'melee': 0},
    }
    unit_a_wins = 0
    unit_b_wins = 0

    for _ in range(num_battles):
        unit_a_clone = unit_a.clone()
        unit_b_clone = unit_b.clone()
        result = simulate_battle(unit_a_clone, unit_b_clone)
        battle_results.append(result)

        if result['winner'] == unit_a.name:
            unit_a_wins += 1
        else:
            unit_b_wins += 1

        for phase in ['missile', 'melee']:
            total_wounds[unit_a.name][phase] += result['wounds_by_phase'][unit_a.name][phase]
            total_wounds[unit_b.name][phase] += result['wounds_by_phase'][unit_b.name][phase]

    average_wounds_per_phase = {
        unit_a.name: {
            phase: total_wounds[unit_a.name][phase] / num_battles for phase in ['missile', 'melee']
        },
        unit_b.name: {
            phase: total_wounds[unit_b.name][phase] / num_battles for phase in ['missile', 'melee']
        },
    }

    print(f"\n{unit_a.name} Win Rate: {unit_a_wins / num_battles * 100:.2f}%")
    print(f"{unit_b.name} Win Rate: {unit_b_wins / num_battles * 100:.2f}%")

    print("\nAverage Wounds Per Attack:")
    print(f"{unit_a.name}:")
    print(f"  Missile: {average_wounds_per_phase[unit_a.name]['missile']:.2f}")
    print(f"  Melee: {average_wounds_per_phase[unit_a.name]['melee']:.2f}")
    print(f"{unit_b.name}:")
    print(f"  Missile: {average_wounds_per_phase[unit_b.name]['missile']:.2f}")
    print(f"  Melee: {average_wounds_per_phase[unit_b.name]['melee']:.2f}")
