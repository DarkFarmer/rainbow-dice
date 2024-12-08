import random

def simulate_fight(unit_a, unit_b):
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
    print("battle happened, winner was " + winning_unit)
    return {
        "winner": winning_unit,
        "survivors": survivors,
        "turns": turn,
        "wounds_by_phase": total_wounds_by_phase,
    }