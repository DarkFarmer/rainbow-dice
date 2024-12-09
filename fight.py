import random

def melee_favorable(attacker, defender):
    """
    Placeholder for melee favorability logic.
    Eventually, this might be replaced with a more complex, possibly ML-driven decision.
    For now, let's just return True.
    """
    return True

def simulate_fight(unit_a, unit_b, initial_distance=24, phase = 'missile'):
    # Initial conditions
    distance = initial_distance

    # Track wounds inflicted by phase
    total_wounds_by_phase = {
        unit_a.name: {'missile': 0, 'melee': 0},
        unit_b.name: {'missile': 0, 'melee': 0},
    }

    # For this single attack sequence, unit_a is the active unit and unit_b is defending
    active_unit = unit_a
    defending_unit = unit_b

    # Perform a single ranged attack if possible
    if phase == 'missile':
        active_unit.attack(defending_unit, 'missile')
        total_wounds_by_phase[active_unit.name]['missile'] += defending_unit.calculate_total_wounds()

        # Check if defending unit died from missile attack
        if not defending_unit.is_alive():
            winner = active_unit.name
            survivors = active_unit.num_models
            print("battle happened, winner was " + winner)
            return {
                "winner": winner,
                "survivors": survivors,
                "turns": 1,
                "wounds_by_phase": total_wounds_by_phase,
            }

        # Consider charging into melee if possible
    if phase == 'melee':
        active_unit.attack(defending_unit, 'melee')
        total_wounds_by_phase[active_unit.name]['melee'] += defending_unit.calculate_total_wounds()

        if not defending_unit.is_alive():
            # Defending unit died in melee
            winner = active_unit.name
            survivors = active_unit.num_models
            print("battle happened, winner was " + winner)
            return {
                "winner": winner,
                "survivors": survivors,
                "turns": 1,
                "wounds_by_phase": total_wounds_by_phase,
            }

    # If we get here, both units are still alive after one sequence of attacks.
    # No winner this round.
    print("battle happened, but no unit was destroyed this attack sequence")
    return {
        "winner": None,
        "survivors": None,
        "turns": 1,
        "wounds_by_phase": total_wounds_by_phase,
    }
