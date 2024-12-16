import random

def melee_favorable(attacker, defender):
    """
    Placeholder for melee favorability logic.
    Eventually, this might be replaced with a more complex, possibly ML-driven decision.
    For now, let's just return True.
    """
    return True

def simulate_fight(unit_a, unit_b, active_player, initial_distance=24, phase='missile', charging=False):
    """
    Simulates a fight between two units, tracking kills and updating active player's stats.
    :param unit_a: The attacking unit.
    :param unit_b: The defending unit.
    :param initial_distance: Starting distance between the units.
    :param active_player: The player controlling the attacking unit.
    :param phase: The phase of the fight ('missile' or 'melee').
    """
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
        initial_models = unit_b.num_models
        unit_a.attack(unit_b, 'missile', charging=False)
        total_wounds_by_phase[active_unit.name]['missile'] += defending_unit.calculate_total_wounds()

        # Count kills from missile attack
        models_killed = initial_models - defending_unit.num_models
        if active_player and models_killed > 0:
            active_player.missile_kills += models_killed

        # Check if defending unit died from missile attack
        if not defending_unit.is_alive():
            winner = active_unit.name
            survivors = active_unit.num_models
            return {
                "winner": winner,
                "survivors": survivors,
                "turns": 1,
                "wounds_by_phase": total_wounds_by_phase,
            }

    # Perform a melee attack if in melee phase
    if phase == 'melee':
        print(f"{active_unit.name} is doing melee")
        initial_models = unit_b.num_models
        unit_a.attack(unit_b, 'melee', charging=charging)
        total_wounds_by_phase[active_unit.name]['melee'] += defending_unit.calculate_total_wounds()

        # Count kills from melee attack
        models_killed = initial_models - defending_unit.num_models
        if active_player and models_killed > 0:
            active_player.melee_kills += models_killed

        if not defending_unit.is_alive():
            # Defending unit died in melee
            winner = active_unit.name
            active_unit.melee_target = None
            survivors = active_unit.num_models
            return {
                "winner": winner,
                "survivors": survivors,
                "turns": 1,
                "wounds_by_phase": total_wounds_by_phase,
            }

    # If we get here, both units are still alive after one sequence of attacks.
    # No winner this round.
    return {
        "winner": None,
        "survivors": None,
        "turns": 1,
        "wounds_by_phase": total_wounds_by_phase,
    }